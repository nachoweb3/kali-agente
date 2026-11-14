"""Installed-wheel smoke test; writes only under a temporary directory."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    with tempfile.TemporaryDirectory(prefix="kali-release-") as folder:
        root = Path(folder)
        env = dict(
            os.environ,
            KALI_AGENT_CONFIG_DIR=str(root / "config"),
            KALI_AGENT_STATE_DIR=str(root / "state"),
        )
        cli = [sys.executable, "-m", "kali_agente"]

        def run(*args, cwd=root):
            return subprocess.run(
                [*cli, *args], cwd=cwd, env=env, text=True, capture_output=True, check=True
            )

        run("--help")
        run("configurar", "--modelo", "fixture:latest")
        run("banner", "--estatico")
        fake = root / "fake-opencode"
        fake.write_text(
            "#!/usr/bin/env python3\nimport json\nfrom pathlib import Path\nPath('codigo.py').write_text('valor = 2\\n')\nprint(json.dumps({'type':'text','sessionID':'fixture','part':{'text':'Hecho'}}))\n"
        )
        fake.chmod(0o755)
        # A tiny local Ollama fixture avoids downloading a model for smoke tests.
        import http.server
        import threading

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length", 0)))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"{}")

            def log_message(self, *args):
                pass

        server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            env.update(
                KALI_AGENT_OPENCODE_BIN=str(fake),
                KALI_AGENT_OLLAMA_URL=f"http://127.0.0.1:{server.server_port}",
            )
            project = root / "project"
            project.mkdir()
            (project / "codigo.py").write_text("valor = 1\n")
            (project / ".kali-agente.json").write_text(
                json.dumps(
                    {
                        "checks": [
                            {
                                "name": "value",
                                "argv": [
                                    sys.executable,
                                    "-c",
                                    "from codigo import valor; assert valor == 2",
                                ],
                            }
                        ],
                        "format_python": False,
                    }
                )
            )
            for args in (
                ("init", "-q"),
                ("config", "user.name", "Release Test"),
                ("config", "user.email", "test@localhost"),
                ("add", "."),
                ("commit", "-qm", "fixture"),
            ):
                subprocess.run(["git", "-C", str(project), *args], check=True)
            result = run(
                "trabajar", "Corrige valor", "--segundos", "30", "--acciones", "5", cwd=project
            )
            report = json.loads(next((root / "state/tareas").glob("*/informe.json")).read_text())
            assert report["estado"] == "verificado", result.stdout
            assert (project / "codigo.py").read_text() == "valor = 1\n"
            patch = Path(report["worktree"]).parent / "cambios.patch"
            assert patch.exists()
            print(
                "Installed wheel: CLI, config, banner, Ollama fixture, OpenCode fixture, worktree, verification and patch OK"
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    main()
