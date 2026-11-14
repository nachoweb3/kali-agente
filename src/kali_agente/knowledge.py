"""Small attributed playbooks selected explicitly or by the user's objective."""

import argparse
import json
from pathlib import Path
import re

from .settings import atomic_json


def library():
    return json.loads(Path(__file__).with_name("playbooks.json").read_text(encoding="utf-8"))


def choose(objective, selected=None):
    guides = library()["guides"]
    if selected:
        if selected not in guides:
            raise ValueError("Guia desconocida")
        return selected, guides[selected]["text"]
    objective = objective.lower()
    categories = [
        ("evidencias", ("informe", "evidencia", "report", "redact")),
        ("codigo", ("codigo", "código", "script", "compil", "despleg", "programa")),
        ("validacion", ("hallazgo", "falso positivo", "vulnerabilidad", "validar")),
        ("web-api", ("http", "api", "web", "cookie", "autentic", "autoriz")),
    ]
    key = next(
        (key for key, words in categories if any(word in objective for word in words)),
        "diagnostico",
    )
    return key, guides[key]["text"]


def guides_cli(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("nombre", nargs="?", choices=list(library()["guides"]))
    opts = parser.parse_args(argv)
    data = library()
    if opts.nombre:
        item = data["guides"][opts.nombre]
        print(item["description"] + "\n\n" + item["text"])
    else:
        for name, item in data["guides"].items():
            print(f"{name:15} {item['description']}")
    print("\nAdaptacion: Claude-BugHunter / Sachin Sharma, CC BY 4.0")
    print(data["attribution"]["source"])
    return 0


def skills_cli(argv):
    directory = Path(__file__).with_name("skills")
    files = {path.parent.name: path for path in sorted(directory.glob("*/SKILL.md"))}
    parser = argparse.ArgumentParser(description="Skills empaquetadas y disponibles para OpenCode")
    parser.add_argument("nombre", nargs="?", choices=list(files))
    opts = parser.parse_args(argv)
    if opts.nombre:
        print(files[opts.nombre].read_text(encoding="utf-8"))
    else:
        for name, path in files.items():
            text = path.read_text(encoding="utf-8")
            description = next(
                line.removeprefix("description: ")
                for line in text.splitlines()
                if line.startswith("description:")
            )
            print(name + "\n  " + description)
        print(
            "\nOpenCode puede cargarlas con su herramienta skill; tambien puedes mencionar @NOMBRE."
        )
    return 0


def notebook(argv):
    parser = argparse.ArgumentParser(
        description="Crea un cuaderno local con objetivo, scripts y evidencias"
    )
    parser.add_argument("nombre")
    parser.add_argument("--objetivo", required=True)
    parser.add_argument("--alcance", default="Pendiente de concretar con el usuario")
    opts = parser.parse_args(argv)
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}", opts.nombre):
        raise ValueError("Nombre: 1..64 letras, numeros, guion o guion bajo")
    directory = Path.cwd() / ".kali-cuadernos" / opts.nombre
    directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    for name in ("scripts", "evidencias", "informes"):
        (directory / name).mkdir(mode=0o700)
    atomic_json(directory / "objetivo.json", {"objetivo": opts.objetivo, "alcance": opts.alcance})
    (directory / "notas.md").write_text(
        "# Notas de trabajo\n\n## Observaciones\n\n## Hipotesis pendientes\n\n## Siguiente paso\n",
        encoding="utf-8",
    )
    (directory / "informes/plantilla.md").write_text(
        "# Informe\n\n## Objetivo y alcance\n\n## Entorno y versiones\n\n## Pasos y comandos\n\n## Resultado esperado y observado\n\n## Evidencias y limites\n\n## Correccion y comprobacion\n\nEstado: no confirmado hasta disponer de evidencia. Revisar secretos antes de compartir.\n",
        encoding="utf-8",
    )
    print("Cuaderno:", directory.resolve())
    return 0
