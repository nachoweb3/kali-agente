"""Guided setup, progress and review of verified changes."""

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from .settings import atomic_json, config_dir, executable, request, settings


def progress(directory, phase, **details):
    path = directory / "progreso.json"
    previous = json.loads(path.read_text()) if path.exists() else {}
    previous.update(details, fase=phase, actualizado=dt.datetime.now().astimezone().isoformat())
    atomic_json(path, previous)


def setup(argv):
    parser = argparse.ArgumentParser(
        description="Comprueba dependencias y elige un modelo instalado"
    )
    parser.add_argument("--modelo")
    opts = parser.parse_args(argv)
    for tool in ("git", "opencode"):
        try:
            result = subprocess.run(
                [executable(tool), "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            hint = (
                "https://opencode.ai/docs/"
                if tool == "opencode"
                else "el gestor de paquetes de tu distribucion"
            )
            raise RuntimeError(
                f"Falta {tool} o no responde. Instala la dependencia desde {hint}. Detalle: {exc}"
            ) from None
        print(f"[OK] {tool}: {result.stdout.strip()}")
    try:
        models = request("/api/tags")["models"]
    except (OSError, ValueError, KeyError) as exc:
        raise RuntimeError(
            "Ollama no responde. Inicia Ollama y revisa la URL con configurar --url. " + str(exc)
        ) from None
    names = sorted({model["name"] for model in models})
    if not names:
        raise RuntimeError(
            "Ollama responde pero no tiene modelos. Instala uno compatible con herramientas y repite iniciar."
        )
    for index, name in enumerate(names, 1):
        print(f"  {index}. {name}")
    chosen = opts.modelo
    current = settings()["model"]
    if chosen is None:
        if not sys.stdin.isatty():
            raise ValueError(
                "Sin terminal interactiva: indica iniciar --modelo NOMBRE. No se guardaron cambios."
            )
        answer = input(f"Modelo (numero o nombre; Enter conserva {current}): ").strip()
        chosen = (
            names[int(answer) - 1]
            if answer.isdecimal() and 1 <= int(answer) <= len(names)
            else answer or current
        )
    if chosen not in names and chosen + ":latest" in names:
        chosen += ":latest"
    if chosen not in names:
        raise ValueError(
            "Elige uno de los modelos instalados; no se descargara ninguno automaticamente"
        )
    effective = os.environ.get("KALI_AGENT_MODEL")
    if effective and effective != chosen:
        raise ValueError(
            "KALI_AGENT_MODEL prevalece sobre el archivo. Ajusta esa variable antes de elegir otro modelo."
        )
    conf = settings()
    conf["model"] = chosen
    atomic_json(config_dir() / "config.json", conf)
    print("[OK] Configuracion guardada. Conexion con Ollama comprobada.")
    print(
        "El soporte de herramientas y la calidad dependen del modelo. Ejecuta kali-agente para empezar."
    )
    return 0


def task_record(identifier):
    from . import coordinador_agente as c

    if not re.fullmatch(r"\d{8}-\d{6}-[0-9a-f]{6}", identifier):
        raise ValueError("Identificador de tarea no valido")
    directory = c.STATE / "tareas" / identifier
    report = json.loads((directory / "informe.json").read_text())
    if (
        report["id"] != identifier
        or Path(report["worktree"]).resolve() != (directory / "proyecto").resolve()
    ):
        raise ValueError("El informe no coincide con la tarea registrada")
    return directory, report


def digest(data):
    return hashlib.sha256(data).hexdigest()


def review(identifier):
    directory, report = task_record(identifier)
    patch = (directory / "cambios.patch").read_bytes()
    print(f"Tarea: {identifier}\nEstado: {report['estado']}\nObjetivo: {report['objetivo']}")
    print("Original:", report["original"], "\nWorktree:", report["worktree"])
    for check in report.get("despues", []):
        print(
            f"  {check['nombre']}: {'OK' if check['codigo'] == 0 and not check['timeout'] else 'FALLO'}"
        )
    print("\n--- PARCHE ---\n" + patch.decode("utf-8", errors="replace"))
    atomic_json(directory / "revision.json", {"sha256": digest(patch)})
    print("Revision registrada para este parche. Aplicar exigira confirmacion en terminal.")
    return 0


def apply(identifier):
    from . import coordinador_agente as c

    directory, report = task_record(identifier)
    if report.get("aplicacion"):
        raise RuntimeError("Esta tarea ya se integro")
    if report["estado"] != "verificado":
        raise RuntimeError("Solo se pueden aplicar tareas verificadas. Corrige o retoma la tarea.")
    patch = directory / "cambios.patch"
    contents = patch.read_bytes()
    if not contents:
        raise RuntimeError("La tarea no contiene cambios")
    receipt = directory / "revision.json"
    if not receipt.exists() or json.loads(receipt.read_text()).get("sha256") != digest(contents):
        raise RuntimeError("Revisa este parche primero: kali-agente revisar " + identifier)
    root, worktree = Path(report["original"]).resolve(), Path(report["worktree"]).resolve()

    def unchanged():
        if c.git(root, "rev-parse", "HEAD") != report["base"] or c.git(
            root, "status", "--porcelain"
        ):
            raise RuntimeError("El proyecto original cambio o esta sucio; no se aplico el parche")
        (directory / "integracion").mkdir(exist_ok=True)
        c.snapshot_diff(worktree, report["base"], directory / "integracion")
        if (
            directory / "integracion/cambios.patch"
        ).read_bytes() != contents or patch.read_bytes() != contents:
            raise RuntimeError(
                "El parche o worktree cambio desde la revision; retoma y revisa de nuevo"
            )

    unchanged()
    config = json.loads((directory / "comprobaciones-originales.json").read_text())
    captured_hash = digest(json.dumps(config, sort_keys=True).encode())
    if report.get("config_sha256") != captured_hash:
        raise RuntimeError("Las comprobaciones capturadas cambiaron; no se aplico el parche")
    checks = c.verify(worktree, config, directory, "integracion")
    if not config.get("checks") or any(item["codigo"] != 0 or item["timeout"] for item in checks):
        raise RuntimeError("Las comprobaciones ya no pasan; no se aplico el parche")
    protected = report.get("protegidos_originales", {})
    if c.protected_hashes(worktree, config, list(protected)) != protected:
        raise RuntimeError("Los archivos protegidos cambiaron; no se aplico el parche")
    unchanged()
    c.git(root, "apply", "--check", "--index", str(patch.resolve()))
    if not sys.stdin.isatty():
        raise RuntimeError("Aplicar requiere confirmacion en una terminal interactiva")
    confirmation = "APLICAR " + identifier
    if input(f"Se integraran cambios en {root}. Escribe {confirmation}: ").strip() != confirmation:
        print("Integracion cancelada; original sin cambios.")
        return 1
    unchanged()
    c.git(root, "apply", "--index", str(patch.resolve()))
    print("Parche aplicado y preparado en Git. Revisa git diff --cached antes de crear tu commit.")
    report["aplicacion"] = {
        "fecha": dt.datetime.now().astimezone().isoformat(),
        "sha256": digest(contents),
    }
    c.write_report(directory, report)
    progress(directory, "aplicada", ultimo="Cambios preparados en Git; pendiente de commit")
    with (directory / "INFORME.md").open("a", encoding="utf-8") as stream:
        stream.write(
            "\n## Integracion\n\nParche aplicado con confirmacion; cambios preparados en Git, sin commit automatico.\n"
        )
    return 0


def dashboard(argv):
    from . import coordinador_agente as c

    parser = argparse.ArgumentParser()
    parser.add_argument("--seguir", action="store_true")
    opts = parser.parse_args(argv)
    if opts.seguir and not sys.stdout.isatty():
        raise ValueError("--seguir requiere una terminal interactiva")
    while True:
        if opts.seguir:
            print("\033[2J\033[H", end="")
        print("KALI AGENTE / TAREAS" + (" / Ctrl+C para salir del panel" if opts.seguir else ""))
        paths = sorted((c.STATE / "tareas").glob("*/informe.json"), reverse=True)[:20]
        if not paths:
            print("Todavia no hay tareas. Usa preparar y trabajar dentro de un repositorio Git.")
        for path in paths:
            report = json.loads(path.read_text())
            live_path = path.parent / "progreso.json"
            live = json.loads(live_path.read_text()) if live_path.exists() else {}
            status = "aplicada" if report.get("aplicacion") else report["estado"]
            print(f"\n{report['id']} | {status} | {report['objetivo'][:90]}")
            print(
                f"  Ultimo registro: {live.get('fase', report['estado'])}; {live.get('actualizado', '-')}"
            )
            print(
                f"  Acciones: {live.get('acciones', '-')} | segundos: {live.get('segundos', '-')} | ultimo: {live.get('ultimo', '-')}"
            )
            print("  Informe:", path.parent / "INFORME.md")
        if not opts.seguir:
            return 0
        time.sleep(1)
