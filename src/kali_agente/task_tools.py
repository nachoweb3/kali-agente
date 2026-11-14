"""Task archive, portable exports, worktree cleanup and offline patch review."""

import argparse
import datetime as dt
import html
from pathlib import Path
import sys
import zipfile

from .experience import task_record
from .settings import atomic_json


def graphical(identifier):
    directory, report = task_record(identifier)
    patch = (directory / "cambios.patch").read_text(encoding="utf-8", errors="replace")
    rows = []
    old = new = 0
    for line in patch.splitlines():
        category = "context"
        left = right = ""
        if line.startswith("@@"):
            import re

            match = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if match:
                old, new = map(int, match.groups())
            category = "header"
        elif line.startswith(
            (
                "diff ",
                "index ",
                "--- ",
                "+++ ",
                "new file",
                "deleted file",
                "Binary",
                "GIT binary",
                "rename ",
                "similarity ",
            )
        ):
            category = "header"
        elif line.startswith("+"):
            right, new, category = str(new), new + 1, "add"
        elif line.startswith("-"):
            left, old, category = str(old), old + 1, "remove"
        elif line.startswith(" "):
            left, right = str(old), str(new)
            old, new = old + 1, new + 1
        rows.append(
            f'<tr class="{category}"><td>{left}</td><td>{right}</td><td><pre>{html.escape(line)}</pre></td></tr>'
        )
    checks = "".join(
        f"<li>{html.escape(item['nombre'])}: {'OK' if item['codigo'] == 0 and not item['timeout'] else 'FALLO'}</li>"
        for item in report.get("despues", [])
    )
    page = """<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Kali Agente · Revision de parche</title><style>
body{background:#080f1c;color:#d6e4f5;font:16px system-ui;margin:0;padding:32px}main{max-width:1400px;margin:auto}
h1{color:#86e8ff}header{border:1px solid #304662;border-radius:18px;padding:24px;margin-bottom:24px;background:#0d192b}
.badge{color:#b8a5ff}table{border-collapse:collapse;width:100%;font:14px monospace}td{border-bottom:1px solid #26374b;padding:4px 9px;vertical-align:top}
td:first-child,td:nth-child(2){width:42px;color:#8fa5c2;text-align:right;user-select:none}pre{margin:0;white-space:pre-wrap;overflow-wrap:anywhere}
.add{background:#10362c}.remove{background:#411f2d}.header{background:#182a43;color:#a8d7ff}.diff{overflow:auto;border:1px solid #304662;border-radius:12px}
p{line-height:1.6}code{color:#b8dfff}a{color:#86e8ff}</style><main><header><p class="badge">NACHO_WEB3 / KALI AGENTE</p>"""
    page += f"<h1>Revision de tarea {html.escape(identifier)}</h1><p>{html.escape(report['objetivo'])}</p><p>Estado: <strong>{html.escape(report['estado'])}</strong></p><ul>{checks}</ul>"
    page += (
        "<p>Vista local sin scripts ni servicios externos. El contenido de archivos se muestra como texto. Para integrar, vuelve a la terminal y ejecuta <code>kali-agente aplicar "
        + html.escape(identifier)
        + "</code>. Se pedira confirmacion.</p></header>"
    )
    page += (
        '<div class="diff"><table aria-label="Parche con lineas originales y nuevas"><thead><tr><th>Antes</th><th>Despues</th><th>Cambios</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table></div></main></html>"
    )
    target = directory / "revision.html"
    target.write_text(page, encoding="utf-8")
    print("Revision grafica:", target)
    return target


def manage(action, argv):
    from . import coordinador_agente as c

    parser = argparse.ArgumentParser()
    parser.add_argument("id")
    if action == "archivar":
        parser.add_argument("--restaurar", action="store_true")
    if action == "exportar":
        parser.add_argument("--destino", type=Path, required=True)
    if action == "limpiar":
        parser.add_argument("--descartar", action="store_true")
    opts = parser.parse_args(argv)
    directory, report = task_record(opts.id)
    if action == "archivar":
        if opts.restaurar:
            report.pop("archivado", None)
        else:
            report["archivado"] = dt.datetime.now().astimezone().isoformat()
        atomic_json(directory / "informe.json", report)
        print(
            "Tarea restaurada"
            if opts.restaurar
            else "Tarea archivada; se conservan worktree, rama e informes"
        )
    elif action == "exportar":
        # Exclusive creation: never overwrite an existing archive.
        with zipfile.ZipFile(opts.destino, "x", compression=zipfile.ZIP_DEFLATED) as archive:
            for name in (
                "INFORME.md",
                "informe.json",
                "cambios.patch",
                "revision.html",
                "progreso.json",
                "respaldo-limpieza/cambios.patch",
            ):
                path = directory / name
                if path.is_file() and not path.is_symlink():
                    archive.write(path, arcname=name)
        print("Exportado:", opts.destino, "(puede contener rutas y objetivos privados)")
    elif action == "limpiar":
        worktree = directory / "proyecto"
        if worktree.is_symlink() or not worktree.is_dir():
            raise ValueError("El worktree no existe o es un enlace simbolico")
        root = Path(report["original"]).resolve()
        registered = c.git(root, "worktree", "list", "--porcelain")
        if "worktree " + str(worktree.resolve()) + "\n" not in registered + "\n":
            raise RuntimeError("El directorio no es un worktree registrado del original")
        if c.git(worktree, "ls-files", "--others", "--ignored", "--exclude-standard"):
            raise RuntimeError(
                "Hay archivos ignorados: guardalos fuera del worktree antes de limpiarlo"
            )
        dirty = bool(c.git(worktree, "status", "--porcelain"))
        if dirty and not opts.descartar:
            raise RuntimeError(
                "Hay cambios sin commit. Usa archivar o revisa --descartar para conservar un parche antes de limpiar"
            )
        backup = directory / "respaldo-limpieza"
        backup.mkdir(exist_ok=True)
        c.snapshot_diff(worktree, report["base"], backup)
        if not sys.stdin.isatty():
            raise RuntimeError("Limpiar requiere una terminal interactiva")
        if (
            input(f"Se eliminara solo {worktree}. Escribe LIMPIAR {opts.id}: ").strip()
            != "LIMPIAR " + opts.id
        ):
            print("Limpieza cancelada")
            return 1
        # Refuse a concurrent change after the confirmation.
        check = directory / "limpieza-comprobacion"
        check.mkdir(exist_ok=True)
        c.snapshot_diff(worktree, report["base"], check)
        if (backup / "cambios.patch").read_bytes() != (
            check / "cambios.patch"
        ).read_bytes() or c.git(
            worktree, "ls-files", "--others", "--ignored", "--exclude-standard"
        ):
            raise RuntimeError("El worktree cambio durante la confirmacion")
        c.git(root, "worktree", "remove", *(["--force"] if dirty else []), str(worktree.resolve()))
        report["limpieza"] = dt.datetime.now().astimezone().isoformat()
        report["archivado"] = report["limpieza"]
        atomic_json(directory / "informe.json", report)
        with (directory / "INFORME.md").open("a", encoding="utf-8") as stream:
            stream.write(
                "\n## Limpieza\n\nWorktree eliminado con confirmacion. Rama conservada y parche actual en respaldo-limpieza/cambios.patch.\n"
            )
        print("Worktree eliminado. Rama, informes y respaldo-limpieza/cambios.patch conservados.")
    return 0
