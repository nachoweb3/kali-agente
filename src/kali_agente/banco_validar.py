"""Comprobaciones del banco, almacenadas fuera del proyecto que edita el agente."""

import importlib.util
import json
from pathlib import Path
import sys
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer


def load(root, name):
    spec = importlib.util.spec_from_file_location("candidate", root / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate(case, root):
    if case == "python-error":
        fn = load(root, "listas.py").sin_duplicados
        for values, expected in [
            ([], []),
            ([3, 1, 3, 2, 1], [3, 1, 2]),
            ([-2, 0, -2, 1], [-2, 0, 1]),
            ([5, 5], [5]),
        ]:
            original = values.copy()
            assert fn(values) == expected, (values, expected)
            assert values == original, "Modifico la lista recibida"
        return 8
    if case == "python-funcion":
        fn = load(root, "texto.py").slugify
        cases = {
            "¡Hola, mundo!": "hola-mundo",
            "  Árbol___Azul 42 ": "arbol-azul-42",
            "café con leche": "cafe-con-leche",
            "a---b": "a-b",
            "": "",
            "---": "",
            "中文": "",
            "Python3": "python3",
        }
        for text, expected in cases.items():
            assert fn(text) == expected, (text, expected)
        return len(cases)
    if case != "web-api":
        raise ValueError("Caso desconocido")
    module = load(root, "app.py")
    server = HTTPServer(("127.0.0.1", 0), module.Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    base = f"http://127.0.0.1:{server.server_port}"

    def request(path):
        try:
            response = urllib.request.urlopen(base + path, timeout=3)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            return response.status, json.load(response)

    try:
        for a, b in [(2, 3), (-1, 1), (0, 4), (1.5, 2.5)]:
            code, data = request(f"/api/sumar?a={a}&b={b}")
            assert code == 200 and data["resultado"] == a + b, (code, data)
        assert request("/api/sumar?a=mal&b=3")[0] == 400
        assert request("/api/sumar?a=1")[0] == 400
        assert request("/no-existe")[0] == 404
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)
    return 7


if __name__ == "__main__":
    count = validate(sys.argv[1], Path(sys.argv[2]).resolve())
    print(json.dumps({"caso": sys.argv[1], "comprobaciones_correctas": count, "estado": "OK"}))
