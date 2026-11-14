"""Render real program output and a static HTML review for the repository gallery.

No browser, JavaScript, network fetches or real model inference are used.
The workflow screenshot is an explicitly labelled controlled agent fixture.
Install the optional media extra; system Pango and DejaVu fonts are required.
"""

import contextlib
import argparse
import io
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageFont
import pymupdf
from weasyprint import CSS, HTML

from kali_agente import __version__
from kali_agente import coordinador_agente as coordinator
from kali_agente.task_tools import graphical

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "assets/screenshots"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def frame(width, height, title, subtitle):
    image = Image.new("RGB", (width, height), "#060b15")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (12, 12, width - 12, height - 12), radius=22, fill="#0c1626", outline="#304562", width=2
    )
    for x, color in ((38, "#80e9ff"), (62, "#6b9fff"), (86, "#bd9bff")):
        draw.ellipse((x, 37, x + 12, 49), fill=color)
    draw.text((122, 31), title, font=ImageFont.truetype(SANS, 19), fill="#c7d7ed")
    draw.line((28, 74, width - 28, 74), fill="#304562", width=1)
    draw.text((38, height - 47), subtitle, font=ImageFont.truetype(SANS, 17), fill="#9aafcc")
    return image


def terminal(name, title, output, subtitle):
    lines = []
    for line in output.splitlines():
        lines.extend(
            textwrap.wrap(line, width=87, replace_whitespace=False, drop_whitespace=False) or [""]
        )
    image = frame(1320, 140 + len(lines) * 28, title, subtitle)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT, 22)
    for index, line in enumerate(lines):
        color = "#d9e4f5"
        if line.startswith("$ "):
            color = "#82eaff"
        elif "FALLO" in line:
            color = "#ffa7b6"
        elif "OK" in line or "verificado" in line:
            color = "#91e8bb"
        draw.text((38, 97 + index * 28), line, font=font, fill=color)
    image.save(DESTINATION / (name + ".png"), optimize=True)
    (DESTINATION / (name + ".txt")).write_text(output, encoding="utf-8")


def deny_fetch(url, *args, **kwargs):
    raise ValueError("External resources are disabled for repository captures")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--docker",
        action="store_true",
        help="Capture real Docker checks using an already installed image",
    )
    opts = parser.parse_args()
    DESTINATION.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="kali-gallery-") as folder:
        temporary = Path(folder)
        env = dict(
            os.environ,
            KALI_AGENT_CONFIG_DIR=str(temporary / "config"),
            KALI_AGENT_STATE_DIR=str(temporary / "state"),
        )
        commands = [
            (["--version"], "kali-agente --version"),
            (["perfiles"], "kali-agente perfiles"),
        ]
        output = []
        for args, label in commands:
            result = subprocess.run(
                [sys.executable, "-m", "kali_agente", *args],
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )
            output.extend(["$ " + label, result.stdout.rstrip(), ""])
        terminal(
            "version-perfiles",
            f"Kali Agente v{__version__} / VERSION Y PERFILES",
            "\n".join(output),
            "Salida real del programa / render de terminal / sin inferencia",
        )

        project = temporary / "proyecto"
        project.mkdir()
        (project / "app.py").write_text("def sumar(a, b):\n    return a * b\n")
        coordinator.save(
            project / ".kali-agente.json",
            {
                "checks": [
                    {
                        "name": "test-suma",
                        "argv": [
                            "python3",
                            "-c",
                            "from app import sumar; assert sumar(2,3)==5; assert sumar(-1,1)==0",
                        ],
                    }
                ],
                "format_python": False,
            },
        )
        for args in (
            ("init", "-q"),
            ("config", "user.name", "Kali Agente Demo"),
            ("config", "user.email", "demo@localhost"),
            ("add", "."),
            ("commit", "-qm", "Demo baseline"),
        ):
            coordinator.git(project, *args)

        def fixture(worktree, *args, **kwargs):
            (worktree / "app.py").write_text("def sumar(a, b):\n    return a + b\n")
            print("  [DEMO] Agente simulado: reemplazar multiplicacion por suma.")
            return dict(codigo=0, motivo_parada=None, acciones=1, segundos=0)

        with (
            patch.object(coordinator, "STATE", temporary / "state"),
            patch.object(coordinator, "stream_agent", fixture),
        ):
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                report = coordinator.task(
                    project, "DEMOSTRACION: corregir la suma de dos numeros", warm=False
                )
            with contextlib.redirect_stdout(io.StringIO()):
                html_path = graphical(report["id"])
            html_source = html_path.read_text()
            html_source = html_source.replace(report["id"], "20261114-120000-abcdef")
            (ROOT / "assets/revision-demo.html").write_text(html_source, encoding="utf-8")
            transcript = "$ kali-agente trabajar 'Corregir la suma'\n\n" + captured.getvalue()
            transcript = transcript.replace(str(temporary), "/demo").replace(
                report["id"], "20261114-120000-abcdef"
            )
            terminal(
                "tarea-verificada",
                f"Kali Agente v{__version__} / DE FALLO A PARCHE",
                transcript,
                "Demo controlada / agente simulado / Git y comprobaciones reales",
            )

            styles = CSS(
                string="""@page {size: 1200px 650px; margin: 0}
                body {font-family: 'DejaVu Sans'; font-size: 19px; padding: 30px}
                header {padding: 22px; margin-bottom: 20px}
                h1 {font-size: 29px; margin: 12px 0}
                p {line-height: 1.5; margin: 12px 0}
                table {font-family: 'DejaVu Sans Mono'; font-size: 18px}
                td {padding: 7px 10px}
                th {padding: 8px 10px; text-align: left}
                .diff {border-radius: 10px}
            """
            )
            pdf = HTML(string=html_source, url_fetcher=deny_fetch).write_pdf(stylesheets=[styles])
            with pymupdf.open(stream=pdf, filetype="pdf") as document:
                if len(document) != 1:
                    raise RuntimeError("Review capture overflowed a single page")
                pixmap = document[0].get_pixmap(matrix=pymupdf.Matrix(4 / 3, 4 / 3), alpha=False)
                content = Image.open(io.BytesIO(pixmap.tobytes("png"))).convert("RGB")
            image = frame(
                content.width + 48,
                content.height + 150,
                f"Kali Agente v{__version__} / REVISION GRAFICA",
                "HTML real de la demo / render estatico sin navegador / datos ficticios",
            )
            image.paste(content, (24, 88))
            image.save(DESTINATION / "revision-grafica.png", optimize=True)

    if opts.docker:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/check_sandbox.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
            timeout=60,
        )
        terminal(
            "docker-real",
            f"Kali Agente v{__version__} / DOCKER REAL",
            "$ python scripts/check_sandbox.py\n\n" + result.stdout,
            "Comprobaciones reales / solo lectura, sin red, escritura explicita y timeout",
        )

    metadata = {
        "version": __version__,
        "terminal": "Captured program output rendered with Pillow",
        "workflow": "Controlled agent fixture; real Git, checks and coordinator",
        "review": "Generated review HTML, static WeasyPrint render; no browser or JavaScript",
        "normalization": "Temporary paths and random task identifiers replaced with demo values",
        "network_fetches": False,
        "docker_checks_captured": opts.docker,
        "render_versions": {
            name: importlib.metadata.version(name) for name in ("Pillow", "weasyprint", "pymupdf")
        },
    }
    (DESTINATION / "provenance.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(DESTINATION)


if __name__ == "__main__":
    main()
