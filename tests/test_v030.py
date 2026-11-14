import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from kali_agente import coordinador_agente as c
from kali_agente.banco_agente import CASES
from kali_agente import banco_validar as validator
from kali_agente import task_tools as tasks
from kali_agente import sandbox
from kali_agente.model_profiles import select
from kali_agente.settings import atomic_json, profile


class TaskTools(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        state = patch.object(c, "STATE", self.folder / "state")
        state.start()
        self.addCleanup(state.stop)
        self.root = self.folder / "repo"
        self.root.mkdir()
        (self.root / "data.txt").write_text("base\n")
        for args in (
            ("init", "-q"),
            ("config", "user.name", "Test"),
            ("config", "user.email", "test@localhost"),
            ("add", "."),
            ("commit", "-qm", "base"),
        ):
            c.git(self.root, *args)

        def agent(worktree, *args, **kwargs):
            (worktree / "data.txt").write_text("<script>alert('x')</script>\n")
            return dict(codigo=0, motivo_parada=None)

        with patch.object(c, "stream_agent", agent), contextlib.redirect_stdout(io.StringIO()):
            self.report = c.task(self.root, "<img src=x onerror=alert(1)>", warm=False)
        self.id = self.report["id"]
        self.directory = c.STATE / "tareas" / self.id

    def manage(self, action, *argv):
        with contextlib.redirect_stdout(io.StringIO()):
            return tasks.manage(action, [self.id, *argv])

    def test_graphical_review_escapes_patch_and_objective(self):
        with contextlib.redirect_stdout(io.StringIO()):
            path = tasks.graphical(self.id)
        page = path.read_text()
        self.assertNotIn("<script>", page)
        self.assertNotIn("<img src=x", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("Content-Security-Policy", page)

    def test_archive_restores_without_moving_worktree(self):
        self.manage("archivar")
        self.assertIn("archivado", json.loads((self.directory / "informe.json").read_text()))
        self.assertTrue(Path(self.report["worktree"]).exists())
        self.manage("archivar", "--restaurar")
        self.assertNotIn("archivado", json.loads((self.directory / "informe.json").read_text()))

    def test_export_is_allowlisted_and_refuses_overwrite(self):
        (self.directory / "secret.env").write_text("secret")
        destination = self.folder / "task.zip"
        self.manage("exportar", "--destino", str(destination))
        with zipfile.ZipFile(destination) as archive:
            self.assertIn("cambios.patch", archive.namelist())
            self.assertNotIn("secret.env", archive.namelist())
        with self.assertRaises(FileExistsError):
            self.manage("exportar", "--destino", str(destination))

    def test_cleanup_requires_discard_for_dirty_candidate(self):
        with self.assertRaisesRegex(RuntimeError, "cambios sin commit"):
            self.manage("limpiar")
        self.assertTrue(Path(self.report["worktree"]).exists())

    def test_cleanup_keeps_patch_and_original_and_branch(self):
        with (
            patch.object(sys.stdin, "isatty", return_value=True),
            patch("builtins.input", return_value="LIMPIAR " + self.id),
        ):
            self.assertEqual(self.manage("limpiar", "--descartar"), 0)
        self.assertFalse(Path(self.report["worktree"]).exists())
        self.assertIn(b"script", (self.directory / "respaldo-limpieza/cambios.patch").read_bytes())
        self.assertEqual((self.root / "data.txt").read_text(), "base\n")
        self.assertTrue(c.git(self.root, "branch", "--list", self.report["rama"]))
        destination = self.folder / "cleaned.zip"
        self.manage("exportar", "--destino", str(destination))
        with zipfile.ZipFile(destination) as archive:
            self.assertIn("respaldo-limpieza/cambios.patch", archive.namelist())

    def test_cleanup_refuses_ignored_files(self):
        worktree = Path(self.report["worktree"])
        (worktree / ".gitignore").write_text("private.bin\n")
        (worktree / "private.bin").write_bytes(b"do not lose")
        with self.assertRaisesRegex(RuntimeError, "archivos ignorados"):
            self.manage("limpiar", "--descartar")

    def test_cleanup_cancellation_preserves_worktree(self):
        with (
            patch.object(sys.stdin, "isatty", return_value=True),
            patch("builtins.input", return_value="no"),
        ):
            self.assertEqual(self.manage("limpiar", "--descartar"), 1)
        self.assertTrue(Path(self.report["worktree"]).exists())


class Sandbox(unittest.TestCase):
    def test_restricted_flags_and_no_shell_interpolation(self):
        with tempfile.TemporaryDirectory() as folder:
            argv = sandbox.command("image@sha256:abc", folder, ["echo", "a; rm -rf /"], "fixture")
        self.assertIn("--network=none", argv)
        self.assertIn("--read-only", argv)
        self.assertIn("--pull=never", argv)
        self.assertIn("--cap-drop=ALL", argv)
        self.assertTrue(
            next(item for item in argv if item.startswith("type=bind,")).endswith(",readonly")
        )
        self.assertEqual(argv[-1], "a; rm -rf /")
        self.assertNotIn("--privileged", argv)

    def test_rejects_root_and_option_like_images(self):
        for image, folder in (("-v", "/tmp"), ("image", "/")):
            with self.assertRaises(ValueError):
                sandbox.command(image, folder, ["true"], "fixture")

    def test_explicit_network_and_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            argv = sandbox.command("image", folder, ["true"], "fixture", True, True)
        self.assertIn("--network=bridge", argv)
        self.assertFalse(
            next(item for item in argv if item.startswith("type=bind,")).endswith(",readonly")
        )


class Evaluation(unittest.TestCase):
    def test_all_six_reference_fixtures_start_broken(self):
        for name, fixture in CASES.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                for path, content in fixture["files"].items():
                    (root / path).write_text(content)
                result = subprocess.run(
                    [sys.executable, str(Path(validator.__file__)), name, folder],
                    capture_output=True,
                    timeout=10,
                )
                self.assertNotEqual(result.returncode, 0)

    def test_new_validators_accept_independent_solutions(self):
        solutions = {
            "multiarchivo": {
                "precios.py": "def total(items):\n return sum(x['precio']*x['cantidad'] for x in items)\n",
                "factura.py": "from precios import total\ndef factura(items, iva):\n return total(items)*(1+iva/100)\n",
            },
            "jsonl": {
                "lector.py": "import json\ndef leer(text):\n result=[]\n for line in text.splitlines():\n  if not line.strip(): continue\n  item=json.loads(line)\n  if not isinstance(item,dict): raise ValueError('object required')\n  result.append(item)\n return result\n"
            },
            "cli": {
                "main.py": "import argparse\np=argparse.ArgumentParser()\np.add_argument('--nombre',required=True)\na=p.parse_args()\nprint(f'Hola, {a.nombre}!')\n"
            },
        }
        for name, files in solutions.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as folder:
                for path, content in files.items():
                    (Path(folder) / path).write_text(content)
                result = subprocess.run(
                    [sys.executable, str(Path(validator.__file__)), name, folder],
                    capture_output=True,
                    timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)


class Profiles(unittest.TestCase):
    def test_profile_applies_request_sampling_without_downloading(self):
        with (
            tempfile.TemporaryDirectory() as folder,
            patch.dict(os.environ, {"KALI_AGENT_CONFIG_DIR": folder}, clear=True),
        ):
            atomic_json(Path(folder) / "config.json", {"model": "fixture:latest"})
            with (
                patch(
                    "kali_agente.model_profiles.request",
                    return_value={"models": [{"name": "fixture:latest"}]},
                ),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(select(["determinista"]), 0)
            data = profile()
            self.assertEqual(
                data["providers"]["ollama"]["models"]["fixture:latest"]["body"]["seed"], 42
            )
            self.assertEqual(
                data["providers"]["ollama"]["models"]["fixture:latest"]["body"]["temperature"], 0
            )
