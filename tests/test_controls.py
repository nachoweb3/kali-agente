"""Pruebas de control: timeout, bucles, worktrees y verificacion independiente."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from kali_agente import coordinador_agente as c


class Controls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="kali-agent-check-")
        self.folder = Path(self.temp.name)
        self.state = patch.object(c, "STATE", self.folder / "state")
        self.state.start()

    def tearDown(self):
        self.state.stop()
        self.temp.cleanup()

    def repo(self, checks=None):
        root = self.folder / "repo"
        root.mkdir()
        (root / "codigo.py").write_text("valor = 1\n")
        (root / ".kali-agente.json").write_text(
            json.dumps({"checks": checks or [], "format_python": False})
        )
        c.git(root, "init", "-q")
        c.git(root, "config", "user.name", "Control local")
        c.git(root, "config", "user.email", "test@localhost")
        c.git(root, "add", ".")
        c.git(root, "commit", "-qm", "Base")
        return root

    def test_timeout(self):
        r = c.checked(
            ["python3", "-c", "import time; time.sleep(30)"],
            self.folder,
            self.folder / "timeout.log",
            1,
        )
        self.assertTrue(r["timeout"])
        self.assertNotEqual(r["codigo"], 0)

    def test_timeout_kills_detached_descendant(self):
        import time

        pidfile = self.folder / "child.pid"
        program = (
            'import subprocess,time; p=subprocess.Popen(["python3","-c",'
            '"import time; time.sleep(30)"],start_new_session=True); '
            f'open({str(pidfile)!r},"w").write(str(p.pid)); time.sleep(30)'
        )
        result = c.checked(
            ["python3", "-c", program], self.folder, self.folder / "descendant.log", 1
        )
        self.assertTrue(result["timeout"])
        child = int(pidfile.read_text())
        time.sleep(0.1)
        stat = Path(f"/proc/{child}/stat")
        self.assertTrue(not stat.exists() or stat.read_text().split(") ")[1].startswith("Z"))

    def test_success_also_cleans_detached_descendant(self):
        import time

        pidfile = self.folder / "normal-child.pid"
        program = (
            'import subprocess; p=subprocess.Popen(["python3","-c",'
            '"import time; time.sleep(30)"],start_new_session=True); '
            f'open({str(pidfile)!r},"w").write(str(p.pid))'
        )
        result = c.checked(
            ["python3", "-c", program], self.folder, self.folder / "normal-child.log", 5
        )
        self.assertEqual(result["codigo"], 0)
        child = int(pidfile.read_text())
        time.sleep(0.1)
        stat = Path(f"/proc/{child}/stat")
        self.assertTrue(not stat.exists() or stat.read_text().split(") ")[1].startswith("Z"))

    def test_interruption_keeps_report(self):
        root = self.repo()
        with (
            patch.object(c, "stream_agent", side_effect=KeyboardInterrupt),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            result = c.task(root, "Interrupcion", warm=False)
        self.assertEqual(result["estado"], "interrumpido")
        self.assertTrue((c.STATE / "tareas" / result["id"] / "INFORME.md").exists())
        self.assertEqual(c.git(root, "status", "--porcelain"), "")

    def test_dirty_refused(self):
        root = self.repo()
        (root / "codigo.py").write_text("valor = 2\n")
        before = c.git(root, "status", "--porcelain")
        with self.assertRaisesRegex(RuntimeError, "cambios pendientes"):
            c.task(root, "No ejecutar", warm=False)
        self.assertEqual(before, c.git(root, "status", "--porcelain"))
        self.assertFalse((c.STATE / "tareas").exists())

    def test_prepare_preserves_instructions_and_detects_python_tests(self):
        root = self.repo()
        (root / c.CONFIG).unlink()
        (root / "AGENTS.md").write_text("Instrucciones propias\n")
        (root / "test_modulo.py").write_text("def test_correcto():\n    assert 2 + 2 == 4\n")
        with contextlib.redirect_stdout(io.StringIO()):
            c.prepare(root)
        self.assertEqual((root / "AGENTS.md").read_text(), "Instrucciones propias\n")
        config = c.load_config(root)
        self.assertEqual(config["checks"][0]["argv"], ["python3", "-m", "pytest", "-q"])
        c.git(root, "add", ".")
        c.git(root, "commit", "-qm", "Preparar comprobaciones")
        with contextlib.redirect_stdout(io.StringIO()):
            results = c.verify(root, config, self.folder / "checks", "manual")
        self.assertTrue(all(x["codigo"] == 0 for x in results))

    def test_original_checks_cannot_be_disabled_by_editing_config(self):
        checks = [
            {
                "name": "siempre-falla",
                "argv": ["python3", "-c", "raise SystemExit(7)"],
                "timeout": 2,
            }
        ]
        root = self.repo(checks)
        base = c.git(root, "rev-parse", "HEAD")

        def fake(worktree, *args):
            (worktree / ".kali-agente.json").write_text('{"checks": []}')
            (worktree / "nuevo.py").write_text('print("nuevo")\n')
            return {
                "codigo": 0,
                "motivo_parada": None,
                "acciones": 1,
                "segundos": 0,
                "sesion": "simulada",
            }

        with patch.object(c, "stream_agent", fake), contextlib.redirect_stdout(io.StringIO()):
            result = c.task(root, "Prueba de controles", warm=False)
        self.assertEqual(result["estado"], "requiere_revision")
        self.assertEqual(result["despues"][1]["codigo"], 7)
        self.assertEqual(c.git(root, "rev-parse", "HEAD"), base)
        self.assertEqual(c.git(root, "status", "--porcelain"), "")
        self.assertFalse((root / "nuevo.py").exists())
        report = c.STATE / "tareas" / result["id"]
        self.assertIn("nuevo.py", (report / "cambios.patch").read_text())
        # El parche entregado debe ser aplicable sobre la base original, sin aplicarlo.
        c.git(root, "apply", "--check", str(report / "cambios.patch"))

    def test_no_checks_is_not_green(self):
        root = self.repo()
        with (
            patch.object(c, "stream_agent", return_value={"codigo": 0, "motivo_parada": None}),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            result = c.task(root, "Prueba sin checks", warm=False)
        self.assertEqual(result["estado"], "sin_comprobaciones_de_proyecto")

    def test_changed_protected_file_is_not_green_even_with_passing_checks(self):
        root = self.repo([{"name": "pasa", "argv": ["python3", "-c", "pass"]}])
        (root / "test_fijo.py").write_text("assert 1 == 1\n")
        config = json.loads((root / c.CONFIG).read_text())
        config["protected_files"] = ["test_*.py"]
        (root / c.CONFIG).write_text(json.dumps(config))
        c.git(root, "add", ".")
        c.git(root, "commit", "-qm", "Proteger prueba")

        def fake(worktree, *args):
            (worktree / "test_fijo.py").write_text("# prueba eliminada\n")
            return {"codigo": 0, "motivo_parada": None}

        with patch.object(c, "stream_agent", fake), contextlib.redirect_stdout(io.StringIO()):
            result = c.task(root, "No ocultar pruebas", warm=False)
        self.assertTrue(all(x["codigo"] == 0 for x in result["despues"]))
        self.assertEqual(result["estado"], "requiere_revision")
        self.assertEqual(result["protegidos_modificados"], ["test_fijo.py"])

    def test_failed_verification_triggers_correction_in_same_session(self):
        root = self.repo(
            [
                {
                    "name": "valor",
                    "argv": ["python3", "-c", "from codigo import valor; assert valor == 2"],
                }
            ]
        )
        calls = []

        def fake(worktree, prompt, directory, seconds, actions, session_id=None):
            calls.append((prompt, session_id))
            (worktree / "codigo.py").write_text(
                "valor = 2   \n" if len(calls) == 1 else "valor = 2\n"
            )
            return {
                "codigo": 0,
                "motivo_parada": None,
                "acciones": 1,
                "segundos": 0,
                "sesion": "ses_prueba",
            }

        with patch.object(c, "stream_agent", fake), contextlib.redirect_stdout(io.StringIO()):
            result = c.task(root, "Corregir valor", warm=False)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1][1], "ses_prueba")
        self.assertIn("trailing whitespace", calls[1][0])
        self.assertEqual(result["estado"], "verificado")
        self.assertEqual(result["agente"]["acciones"], 2)
        self.assertEqual((root / "codigo.py").read_text(), "valor = 1\n")

    def test_resume_keeps_worktree_history_and_original_checks(self):
        root = self.repo(
            [
                {
                    "name": "valor",
                    "argv": ["python3", "-c", "from codigo import valor; assert valor == 2"],
                }
            ]
        )
        with (
            patch.object(
                c,
                "stream_agent",
                return_value={
                    "codigo": 1,
                    "motivo_parada": "tiempo_maximo",
                    "sesion": "ses_prueba",
                },
            ),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            initial = c.task(root, "Corregir valor", warm=False)

        def fix(worktree, *args, **kwargs):
            self.assertEqual(kwargs["session_id"], "ses_prueba")
            (worktree / "codigo.py").write_text("valor = 2\n")
            return {
                "codigo": 0,
                "motivo_parada": None,
                "acciones": 1,
                "segundos": 0,
                "sesion": "ses_prueba",
            }

        with patch.object(c, "stream_agent", fix), contextlib.redirect_stdout(io.StringIO()):
            result = c.resume(initial["id"], warm=False)
        self.assertEqual(result["estado"], "verificado")
        self.assertEqual(result["worktree"], initial["worktree"])
        self.assertEqual(result["historial"][0]["estado"], "requiere_revision")
        self.assertEqual((root / "codigo.py").read_text(), "valor = 1\n")

    def test_resume_refuses_changed_original(self):
        root = self.repo()
        with (
            patch.object(c, "stream_agent", return_value={"codigo": 0, "motivo_parada": None}),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            initial = c.task(root, "Revisar", warm=False)
        (root / "codigo.py").write_text("Trabajo posterior del usuario\n")
        with self.assertRaisesRegex(RuntimeError, "original cambio"):
            c.resume(initial["id"], warm=False)
        self.assertEqual((root / "codigo.py").read_text(), "Trabajo posterior del usuario\n")

    def test_real_formatter_normalizes_only_changed_python(self):
        root = self.repo(
            [
                {
                    "name": "valor",
                    "argv": ["python3", "-c", "from codigo import valor; assert valor == 2"],
                }
            ]
        )
        config = json.loads((root / c.CONFIG).read_text())
        config["format_python"] = True
        (root / c.CONFIG).write_text(json.dumps(config))
        c.git(root, "add", ".")
        c.git(root, "commit", "-qm", "Activar formato")

        def fake(worktree, *args):
            (worktree / "codigo.py").write_text("valor=2    \n")
            return {"codigo": 0, "motivo_parada": None, "acciones": 1, "segundos": 0}

        with patch.object(c, "stream_agent", fake), contextlib.redirect_stdout(io.StringIO()):
            result = c.task(root, "Formato determinista", warm=False)
        self.assertEqual(result["estado"], "verificado")
        self.assertEqual(result["formato"]["codigo"], 0)
        self.assertEqual((Path(result["worktree"]) / "codigo.py").read_text(), "valor = 2\n")
        self.assertEqual((root / "codigo.py").read_text(), "valor = 1\n")

    def test_failed_loop_and_pwd(self):
        executable = self.folder / "fake-opencode"
        executable.write_text("""#!/usr/bin/env python3
import json, os, time
print(json.dumps({'type':'text','part':{'text':os.environ['PWD']}}), flush=True)
for i in range(3):
 print(json.dumps({'type':'tool_use','sessionID':'test','part':{'tool':'shell','state':{'status':'completed','input':{'command':'fallo'},'metadata':{'metadata':{'exit':1}}}}}), flush=True)
time.sleep(30)
""")
        executable.chmod(0o755)
        with patch.object(c, "BIN", executable), contextlib.redirect_stdout(io.StringIO()):
            r = c.stream_agent(self.folder, "Prueba", self.folder, 5, 10)
        self.assertEqual(r["motivo_parada"], "misma_accion_fallida_tres_veces")
        self.assertEqual(r["acciones"], 3)
        first = json.loads((self.folder / "eventos.jsonl").read_text().splitlines()[0])
        self.assertEqual(first["part"]["text"], str(self.folder))


if __name__ == "__main__":
    unittest.main(verbosity=2)
