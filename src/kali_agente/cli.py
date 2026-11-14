"""Console interface. Linux native or inside WSL2."""

import argparse
import os
import signal
import subprocess
import sys

from . import __version__
from .settings import activate, atomic_json, config_dir, executable, request, settings


def main():
    args = sys.argv[1:]
    if args and args[0] in ("--version", "version"):
        print(__version__)
        return 0
    if args and args[0] in ("--help", "-h", "ayuda"):
        print("""KALI AGENTE Â· nacho_web3

kali-agente configurar [--modelo ID] [--url http://localhost:11434]
                       [--contexto 16384] [--salida 2048]
kali-agente estado                  Diagnostica Ollama y OpenCode
kali-agente banner [--estatico]     Robot granjero animado
kali-agente                        Abre OpenCode interactivo
kali-agente tarea 'objetivo'        Ejecuta una tarea con permisos interactivos
kali-agente auto 'objetivo'         Ejecuta aprobando permisos automaticamente
kali-agente preparar               Crea comprobaciones en el repositorio actual
kali-agente trabajar 'objetivo' [--segundos 1200] [--acciones 60]
kali-agente retomar ID             Continua la misma tarea y worktree
kali-agente verificar              Ejecuta comprobaciones del proyecto
kali-agente resultados             Lista informes locales
kali-agente banco [--caso todos]    Banco optativo con el modelo real
kali-agente opencode [argumentos]   Pasa argumentos directamente a OpenCode

Linux / WSL2. Los worktrees separan cambios; el shell tiene acceso real al sistema.
trabajar, retomar y banco aprueban herramientas automaticamente. Revisa sus parches.
""")
        return 0
    if os.name != "posix" or not sys.platform.startswith("linux"):
        raise RuntimeError("Ejecuta kali-agente dentro de Linux o WSL2.")
    if args and args[0] == "configurar":
        parser = argparse.ArgumentParser()
        parser.add_argument("--modelo", default=settings()["model"])
        parser.add_argument("--url", default=settings()["url"])
        parser.add_argument("--contexto", type=int, default=16384)
        parser.add_argument("--salida", type=int, default=2048)
        opts = parser.parse_args(args[1:])
        from .settings import validate_settings

        data = validate_settings(
            dict(model=opts.modelo, url=opts.url, context=opts.contexto, output=opts.salida)
        )
        atomic_json(config_dir() / "config.json", data)
        print("Configuracion guardada:", config_dir() / "config.json")
        return 0
    if args and args[0] == "banner":
        from .cabecera_kali import show

        show(animate="--estatico" not in args)
        return 0
    activate()
    if args and args[0] == "estado":
        model = settings()["model"]
        models = request("/api/tags")["models"]
        if not any(item["name"] == model or item["name"] == model + ":latest" for item in models):
            raise RuntimeError("Modelo no instalado en Ollama: " + model)
        print("Ollama conectado; modelo:", model)
        subprocess.run([executable("opencode"), "--version"], check=True)
        print("Git:", subprocess.check_output(["git", "--version"], text=True).strip())
        return 0
    if args and args[0] in ("preparar", "trabajar", "retomar", "verificar", "resultados", "banco"):
        import fcntl
        from . import coordinador_agente as coordinator

        with __import__("contextlib").ExitStack() as stack:
            if args[0] in ("trabajar", "retomar", "banco"):
                coordinator.STATE.mkdir(parents=True, exist_ok=True)
                lock = stack.enter_context((coordinator.STATE / "ejecucion.lock").open("a+"))
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    raise RuntimeError("Ya hay otra tarea coordinada en marcha") from None
            return coordinator.main()
    from .cabecera_kali import show

    if not args:
        show()
    if args and args[0] in ("tarea", "auto"):
        command = ["run"] + (["--auto"] if args[0] == "auto" else []) + args[1:]
    elif args and args[0] == "opencode":
        command = args[1:]
    elif args:
        raise ValueError("Comando desconocido. Consulta kali-agente --help")
    else:
        command = []
    return subprocess.call([executable("opencode"), "--standalone", *command])


def entrypoint():
    def interrupted(signum, frame):
        raise KeyboardInterrupt

    for name in ("SIGTERM", "SIGHUP"):
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), interrupted)
    try:
        code = main()
    except KeyboardInterrupt:
        print("\nOperacion interrumpida.", file=sys.stderr)
        code = 130
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, KeyError) as exc:
        print("Error:", exc, file=sys.stderr)
        code = 1
    raise SystemExit(code)
