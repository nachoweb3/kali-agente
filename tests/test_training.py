import contextlib
import copy
import io
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1] / "training"
prepare = runpy.run_path(str(ROOT / "prepare.py"))["build"]
compare = runpy.run_path(str(ROOT / "compare.py"))["compare"]


def fixture(passed):
    return {
        "model_digest": "fixture-not-a-real-model",
        "conditions": dict.fromkeys(
            (
                "suite_sha256",
                "runner_sha256",
                "budget_seconds",
                "action_limit",
                "context",
                "output_tokens",
                "seed",
                "backend",
                "hardware",
                "deployment_schema_sha256",
            ),
            "fixture",
        ),
        "tasks": [
            {
                "id": str(i),
                "passed": value,
                "seconds": 1.0,
                "split": "test",
                "training_overlap": False,
                "verification_sha256": "fixture",
            }
            for i, value in enumerate(passed)
        ],
    }


class Training(unittest.TestCase):
    def test_training_preflight_rejects_small_gpu_before_heavy_imports(self):
        import subprocess

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            corpus = root / "corpus"
            with contextlib.redirect_stdout(io.StringIO()):
                prepare(corpus)
            checkpoint = root / "checkpoint"
            checkpoint.mkdir()
            (checkpoint / "config.json").write_text("{}")
            (checkpoint / "fixture.safetensors").touch()
            template = root / "template.jinja"
            template.write_text("{% generation %}{{ content }}{% endgeneration %}")
            args = [
                str(ROOT / "train_lora.py"),
                "--checkpoint",
                str(checkpoint),
                "--corpus",
                str(corpus),
                "--output",
                str(root / "adapter"),
                "--chat-template",
                str(template),
                "--smoke-only",
                "--run",
            ]
            with (
                patch("sys.argv", args),
                patch(
                    "subprocess.run",
                    return_value=subprocess.CompletedProcess([], 0, "6144, 2048\n"),
                ),
                contextlib.redirect_stdout(io.StringIO()),
                self.assertRaisesRegex(RuntimeError, "Insufficient free GPU memory"),
            ):
                runpy.run_path(str(ROOT / "train_lora.py"), run_name="__main__")
            self.assertFalse((root / "adapter").exists())

    def test_seed_checks_execute_and_families_do_not_leak(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "corpus"
            with contextlib.redirect_stdout(io.StringIO()):
                prepare(root)
            manifest = json.loads((root / "manifest.json").read_text())
            self.assertEqual(manifest["counts"], {"train": 8, "dev": 2})
            train, dev = (
                [json.loads(line) for line in (root / (split + ".jsonl")).read_text().splitlines()]
                for split in ("train", "dev")
            )
            self.assertFalse({r["family"] for r in train} & {r["family"] for r in dev})
            for row in train + dev:
                self.assertFalse(row["model_generated"])
                self.assertEqual(row["verification"]["after_exit"], 0)
                self.assertNotEqual(row["verification"]["before_exit"], 0)
            with self.assertRaises(FileExistsError):
                prepare(root)

    def test_small_or_unchanged_runs_cannot_promote(self):
        self.assertFalse(
            compare(fixture([False] * 5), fixture([True] * 5))["promotion_gate_passed"]
        )
        self.assertFalse(
            compare(fixture([True] * 30), fixture([True] * 30))["promotion_gate_passed"]
        )

    def test_paired_wins_pass_gate_but_regressions_block_it(self):
        result = compare(fixture([False] * 10 + [True] * 20), fixture([True] * 30))
        self.assertTrue(result["promotion_gate_passed"])
        self.assertEqual(result["wins"], 10)
        result = compare(fixture([False] * 10 + [True] * 20), fixture([True] * 29 + [False]))
        self.assertFalse(result["promotion_gate_passed"])
        self.assertEqual(result["regressions"], 1)

    def test_mismatched_conditions_missing_tasks_and_contamination_are_rejected(self):
        base = fixture([True] * 30)
        for mutation in (
            lambda r: r["conditions"].update(budget_seconds="different"),
            lambda r: r["tasks"].pop(),
            lambda r: r["tasks"][0].update(training_overlap=True),
            lambda r: r["tasks"][0].update(passed="true"),
        ):
            candidate = copy.deepcopy(base)
            mutation(candidate)
            with self.assertRaises(ValueError):
                compare(base, candidate)
