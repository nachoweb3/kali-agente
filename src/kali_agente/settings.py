"""Portable user settings and explicitly selected local provider."""

import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
import time
import urllib.parse
import urllib.request

DEFAULT_MODEL = "huihui_ai/qwen3-coder-abliterated:30b"


def config_dir():
    return Path(
        os.environ.get(
            "KALI_AGENT_CONFIG_DIR",
            Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "kali-agente",
        )
    )


def executable(name):
    override = os.environ.get("KALI_AGENT_" + name.upper() + "_BIN")
    if override:
        return override
    found = shutil.which(name)
    if found:
        return found
    for candidate in [Path.home() / ".local/bin" / name, Path.home() / ".opencode/bin" / name]:
        if candidate.is_file():
            return str(candidate)
    return name


def settings():
    path = config_dir() / "config.json"
    data = json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(data, dict):
        raise ValueError("config.json debe contener un objeto")
    result = dict(model=DEFAULT_MODEL, url="http://127.0.0.1:11434", context=16384, output=2048)
    result.update(data)
    for key, env in [("model", "KALI_AGENT_MODEL"), ("url", "KALI_AGENT_OLLAMA_URL")]:
        result[key] = os.environ.get(env, result[key])
    return validate_settings(result)


def validate_settings(result):
    if not isinstance(result["url"], str):
        raise ValueError("La URL de Ollama debe ser texto")
    url = urllib.parse.urlsplit(result["url"])
    if (
        url.scheme not in ("http", "https")
        or not url.hostname
        or url.username
        or url.password
        or url.query
        or url.fragment
    ):
        raise ValueError("URL de Ollama invalida; utiliza http(s) sin credenciales ni parametros")
    result["url"] = result["url"].rstrip("/")
    if not isinstance(result["model"], str) or not result["model"].strip():
        raise ValueError("Modelo vacio")
    if (
        any(type(result[key]) is not int for key in ("context", "output"))
        or not 8192 <= result["context"] <= 1048576
        or not 128 <= result["output"] <= result["context"] // 2
    ):
        raise ValueError("Contexto: 8192..1048576; salida: 128..contexto/2")
    if type(result.get("seed", 42)) is not int or not 0 <= result.get("seed", 42) <= 2147483647:
        raise ValueError("Seed valido: entero 0..2147483647")
    temperature = result.get("temperature", 0.1)
    if type(temperature) not in (int, float) or not 0 <= temperature <= 2:
        raise ValueError("Temperatura valida: 0..2")
    return result


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".config-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def profile():
    conf = settings()
    data = json.loads(Path(__file__).with_name("profile.json").read_text())
    item = next(iter(data["providers"]["ollama"]["models"].values()))
    item["limit"] = {"context": conf["context"], "output": conf["output"]}
    item["body"] = {
        "temperature": conf.get("temperature", 0.1),
        "seed": conf.get("seed", 42),
        "max_tokens": conf["output"],
    }
    data["model"] = "ollama/" + conf["model"]
    data["providers"]["ollama"]["models"] = {conf["model"]: item}
    data["providers"]["ollama"]["settings"]["baseURL"] = conf["url"] + "/v1"
    return data


def activate():
    # Content is regenerated per invocation; never replaces the user's OpenCode files.
    os.environ["OPENCODE_CONFIG_CONTENT"] = json.dumps(profile(), ensure_ascii=False)
    os.environ["OPENCODE_DISABLE_FREE_MODELS"] = "true"


def request(path, data=None, timeout=5):
    req = urllib.request.Request(
        settings()["url"] + path,
        data=None if data is None else json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def warm_model():
    print("Preparando el modelo local (hasta 180 s)...", flush=True)
    finished = threading.Event()
    started = time.monotonic()

    def notice():
        while not finished.wait(10):
            print(
                f"  Esperando a Ollama: {int(time.monotonic() - started)} s. Ctrl+C para cancelar.",
                flush=True,
            )

    worker = threading.Thread(target=notice, daemon=True)
    worker.start()
    try:
        request(
            "/api/generate",
            {"model": settings()["model"], "keep_alive": "30m", "stream": False},
            timeout=180,
        )
    finally:
        finished.set()
        worker.join()
