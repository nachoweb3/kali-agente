"""Versioned inference settings; model weights remain external."""

import argparse
import json

from .settings import atomic_json, config_dir, request, settings, validate_settings

PROFILES = {
    "equilibrado": {"context": 16384, "output": 2048, "temperature": 0.1, "seed": 42},
    "determinista": {"context": 16384, "output": 2048, "temperature": 0, "seed": 42},
    "contexto-amplio": {"context": 32768, "output": 4096, "temperature": 0.1, "seed": 42},
}


def select(argv):
    parser = argparse.ArgumentParser(
        description="Perfiles de parametros; no descargan ni cambian pesos"
    )
    parser.add_argument("nombre", nargs="?", choices=list(PROFILES))
    parser.add_argument("--modelo")
    opts = parser.parse_args(argv)
    if not opts.nombre:
        print(json.dumps(PROFILES, indent=2))
        return 0
    conf = settings()
    conf.update(PROFILES[opts.nombre], profile=opts.nombre)
    if opts.modelo:
        conf["model"] = opts.modelo
    models = request("/api/tags")["models"]
    if not any(
        item["name"] == conf["model"] or item["name"] == conf["model"] + ":latest"
        for item in models
    ):
        raise RuntimeError("El modelo debe estar instalado antes de seleccionar el perfil")
    import os

    if os.environ.get("KALI_AGENT_MODEL") and os.environ["KALI_AGENT_MODEL"] != conf["model"]:
        raise ValueError("KALI_AGENT_MODEL prevalece sobre el perfil; ajusta la variable")
    atomic_json(config_dir() / "config.json", validate_settings(conf))
    print("Perfil guardado:", opts.nombre, "/ modelo:", conf["model"])
    print("Los parametros no garantizan identicas salidas en distinto hardware o versiones.")
    return 0
