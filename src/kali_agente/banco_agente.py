"""Banco reproducible de tres tareas pequenas para el Qwen local en OpenCode."""

import datetime as dt
import hashlib
import json
import platform
import os
import subprocess
import sys
from .settings import warm_model, settings
import time
import uuid

from .coordinador_agente import HERE, STATE, git, save, task
from . import __version__
from .settings import executable, request, profile

CASES = {
    "python-error": {
        "files": {"listas.py": "def sin_duplicados(items):\n    return sorted(set(items))\n"},
        "objective": "Corrige sin_duplicados en listas.py: debe quitar duplicados de una lista de enteros conservando el orden de primera aparicion y sin modificar la lista de entrada. Prueba el resultado con la comprobacion configurada.",
    },
    "python-funcion": {
        "files": {"texto.py": 'def slugify(text):\n    raise NotImplementedError("Pendiente")\n'},
        "objective": "Implementa slugify(text) en texto.py con biblioteca estandar. Debe convertir a minusculas, quitar acentos, separar palabras con un unico guion, tratar espacios y guiones bajos como separadores, quitar puntuacion, conservar digitos y letras ASCII, y eliminar guiones iniciales/finales. Texto sin caracteres ASCII utiles devuelve cadena vacia. Ejemplo: ¡Hola, mundo! -> hola-mundo; Árbol___Azul 42 -> arbol-azul-42. Ejecuta la comprobacion configurada.",
    },
    "web-api": {
        "files": {
            "app.py": """import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path != "/api/sumar":
            return self.reply(404, {"error": "Ruta no encontrada"})
        args = parse_qs(url.query)
        try:
            a, b = float(args["a"][0]), float(args["b"][0])
        except (KeyError, ValueError):
            return self.reply(400, {"error": "Parametros invalidos"})
        return self.reply(200, {"resultado": a * b})

if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
"""
        },
        "objective": "Corrige la API HTTP de app.py: GET /api/sumar?a=2&b=3 debe devolver resultado 5. Conserva el soporte de decimales, los errores 400 para parametros invalidos o ausentes y 404 para rutas desconocidas. Ejecuta la comprobacion configurada; no dejes servidores corriendo en segundo plano.",
    },
}

CASES.update(
    {
        "multiarchivo": {
            "files": {
                "precios.py": "def total(items):\n    return sum(items)\n",
                "factura.py": "from precios import total\ndef factura(items, iva):\n    return total(items) + iva\n",
            },
            "objective": "Corrige precios.total para sumar precio*cantidad de una lista de diccionarios y factura.factura para aplicar un IVA porcentual sobre esa base. No mutes los datos. Conserva ambas funciones publicas y usa comprobaciones configuradas.",
        },
        "jsonl": {
            "files": {"lector.py": "def leer(text):\n    return []\n"},
            "objective": "Implementa lector.leer(text): lee objetos JSON uno por linea, ignora lineas vacias, devuelve la lista de objetos dict en orden y lanza ValueError para JSON invalido o valores que no sean objetos. No uses dependencias.",
        },
        "cli": {
            "files": {"main.py": "print('pendiente')\n"},
            "objective": "Implementa main.py como CLI de biblioteca estandar. --nombre NOMBRE imprime exactamente Hola, NOMBRE! con salto de linea y exit 0. --help debe terminar con 0. Si falta --nombre o hay argumentos desconocidos debe terminar con codigo 2 sin traceback. Usa argparse.",
        },
    }
)


def manifest():
    conf = settings()
    models = request("/api/tags")["models"]
    selected = next(
        (item for item in models if item["name"] in (conf["model"], conf["model"] + ":latest")), {}
    )

    def version(tool):
        return subprocess.check_output(
            [executable(tool), "--version"], text=True, timeout=15
        ).strip()

    source = "".join(
        hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        for name in (
            "banco_validar.py",
            "banco_agente.py",
            "coordinador_agente.py",
            "settings.py",
            "profile.json",
        )
    )
    cpu = "unknown"
    if __import__("pathlib").Path("/proc/cpuinfo").exists():
        cpu = next(
            (
                line.split(":", 1)[1].strip()
                for line in __import__("pathlib").Path("/proc/cpuinfo").read_text().splitlines()
                if line.startswith("model name")
            ),
            cpu,
        )
    return {
        "version": __version__,
        "runner_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "suite_sha256": hashlib.sha256(json.dumps(CASES, sort_keys=True).encode()).hexdigest(),
        "configuracion": {key: conf.get(key) for key in ("model", "context", "output", "profile")},
        "peticion_sha256": hashlib.sha256(
            json.dumps(profile(), sort_keys=True).encode()
        ).hexdigest(),
        "muestreo": {"temperature": conf.get("temperature", 0.1), "seed": conf.get("seed", 42)},
        "modelo_digest": selected.get("digest"),
        "modelo_bytes": selected.get("size"),
        "versiones": {
            "python": platform.python_version(),
            "opencode": version("opencode"),
            "git": version("git"),
            "ollama": request("/api/version").get("version"),
        },
        "hardware": {
            "cpu": cpu,
            "arquitectura": platform.machine(),
            "cpus": os.cpu_count(),
            "memoria_bytes": os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE"),
        },
    }


def run_bank(selected="todos", repetitions=1, seconds=600, actions=30):
    if not 1 <= repetitions <= 10 or not 30 <= seconds <= 7200 or not 1 <= actions <= 200:
        raise ValueError("Repeticiones 1..10, segundos 30..7200, acciones 1..200")
    start = time.monotonic()
    identifier = dt.datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    directory = STATE / "banco" / identifier
    directory.mkdir(parents=True)
    validator = HERE / "banco_validar.py"
    digest = hashlib.sha256(validator.read_bytes()).hexdigest()
    metadata = manifest()
    metadata["limites"] = {"repeticiones": repetitions, "segundos": seconds, "acciones": actions}
    save(directory / "manifest.json", metadata)
    warm_model()
    results = []
    names = list(CASES) if selected == "todos" else [selected]
    names = [(name, iteration) for iteration in range(1, repetitions + 1) for name in names]
    for name, iteration in names:
        fixture = CASES[name]
        root = directory / (name + "-" + str(iteration))
        root.mkdir()
        for filename, content in fixture["files"].items():
            (root / filename).write_text(content, encoding="utf-8")
        (root / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n", encoding="utf-8")
        (root / "AGENTS.md").write_text(
            "Resuelve la tarea editando solo el codigo del proyecto. No modifiques .kali-agente.json, las pruebas externas ni este archivo. Usa la comprobacion configurada. No instales dependencias: todos los ejercicios usan la biblioteca estandar de Python.\n",
            encoding="utf-8",
        )
        save(
            root / ".kali-agente.json",
            {
                "checks": [
                    {
                        "name": "validacion-" + name,
                        "argv": [sys.executable, str(validator), name, "."],
                        "timeout": 30,
                    }
                ]
            },
        )
        git(root, "init", "-q")
        git(root, "config", "user.name", "Kali Agent Bench")
        git(root, "config", "user.email", "bench@localhost")
        git(root, "add", ".")
        git(root, "commit", "-qm", "Caso de referencia con fallo conocido")
        print("\n=== BANCO:", name, "===", flush=True)
        result = task(root, fixture["objective"], seconds=seconds, max_actions=actions, warm=False)
        baseline_failed = any(
            x["codigo"] != 0
            for x in result.get("antes", [])
            if x["nombre"].startswith("validacion-")
        )
        valid = (
            result["estado"] == "verificado"
            and baseline_failed
            and digest == hashlib.sha256(validator.read_bytes()).hexdigest()
        )
        results.append(
            {
                "caso": name,
                "repeticion": iteration,
                "correcto": valid,
                "tarea": result["id"],
                "estado": result["estado"],
                "segundos_agente": result.get("agente", {}).get("segundos"),
                "acciones": result.get("agente", {}).get("acciones"),
                "fallo_inicial_reproducido": baseline_failed,
            }
        )
        save(directory / "resultados.json", {"casos": results, "completado": False})
        if result["estado"] == "interrumpido":
            break
    score = sum(item["correcto"] for item in results)
    summary = {
        "manifest": metadata,
        "modelo": "ollama/" + settings()["model"],
        "framework": "OpenCode",
        "casos": results,
        "correctos": score,
        "total": len(results),
        "segundos_totales": round(time.monotonic() - start, 2),
        "completado": len(results) == len(names)
        and all(x["estado"] != "interrumpido" for x in results),
        "validador_sin_cambios": digest == hashlib.sha256(validator.read_bytes()).hexdigest(),
        "limite": "Banco pequeno de integracion; no es una clasificacion general del modelo ni una garantia para proyectos reales.",
    }
    save(directory / "resultados.json", summary)
    markdown = (
        "# Banco local de OpenCode\n\n"
        + f"Resultado: {score}/{len(results)} casos correctos.\n\n"
        + "\n".join(
            f"- {x['caso']}: {'OK' if x['correcto'] else 'FALLO'}; {x['segundos_agente']} s; {x['acciones']} acciones; tarea {x['tarea']}"
            for x in results
        )
        + "\n\n"
        + summary["limite"]
        + "\n"
    )
    (directory / "RESULTADOS.md").write_text(markdown, encoding="utf-8")
    print(f"\nBANCO: {score}/{len(results)}. Informe: {directory / 'RESULTADOS.md'}", flush=True)
    return 130 if not summary["completado"] else (0 if score == len(results) else 1)
