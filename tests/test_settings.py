import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from kali_agente.settings import atomic_json, profile, settings, validate_settings


class Settings(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.environment = patch.dict(os.environ, {"KALI_AGENT_CONFIG_DIR": str(self.path)})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        for key in ("KALI_AGENT_MODEL", "KALI_AGENT_OLLAMA_URL"):
            os.environ.pop(key, None)

    def test_environment_overrides_saved_settings(self):
        atomic_json(self.path / "config.json", {"model": "saved:latest"})
        with patch.dict(os.environ, {"KALI_AGENT_MODEL": "chosen:latest"}):
            self.assertEqual(settings()["model"], "chosen:latest")

    def test_invalid_config_is_rejected_without_replacing_previous(self):
        command = [sys.executable, "-m", "kali_agente", "configurar", "--modelo", "good:latest"]
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
        original = (self.path / "config.json").read_bytes()
        result = subprocess.run(command + ["--contexto", "512"], capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual((self.path / "config.json").read_bytes(), original)

    def test_urls_reject_embedded_credentials(self):
        for url in (
            "file:///etc/passwd",
            "http://user:secret@localhost:11434",
            "http://localhost?key=secret",
        ):
            with self.assertRaises(ValueError):
                validate_settings(dict(url=url, model="model", context=16384, output=2048))

    def test_profile_uses_selected_endpoint_and_full_model_name(self):
        atomic_json(
            self.path / "config.json", {"model": "org/model:tag", "url": "http://localhost:1234/"}
        )
        data = profile()
        self.assertEqual(data["model"], "ollama/org/model:tag")
        self.assertIn("org/model:tag", data["providers"]["ollama"]["models"])
        self.assertEqual(
            data["providers"]["ollama"]["settings"]["baseURL"], "http://localhost:1234/v1"
        )
        self.assertFalse((self.path / "opencode.json").exists())

    def test_atomic_json_is_valid_and_private(self):
        target = self.path / "nested/config.json"
        atomic_json(target, {"a": 1})
        atomic_json(target, {"b": 2})
        self.assertEqual(json.loads(target.read_text()), {"b": 2})
        self.assertEqual(target.stat().st_mode & 0o077, 0)
        self.assertEqual(list(target.parent.glob(".config-*")), [])

    def test_help_and_static_banner_need_no_provider(self):
        for args in (["--help"], ["banner", "--estatico"]):
            result = subprocess.run(
                [sys.executable, "-m", "kali_agente", *args], capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(result.stdout.strip())
