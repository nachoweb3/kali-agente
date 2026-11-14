"""Optional OpenCode integration: verify actual request sampling with a local fixture."""

import http.server
import json
import os
from pathlib import Path
import tempfile
import threading

from kali_agente.settings import activate, atomic_json


def main():
    requests = []
    paths = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def reply(self, data):
            body = json.dumps(data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            paths.append(self.path)
            if self.path.endswith("/models"):
                self.reply(
                    {
                        "object": "list",
                        "data": [
                            {
                                "id": "fixture:latest",
                                "object": "model",
                                "created": 0,
                                "owned_by": "ollama",
                            }
                        ],
                    }
                )
            else:
                self.reply(
                    {
                        "models": [
                            {
                                "name": "fixture:latest",
                                "model": "fixture:latest",
                                "modified_at": "2026-11-14T00:00:00Z",
                                "size": 1000,
                                "digest": "sha256:" + "a" * 64,
                                "details": {
                                    "format": "gguf",
                                    "family": "qwen3",
                                    "families": ["qwen3"],
                                    "parameter_size": "4B",
                                    "quantization_level": "Q4_K_M",
                                },
                            }
                        ]
                    }
                )

        def do_POST(self):
            paths.append(self.path)
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            if "chat/completions" not in self.path:
                self.reply(
                    {
                        "capabilities": ["completion", "tools"],
                        "model_info": {
                            "general.architecture": "qwen3",
                            "qwen3.context_length": 16384,
                        },
                    }
                )
                return
            requests.append(data)
            if data.get("stream"):
                chunks = [
                    {
                        "id": "fixture",
                        "object": "chat.completion.chunk",
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"role": "assistant", "content": "PROFILE_OK"},
                                "finish_reason": None,
                            }
                        ],
                    },
                    {
                        "id": "fixture",
                        "object": "chat.completion.chunk",
                        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                    },
                ]
                body = (
                    "".join("data: " + json.dumps(chunk) + "\n\n" for chunk in chunks)
                    + "data: [DONE]\n\n"
                ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.reply(
                    {
                        "id": "fixture",
                        "object": "chat.completion",
                        "choices": [
                            {
                                "index": 0,
                                "message": {"role": "assistant", "content": "PROFILE_OK"},
                                "finish_reason": "stop",
                            }
                        ],
                    }
                )

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    previous = dict(os.environ)
    try:
        with tempfile.TemporaryDirectory(prefix="kali-profile-test-") as folder:
            root = Path(folder)
            os.environ["KALI_AGENT_CONFIG_DIR"] = str(root / "config")
            os.environ.pop("KALI_AGENT_MODEL", None)
            os.environ.pop("KALI_AGENT_OLLAMA_URL", None)
            atomic_json(
                root / "config/config.json",
                {
                    "model": "fixture:latest",
                    "url": f"http://127.0.0.1:{server.server_port}",
                    "temperature": 0,
                    "seed": 42,
                },
            )
            activate()
            from kali_agente import coordinador_agente as c

            c.git(root, "init", "-q")
            result = c.stream_agent(root, "Responde PROFILE_OK sin usar herramientas", root, 40, 5)
            if result["codigo"] != 0 or result["motivo_parada"]:
                print("Fixture paths:", paths)
                print((root / "eventos.jsonl").read_text())
                print((root / "agente.stderr.log").read_text())
            assert result["codigo"] == 0 and not result["motivo_parada"], result
            assert requests, "OpenCode did not reach the fixture endpoint"
            assert requests[0].get("temperature") == 0, requests[0].keys()
            assert requests[0].get("seed") == 42, requests[0].keys()
            assert requests[0].get("max_tokens") == 2048, requests[0].keys()
            print("OpenCode actual request: temperature=0, seed=42, max_tokens=2048 OK")
    finally:
        os.environ.clear()
        os.environ.update(previous)
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == "__main__":
    main()
