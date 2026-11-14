"""Banco reproducible de tres tareas pequenas para el Qwen local en OpenCode."""

import datetime as dt
import hashlib
import sys
from .settings import warm_model, settings
import time
import uuid

from .coordinador_agente import HERE, STATE, git, save, task

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


def run_bank(selected="todos"):
    start = time.monotonic()
    identifier = dt.datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    directory = STATE / "banco" / identifier
    directory.mkdir(parents=True)
    validator = HERE / "banco_validar.py"
    digest = hashlib.sha256(validator.read_bytes()).hexdigest()
    warm_model()
    results = []
    names = list(CASES) if selected == "todos" else [selected]
    for name in names:
        fixture = CASES[name]
        root = directory / name
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
        result = task(root, fixture["objective"], seconds=600, max_actions=30, warm=False)
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
