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
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"models":[{"name":"fixture:latest"}]}')

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
            run("iniciar", "--modelo", "fixture:latest")
            run("perfiles", "determinista")
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
            run("revisar", report["id"], "--grafico")
            assert (patch.parent / "revision.html").exists()
            run("archivar", report["id"])
            assert report["id"] not in run("tareas").stdout
            assert report["id"] in run("tareas", "--archivo").stdout
            run("archivar", report["id"], "--restaurar")
            run("exportar", report["id"], "--destino", str(root / "export.zip"))
            assert (root / "export.zip").exists()
            assert report["id"] in run("tareas").stdout
            refused = subprocess.run(
                [*cli, "aplicar", report["id"]],
                cwd=project,
                env=env,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
            )
            assert refused.returncode == 1 and "terminal interactiva" in refused.stderr
            import pty

            master, slave = pty.openpty()
            try:
                os.write(master, ("APLICAR " + report["id"] + "\n").encode())
                applied = subprocess.run(
                    [*cli, "aplicar", report["id"]],
                    cwd=project,
                    env=env,
                    stdin=slave,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                assert applied.returncode == 0, applied.stderr + applied.stdout
            finally:
                os.close(master)
                os.close(slave)
            assert (project / "codigo.py").read_text() == "valor = 2\n"
            staged = subprocess.check_output(
                ["git", "-C", str(project), "diff", "--cached", "--name-only"], text=True
            )
            assert "codigo.py" in staged
            print(
                "Installed wheel: profiles, archive/export, HTML review, wizard, dashboard, integration and verification OK"
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    main()
