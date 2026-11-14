import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from kali_agente import coordinador_agente as c
from kali_agente import experience as e


class Integration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        state = patch.object(c, "STATE", self.folder / "state")
        state.start()
        self.addCleanup(state.stop)
        self.root = self.folder / "repo"
        self.root.mkdir()
        (self.root / "code.py").write_text("value = 1\n")
        (self.root / ".kali-agente.json").write_text(
            json.dumps(
                {
                    "checks": [
                        {
                            "name": "value",
                            "argv": [
                                sys.executable,
                                "-c",
                                "from code import value; assert value == 2",
                            ],
                        }
                    ],
                    "format_python": False,
                }
            )
        )
        for args in (
            ("init", "-q"),
            ("config", "user.name", "Test"),
            ("config", "user.email", "test@localhost"),
            ("add", "."),
            ("commit", "-qm", "base"),
        ):
            c.git(self.root, *args)
        self.base = c.git(self.root, "rev-parse", "HEAD")

        def agent(worktree, *args, **kwargs):
            (worktree / "code.py").write_text("value = 2\n")
            (worktree / "new.txt").write_text("new file\n")
            return dict(codigo=0, motivo_parada=None, acciones=1, segundos=0)

        with patch.object(c, "stream_agent", agent), contextlib.redirect_stdout(io.StringIO()):
            self.report = c.task(self.root, "Fix", warm=False)
        self.identifier = self.report["id"]
        self.directory = c.STATE / "tareas" / self.identifier
        self.assertEqual(self.report["estado"], "verificado")

    def review(self):
        with contextlib.redirect_stdout(io.StringIO()):
            e.review(self.identifier)

    def apply(self, answer=None, interactive=True):
        with (
            patch.object(sys.stdin, "isatty", return_value=interactive),
            patch("builtins.input", return_value=answer or "APLICAR " + self.identifier),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            return e.apply(self.identifier)

    def test_applies_reviewed_patch_and_new_file_without_committing(self):
        self.review()
        self.assertEqual(self.apply(), 0)
        self.assertEqual((self.root / "code.py").read_text(), "value = 2\n")
        self.assertEqual((self.root / "new.txt").read_text(), "new file\n")
        self.assertEqual(c.git(self.root, "rev-parse", "HEAD"), self.base)
        self.assertTrue(c.git(self.root, "diff", "--cached", "--name-only"))
        self.assertEqual(c.git(self.root, "diff", "--name-only"), "")
        with self.assertRaisesRegex(RuntimeError, "ya se integro"):
            self.apply()

    def test_requires_review_before_apply(self):
        with self.assertRaisesRegex(RuntimeError, "Revisa este parche"):
            self.apply()
        self.assertEqual(c.git(self.root, "status", "--porcelain"), "")

    def test_rejects_changed_original(self):
        self.review()
        (self.root / "personal.txt").write_text("keep")
        with self.assertRaisesRegex(RuntimeError, "original cambio"):
            self.apply()
        self.assertEqual((self.root / "code.py").read_text(), "value = 1\n")
        self.assertEqual((self.root / "personal.txt").read_text(), "keep")

    def test_rejects_new_commit_even_when_clean(self):
        self.review()
        c.git(self.root, "commit", "--allow-empty", "-qm", "later")
        with self.assertRaisesRegex(RuntimeError, "original cambio"):
            self.apply()

    def test_rejects_changed_worktree_after_review(self):
        self.review()
        (Path(self.report["worktree"]) / "new.txt").write_text("changed")
        with self.assertRaisesRegex(RuntimeError, "worktree cambio"):
            self.apply()

    def test_rejects_changed_patch_after_review(self):
        self.review()
        with (self.directory / "cambios.patch").open("ab") as stream:
            stream.write(b"\n")
        with self.assertRaisesRegex(RuntimeError, "Revisa este parche"):
            self.apply()

    def test_confirmation_can_cancel_and_pipes_cannot_confirm(self):
        self.review()
        self.assertEqual(self.apply("no"), 1)
        with self.assertRaisesRegex(RuntimeError, "terminal interactiva"):
            self.apply(interactive=False)
        self.assertEqual(c.git(self.root, "status", "--porcelain"), "")

    def test_rechecks_original_after_confirmation(self):
        self.review()

        def confirm(*args):
            (self.root / "other.txt").write_text("concurrent user work")
            return "APLICAR " + self.identifier

        with (
            patch.object(sys.stdin, "isatty", return_value=True),
            patch("builtins.input", side_effect=confirm),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            with self.assertRaisesRegex(RuntimeError, "original cambio"):
                e.apply(self.identifier)
        self.assertEqual((self.root / "code.py").read_text(), "value = 1\n")

    def test_failed_reverification_blocks_integration(self):
        self.review()
        with patch.object(c, "verify", return_value=[dict(codigo=1, timeout=False)]):
            with self.assertRaisesRegex(RuntimeError, "ya no pasan"):
                self.apply()

    def test_nonverified_status_blocks_integration(self):
        self.review()
        self.report["estado"] = "requiere_revision"
        c.save(self.directory / "informe.json", self.report)
        with self.assertRaisesRegex(RuntimeError, "Solo se pueden"):
            self.apply()

    def test_changed_captured_checks_block_integration(self):
        self.review()
        c.save(
            self.directory / "comprobaciones-originales.json",
            {"checks": [{"name": "fake", "argv": [sys.executable, "-c", "pass"]}]},
        )
        with self.assertRaisesRegex(RuntimeError, "comprobaciones capturadas cambiaron"):
            self.apply()

    def test_progress_records_final_state_and_dashboard(self):
        live = json.loads((self.directory / "progreso.json").read_text())
        self.assertEqual(live["fase"], "verificado")
        with contextlib.redirect_stdout(io.StringIO()) as output:
            e.dashboard([])
        self.assertIn(self.identifier, output.getvalue())
        self.assertIn("verificado", output.getvalue())

    def test_invalid_identifier_is_not_a_path(self):
        for identifier in ("../../other", "-", "0000"):
            with self.assertRaises(ValueError):
                e.task_record(identifier)


class Setup(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        import os

        env = patch.dict(os.environ, {"KALI_AGENT_CONFIG_DIR": str(self.folder)}, clear=True)
        env.start()
        self.addCleanup(env.stop)

    def setup(self, args, models=None):
        result = subprocess.CompletedProcess([], 0, "version-test", "")
        with (
            patch.object(e.subprocess, "run", return_value=result),
            patch.object(
                e,
                "request",
                return_value={
                    "models": models if models is not None else [{"name": "local:latest"}]
                },
            ),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            return e.setup(args)

    def test_selects_installed_model_and_saves_config(self):
        self.assertEqual(self.setup(["--modelo", "local"]), 0)
        self.assertEqual(
            json.loads((self.folder / "config.json").read_text())["model"], "local:latest"
        )

    def test_uninstalled_model_is_not_downloaded_or_saved(self):
        with self.assertRaisesRegex(ValueError, "modelos instalados"):
            self.setup(["--modelo", "missing"])
        self.assertFalse((self.folder / "config.json").exists())

    def test_no_models_explains_next_step(self):
        with self.assertRaisesRegex(RuntimeError, "no tiene modelos"):
            self.setup([], models=[])

    def test_missing_dependency_has_actionable_error(self):
        with patch.object(e.subprocess, "run", side_effect=FileNotFoundError("opencode")):
            with self.assertRaisesRegex(RuntimeError, "Instala la dependencia"):
                e.setup([])
