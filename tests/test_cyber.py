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

from kali_agente import cyber, knowledge


class Cyber(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {})
        environment.start()
        self.addCleanup(environment.stop)

    def test_inventory_does_not_execute_detected_programs(self):
        with tempfile.TemporaryDirectory() as folder:
            tool = Path(folder) / "fake-local-tool"
            marker = Path(folder) / "should-not-exist"
            tool.write_text("#!/bin/sh\ntouch " + str(marker))
            tool.chmod(0o755)
            with patch.dict(os.environ, {"PATH": folder}):
                self.assertIn(tool.name, cyber.inventory())
            self.assertFalse(marker.exists())

    def test_help_uses_known_recipe_and_original_argv(self):
        with tempfile.TemporaryDirectory() as folder:
            tool = Path(folder) / "nmap"
            tool.write_text("#!/bin/sh\nprintf 'Nmap local fixture: %s\\n' \"$1\"\n")
            tool.chmod(0o755)
            with patch.dict(os.environ, {"PATH": folder}):
                result = cyber.local_help("nmap")
            self.assertEqual(result["codigo"], 0)
            self.assertIn("--help", result["texto"])
            self.assertEqual(result["comando_ayuda"], [str(tool), "--help"])

    def test_help_rejects_command_injection_and_paths(self):
        for name in ("nmap;id", "../../bin/sh", "-x", "nmap --help"):
            with self.assertRaises(ValueError):
                cyber.local_help(name)

    def test_local_help_can_filter_a_flag_without_model(self):
        with (
            patch.object(
                cyber,
                "local_help",
                return_value={
                    "herramienta": "nmap",
                    "ejecutable": "/nmap",
                    "codigo": 0,
                    "timeout": False,
                    "texto": "-sV: Probe versions\n-Pn: Skip discovery",
                },
            ),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            self.assertEqual(cyber.tools_cli(["ayuda", "nmap", "--buscar=-sV"]), 0)
        self.assertIn("Probe versions", output.getvalue())
        self.assertNotIn("Skip discovery", output.getvalue())

    def test_log_tail_is_bounded_and_removes_terminal_controls(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / "out.txt"
            log.write_text("x" * 10000 + "\n\033[31mvisible\033[0m\n\033]52;c;secret\a")
            text = cyber.output_tail(log, 100)
            self.assertLessEqual(len(text), 100)
            self.assertIn("visible", text)
            self.assertNotIn("\033", text)
            self.assertNotIn("secret", text)

    def test_log_reader_rejects_non_regular_file(self):
        with tempfile.TemporaryDirectory() as folder:
            fifo = Path(folder) / "fifo"
            os.mkfifo(fifo)
            with self.assertRaisesRegex(ValueError, "archivo regular"):
                cyber.output_tail(fifo)

    def test_copilot_passes_only_explicit_output_and_no_default_auto(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / "out.txt"
            log.write_text("HTTP/1.1 401 Unauthorized\n")
            with (
                patch.object(cyber, "inventory", return_value={"curl": "/usr/bin/curl"}),
                patch.object(cyber.subprocess, "call", return_value=0) as call,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                cyber.copilot(["--salida", str(log), "Explica este error HTTP"])
            args = call.call_args.args[0]
            self.assertIn("copiloto", args)
            self.assertNotIn("--auto", args)
            self.assertIn("401 Unauthorized", args[-1])
            self.assertIn("salida_compartida_no_confiable", args[-1])
            config = json.loads(os.environ["OPENCODE_CONFIG_CONTENT"])
            self.assertEqual(config["default_agent"], "copiloto")
            self.assertIn("nacho", config["agents"])

    def test_copilot_supports_continuation_and_explicit_auto(self):
        with (
            patch.object(cyber, "inventory", return_value={}),
            patch.object(cyber.subprocess, "call", return_value=0) as call,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            cyber.copilot(["--continuar", "--auto", "Implementa un script"])
        self.assertIn("--continue", call.call_args.args[0])
        self.assertIn("--auto", call.call_args.args[0])

    def test_record_preserves_metacharacters_and_exit_status(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / "capture.txt"
            env = dict(os.environ)
            command = [
                sys.executable,
                "-m",
                "kali_agente",
                "registrar",
                "--salida",
                str(log),
                "--",
                sys.executable,
                "-c",
                "import sys; print(sys.argv[1]); sys.exit(7)",
                "literal;$(id) $HOME",
            ]
            result = subprocess.run(
                command,
                env=env,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=15,
            )
            self.assertEqual(result.returncode, 7, result.stderr)
            self.assertIn("literal;$(id) $HOME", log.read_text())
            self.assertEqual(log.stat().st_mode & 0o077, 0)
            self.assertNotIn("uid=", result.stdout)
            again = subprocess.run(
                command, env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=10
            )
            self.assertNotEqual(again.returncode, 0)


class Knowledge(unittest.TestCase):
    def test_native_skills_have_frontmatter_and_are_in_config(self):
        from kali_agente.settings import profile

        source = Path(profile()["skills"][0])
        files = list(source.glob("*/SKILL.md"))
        self.assertEqual(len(files), 6)
        for path in files:
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"))
            self.assertIn("name: " + path.parent.name + "\n", text)
            self.assertIn("license: CC-BY-4.0", text)
            self.assertIn("8ac4242", text)

    def test_guides_are_compact_attributed_and_selective(self):
        data = knowledge.library()
        self.assertEqual(data["attribution"]["license"], "CC-BY-4.0")
        for guide in data["guides"].values():
            self.assertLess(len(guide["text"]), 1600)
            self.assertTrue(guide["sources"])
        self.assertEqual(knowledge.choose("Escribe un script y compilalo")[0], "codigo")
        self.assertEqual(knowledge.choose("Analiza la respuesta HTTP")[0], "web-api")
        self.assertEqual(knowledge.choose("Redacta un informe")[0], "evidencias")

    def test_notebook_creates_files_without_overwriting(self):
        with tempfile.TemporaryDirectory() as folder:
            previous = Path.cwd()
            try:
                os.chdir(folder)
                with contextlib.redirect_stdout(io.StringIO()):
                    knowledge.notebook(
                        ["mi-lab", "--objetivo", "Entender HTTP", "--alcance", "localhost"]
                    )
                root = Path(folder) / ".kali-cuadernos/mi-lab"
                self.assertTrue((root / "scripts").is_dir())
                self.assertTrue((root / "informes/plantilla.md").exists())
                self.assertEqual(
                    json.loads((root / "objetivo.json").read_text())["alcance"], "localhost"
                )
                with self.assertRaises(FileExistsError):
                    knowledge.notebook(["mi-lab", "--objetivo", "Otro"])
                with self.assertRaises(ValueError):
                    knowledge.notebook(["../../other", "--objetivo", "Otro"])
            finally:
                os.chdir(previous)
