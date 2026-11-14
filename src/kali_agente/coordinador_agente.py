"""Tareas OpenCode en worktrees, comprobaciones independientes y banco local."""

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import selectors
import shlex
import signal
import subprocess
import time
import uuid

HERE = Path(__file__).resolve().parent
STATE = Path(
    os.environ.get(
        "KALI_AGENT_STATE_DIR",
        Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "kali-agente",
    )
)
from .settings import atomic_json, executable, warm_model

BIN = Path(executable("opencode"))
CONFIG = ".kali-agente.json"


def save(path, data):
    atomic_json(path, data)


def git(root, *args, check=True):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if check and result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace").strip())
    return result.stdout.decode("utf-8", errors="replace").strip()


def stop_process(process):
    token = getattr(process, "_agent_run_token", None)
    owned = set()
    if token:
        marker = ("KALI_AGENT_RUN_TOKEN=" + token).encode()
        for item in Path("/proc").iterdir():
            if item.name.isdigit():
                try:
                    if marker in (item / "environ").read_bytes().split(b"\0"):
                        owned.add(int(item.name))
                except (OSError, PermissionError):
                    pass
        for pid in owned:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        except ProcessLookupError:
            pass
    # El servidor privado de OpenCode crea otra sesion: killpg del CLI no basta.
    for pid in owned:
        try:
            if marker in Path(f"/proc/{pid}/environ").read_bytes().split(b"\0"):
                os.kill(pid, signal.SIGKILL)
        except (OSError, PermissionError):
            pass


def checked(argv, cwd, output, seconds=90):
    start = time.monotonic()
    with output.open("w", encoding="utf-8") as log:
        token = uuid.uuid4().hex
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env=dict(
                os.environ,
                PWD=str(Path(cwd).resolve()),
                KALI_AGENT_RUN_TOKEN=token,
                PATH=str(Path.home() / ".local/bin") + os.pathsep + os.environ.get("PATH", ""),
                PYTHONPYCACHEPREFIX=str(output.parent / ".bytecode" / token),
            ),
        )
        process._agent_run_token = token
        try:
            code = process.wait(timeout=seconds)
            timeout = False
            stop_process(process)
        except subprocess.TimeoutExpired:
            stop_process(process)
            code, timeout = process.returncode, True
        except BaseException:
            stop_process(process)
            raise
    return {
        "comando": shlex.join(argv),
        "codigo": code,
        "timeout": timeout,
        "segundos": round(time.monotonic() - start, 2),
        "log": str(output),
        "salida_final": output.read_text(encoding="utf-8", errors="replace")[-4000:],
    }


def load_config(root):
    path = root / CONFIG
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"checks": []}
    if not isinstance(data, dict):
        raise ValueError("La configuracion debe ser un objeto JSON")
    checks = data.get("checks", [])
    if not isinstance(checks, list) or len(checks) > 12:
        raise ValueError("checks debe ser una lista de hasta 12 comprobaciones")
    for item in checks:
        if not isinstance(item, dict):
            raise ValueError("Cada check debe ser un objeto JSON")
        args = item.get("argv")
        if not isinstance(args, list) or not args or not all(isinstance(x, str) for x in args):
            raise ValueError("Cada check necesita argv como lista de argumentos")
        limit = item.get("timeout", 90)
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 600:
            raise ValueError("El timeout de cada check debe estar entre 1 y 600 segundos")
    return data


def protected_hashes(root, config, names=None):
    patterns = config.get("protected_files", [])
    if not isinstance(patterns, list) or not all(isinstance(x, str) for x in patterns):
        raise ValueError("protected_files debe ser una lista de patrones de ruta")
    patterns = patterns + [CONFIG]
    if names is None:
        names = [
            name
            for name in git(root, "ls-files", "-z").split("\0")
            if name and any(fnmatch.fnmatchcase(name, p) for p in patterns)
        ]
    result = {}
    for name in names:
        path = root / name
        if not path.is_file():
            result[name] = None
            continue
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(131072), b""):
                digest.update(chunk)
        result[name] = digest.hexdigest()
    return result


def verify(root, config, directory, phase):
    directory.mkdir(parents=True, exist_ok=True)
    results = []
    # Git tambien detecta errores de espacio en cambios ya preparados en el indice.
    commands = [
        {"name": "git-diff-check", "argv": ["git", "diff", "HEAD", "--check"], "timeout": 30}
    ]
    commands += config.get("checks", [])
    for i, item in enumerate(commands):
        result = checked(
            item["argv"], root, directory / f"{phase}-{i:02d}.log", item.get("timeout", 90)
        )
        result["nombre"] = item.get("name", f"check-{i}")
        results.append(result)
        print(
            f"  [{phase}] {result['nombre']}: "
            + ("OK" if result["codigo"] == 0 and not result["timeout"] else "FALLO"),
            flush=True,
        )
    return results


def format_candidate(root, config, directory, phase, base):
    """Formato determinista antes de validar; solo archivos Python cambiados."""
    skipped = {"nombre": "formato-python", "codigo": 0, "timeout": False, "omitido": True}
    if not config.get("format_python", True):
        return dict(skipped, motivo="desactivado en el proyecto")
    formatter = Path(executable("ruff"))
    if not formatter.is_file():
        return dict(skipped, motivo="ruff no instalado")
    names = set(git(root, "diff", base, "--name-only", "-z").split("\0"))
    names.update(git(root, "ls-files", "--others", "--exclude-standard", "-z").split("\0"))
    files = []
    for name in sorted(names):
        if not name or Path(name).suffix not in (".py", ".pyi"):
            continue
        path = root / name
        if path.is_file() and path.resolve().is_relative_to(root.resolve()):
            files.append(name)
    if not files:
        return dict(skipped, motivo="sin archivos Python modificados")
    if len(files) > 500:
        raise RuntimeError("Demasiados archivos para formatear automaticamente; revisa el alcance")
    result = checked(
        [str(formatter), "format", "--", *files], root, directory / (phase + "-formato.log"), 60
    )
    result["nombre"] = "formato-python"
    print("  Formato Python: " + ("OK" if result["codigo"] == 0 else "FALLO"), flush=True)
    return result


def stream_agent(worktree, prompt, directory, seconds, max_actions, session_id=None):
    start = time.monotonic()
    count = 0
    failures = {}
    reason = None
    session = None
    argv = [str(BIN), "--standalone", "run", "--auto", "--agent", "nacho", "--format", "json"]
    if session_id:
        argv += ["--session", session_id]
    argv.append(prompt)
    with (
        (directory / "agente.stderr.log").open("a") as err,
        (directory / "eventos.jsonl").open("a", encoding="utf-8") as out,
    ):
        token = uuid.uuid4().hex
        process = subprocess.Popen(
            argv,
            cwd=worktree,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=err,
            start_new_session=True,
            env=dict(
                os.environ,
                PWD=str(worktree),
                OPENCODE_DISABLE_FREE_MODELS="1",
                KALI_AGENT_RUN_TOKEN=token,
                PATH=str(Path.home() / ".local/bin") + os.pathsep + os.environ.get("PATH", ""),
            ),
        )
        process._agent_run_token = token
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        pending = b""
        last_notice = start
        try:
            eof = False
            while not eof:
                now = time.monotonic()
                if now - start > seconds:
                    reason = "tiempo_maximo"
                    break
                if now - last_notice >= 15:
                    print(f"  Agente activo: {int(now - start)} s, {count} acciones.", flush=True)
                    last_notice = now
                for key, _ in selector.select(timeout=1):
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        eof = True
                        break
                    pending += chunk
                    while b"\n" in pending:
                        raw, pending = pending.split(b"\n", 1)
                        line = raw.decode("utf-8", errors="replace")
                        out.write(line + "\n")
                        out.flush()
                        try:
                            event = json.loads(line)
                        except ValueError:
                            continue
                        session = event.get("sessionID", session)
                        part = event.get("part", {})
                        if event.get("type") == "text":
                            print("\n" + part.get("text", ""), flush=True)
                        if event.get("type") == "error":
                            reason = "error_del_framework"
                        if event.get("type") != "tool_use":
                            continue
                        count += 1
                        state = part.get("state", {})
                        tool = part.get("tool", "?")
                        print(f"  Herramienta: {tool} [{state.get('status', '?')}]", flush=True)
                        metadata = state.get("metadata", {}).get("metadata", {})
                        failed = (
                            state.get("status") == "error"
                            or metadata.get("exit", 0) != 0
                            or metadata.get("error", False)
                        )
                        if failed:
                            signature = json.dumps([tool, state.get("input")], sort_keys=True)
                            failures[signature] = failures.get(signature, 0) + 1
                            if failures[signature] >= 3:
                                reason = "misma_accion_fallida_tres_veces"
                        if count >= max_actions:
                            reason = "limite_de_acciones"
                if reason:
                    break
            if reason:
                stop_process(process)
            code = process.wait(timeout=10)
            stop_process(process)
        except BaseException:
            stop_process(process)
            raise
        finally:
            selector.close()
            process.stdout.close()
    return {
        "codigo": code,
        "motivo_parada": reason,
        "acciones": count,
        "segundos": round(time.monotonic() - start, 2),
        "sesion": session,
    }


def snapshot_diff(worktree, base, directory):
    # Incluye cambios preparados, commits del agente y archivos nuevos sin preparar.
    patch = subprocess.run(
        ["git", "diff", "--no-ext-diff", "--no-textconv", base, "--binary"],
        cwd=worktree,
        capture_output=True,
        check=True,
    ).stdout
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=worktree,
        capture_output=True,
        check=True,
    ).stdout
    for raw in untracked.split(b"\0"):
        if raw:
            part = subprocess.run(
                [
                    "git",
                    "diff",
                    "--no-index",
                    "--no-ext-diff",
                    "--no-textconv",
                    "--binary",
                    "--",
                    "/dev/null",
                    os.fsdecode(raw),
                ],
                cwd=worktree,
                capture_output=True,
            )
            if part.returncode not in (0, 1):
                raise RuntimeError("No se pudo recoger el diff de un archivo nuevo")
            patch += part.stdout
    (directory / "cambios.patch").write_bytes(patch)
    return git(worktree, "status", "--short"), bool(patch)


def write_report(directory, report):
    save(directory / "informe.json", report)
    lines = [
        "# Informe de tarea",
        "",
        f"Estado: **{report['estado']}**",
        "",
        "Objetivo: " + report["objetivo"],
        "",
        "Proyecto original: " + report["original"],
        "Worktree: " + report["worktree"],
        "Rama: " + report["rama"],
        "Base: " + report["base"],
        "",
        "El proyecto original no recibe los cambios automaticamente. Un worktree separa el codigo; no aisla permisos, procesos ni red.",
        "",
        "## Comprobaciones del coordinador",
        "",
    ]
    for phase in ("antes", "despues"):
        for result in report.get(phase, []):
            ok = result["codigo"] == 0 and not result["timeout"]
            lines.append(
                f"- {phase}: {result['nombre']}: {'OK' if ok else 'FALLO'} ({result['segundos']} s). Log: {result['log']}"
            )
    lines += [
        "",
        "## Cambios",
        "",
        "```",
        report.get("archivos", ""),
        "```",
        "",
        "Diff completo: cambios.patch. Eventos: eventos.jsonl. Errores de OpenCode: agente.stderr.log.",
    ]
    if report.get("error"):
        lines += ["", "Error: " + report["error"]]
    if report.get("agente"):
        agent = report["agente"]
        lines += [
            "",
            "## Ejecucion del agente",
            "",
            f"Tiempo: {agent.get('segundos', '?')} s. Acciones: {agent.get('acciones', '?')}. Codigo: {agent.get('codigo', '?')}.",
            "Motivo de parada: " + str(agent.get("motivo_parada") or "terminacion normal"),
        ]
    if report.get("protegidos_modificados"):
        lines += [
            "",
            "Archivos protegidos modificados: " + ", ".join(report["protegidos_modificados"]),
            "Se requiere revision aunque las comprobaciones hayan pasado.",
        ]
    (directory / "INFORME.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def task(root, objective, seconds=1200, max_actions=60, warm=True):
    root = Path(git(root, "rev-parse", "--show-toplevel")).resolve()
    base = git(root, "rev-parse", "HEAD")
    if git(root, "status", "--porcelain"):
        raise RuntimeError(
            "El proyecto tiene cambios pendientes. Guarda un commit o gestionalos antes; no se hace stash ni se descarta trabajo automaticamente."
        )
    config = load_config(
        root
    )  # Capturado fuera del worktree: no se relee tras los cambios del agente.
    protected = protected_hashes(root, config)
    identifier = dt.datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    directory = STATE / "tareas" / identifier
    directory.mkdir(parents=True)
    worktree = directory / "proyecto"
    branch = "nacho/" + identifier
    git(root, "worktree", "add", "-b", branch, str(worktree), base)
    report = {
        "id": identifier,
        "objetivo": objective,
        "original": str(root),
        "worktree": str(worktree),
        "rama": branch,
        "base": base,
        "estado": "iniciando",
        "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
    }
    report["protegidos_originales"] = protected
    save(directory / "comprobaciones-originales.json", config)
    write_report(directory, report)
    print("Tarea:", identifier, "\nWorktree:", worktree, "\nRama:", branch, flush=True)
    try:
        report["antes"] = verify(worktree, config, directory, "antes")
        if warm:
            warm_model()
        commands = "- git diff HEAD --check\n" + "\n".join(
            "- " + shlex.join(x["argv"]) for x in config.get("checks", [])
        )
        failures = "\n".join(
            x["nombre"] + ":\n" + x["salida_final"][-1200:]
            for x in report["antes"]
            if x["codigo"] != 0
        )[:3600]
        files = "\n".join(git(worktree, "ls-files").splitlines()[:40])
        prompt = (
            objective + "\n\nDirectorio de trabajo: " + str(worktree) + ". "
            "Ejecuta las comprobaciones desde este directorio. Usa la ruta absoluta de scripts externos sin cambiar a su carpeta. "
            "No hagas commits, push, merges ni cambies de rama. "
            "Conserva pruebas y comprobaciones; no las debilites para ocultar errores. Sigue AGENTS.md. "
            "Empieza por los archivos relevantes ya identificados; evita busquedas globales redundantes. "
            "El coordinador ejecutara estas mismas comprobaciones originales independientemente al final. "
            "El formato Python se normaliza automaticamente; no reescribas la logica solo para quitar espacios. "
            "Corrige la causa y verifica. Resume cambios y resultados reales.\n\n"
            "Archivos iniciales (hasta 40):\n"
            + files
            + "\n\nComprobaciones originales:\n"
            + (commands or "(Sin comprobaciones configuradas)")
            + "\n\nFallos iniciales ya reproducidos por el coordinador:\n"
            + (failures or "(Ninguno)")
        )
        agent_start = time.monotonic()
        report["agente"] = stream_agent(worktree, prompt, directory, seconds, max_actions)
        report["intentos"] = [dict(report["agente"])]
        report["formato"] = format_candidate(worktree, config, directory, "despues", base)
        report["despues"] = verify(worktree, config, directory, "despues")
        bad = [x for x in report["despues"] if x["codigo"] != 0 or x["timeout"]]
        if report["formato"]["codigo"] != 0 or report["formato"]["timeout"]:
            bad.append(report["formato"])
        remaining = seconds - (time.monotonic() - agent_start)
        actions_left = max_actions - report["agente"].get("acciones", 0)
        if (
            bad
            and remaining >= 15
            and actions_left > 0
            and report["agente"].get("sesion")
            and report["agente"]["codigo"] == 0
            and not report["agente"]["motivo_parada"]
        ):
            print(
                "\nEl coordinador ha detectado fallos: se envia una ronda correctiva al mismo agente.",
                flush=True,
            )
            feedback = (
                "Las comprobaciones independientes aun fallan. Corrige los problemas siguientes en el worktree, "
                "conservando pruebas y configuracion. No hagas commits. Ejecuta de nuevo las comprobaciones y termina con un resumen breve.\n\n"
                + "\n\n".join(
                    x["nombre"]
                    + "\nComando: "
                    + x["comando"]
                    + "\nSalida:\n"
                    + x["salida_final"][-2000:]
                    for x in bad
                )[:6000]
            )
            previous = report["agente"]
            correction = stream_agent(
                worktree,
                feedback,
                directory,
                int(remaining),
                actions_left,
                session_id=previous["sesion"],
            )
            report["intentos"].append(dict(correction))
            report["verificacion_intermedia"] = report["despues"]
            report["formato"] = format_candidate(worktree, config, directory, "correccion", base)
            report["despues"] = verify(worktree, config, directory, "correccion")
            report["agente"] = dict(
                correction,
                acciones=previous.get("acciones", 0) + correction.get("acciones", 0),
                segundos=round(previous.get("segundos", 0) + correction.get("segundos", 0), 2),
            )
        passed = (
            all(x["codigo"] == 0 and not x["timeout"] for x in report["despues"])
            and report["formato"]["codigo"] == 0
            and not report["formato"]["timeout"]
        )
        completed = report["agente"]["codigo"] == 0 and not report["agente"]["motivo_parada"]
        report["estado"] = (
            "verificado"
            if passed and completed and config.get("checks")
            else ("sin_comprobaciones_de_proyecto" if passed and completed else "requiere_revision")
        )
    except KeyboardInterrupt:
        report["estado"], report["error"] = "interrumpido", "Interrumpido por el usuario"
    except Exception as exc:
        report["estado"], report["error"] = "error", str(exc)
    finally:
        try:
            current = protected_hashes(worktree, config, list(protected))
            report["protegidos_modificados"] = [
                p for p in protected if current.get(p) != protected[p]
            ]
            if report["protegidos_modificados"]:
                report["estado"] = "requiere_revision"
            report["archivos"], report["hay_cambios"] = snapshot_diff(worktree, base, directory)
            report["original_sigue_en_base"] = git(root, "rev-parse", "HEAD") == base
            report["estado_original"] = git(root, "status", "--porcelain")
            if not report["original_sigue_en_base"] or report["estado_original"]:
                report["estado"] = "original_modificado_revisar"
        except Exception as exc:
            report["estado"], report["error"] = "error_al_recoger_cambios", str(exc)
        write_report(directory, report)
    print(
        "\nEstado:",
        report["estado"],
        "\nInforme:",
        directory / "INFORME.md",
        "\nDiff:",
        directory / "cambios.patch",
        flush=True,
    )
    return report


def prepare(root):
    root = Path(git(root, "rev-parse", "--show-toplevel")).resolve()
    path = root / CONFIG
    if path.exists():
        raise RuntimeError(CONFIG + " ya existe; no se sobrescribe")
    checks = []
    package = root / "package.json"
    if package.exists():
        scripts = json.loads(package.read_text()).get("scripts", {})
        for name in ("test", "lint", "typecheck", "build"):
            if name in scripts:
                checks.append({"name": name, "argv": ["npm", "run", name], "timeout": 120})
    elif (root / "tests").is_dir() or list(root.glob("test_*.py")):
        checks.append({"name": "pytest", "argv": ["python3", "-m", "pytest", "-q"], "timeout": 90})
    save(
        path,
        {
            "checks": checks,
            "protected_files": [
                "AGENTS.md",
                "tests/**",
                "test_*.py",
                "**/test_*.py",
                "*.test.*",
                "*.spec.*",
            ],
        },
    )
    instructions = root / "AGENTS.md"
    if not instructions.exists():
        instructions.write_text(
            "# Trabajo en este proyecto\n\nInspecciona el codigo y reproduce el fallo antes de cambiarlo. Conserva el trabajo existente.\nUsa los comandos de .kali-agente.json para verificar. No modifiques las comprobaciones para esconder errores.\nNo publiques, hagas push ni cambies de rama durante una tarea.\nAl terminar informa de archivos cambiados, pruebas ejecutadas y limitaciones.\n",
            encoding="utf-8",
        )
    print(
        "Configuracion creada:",
        path,
        "\nRevisa los comandos, adapta AGENTS.md y guarda ambos en un commit antes de trabajar.",
    )
    if not checks:
        print("No se detectaron comprobaciones. Anade checks antes de pedir una tarea verificable.")


def resume(identifier, seconds=1200, max_actions=60, warm=True):
    if not identifier or any(c not in "0123456789abcdef-" for c in identifier):
        raise ValueError("Identificador de tarea no valido")
    directory = STATE / "tareas" / identifier
    report = json.loads((directory / "informe.json").read_text(encoding="utf-8"))
    worktree = (directory / "proyecto").resolve()
    root = Path(report["original"]).resolve()
    if worktree != Path(report["worktree"]).resolve() or not worktree.is_dir():
        raise RuntimeError("El worktree registrado no coincide o ya no existe")
    if git(root, "rev-parse", "HEAD") != report["base"] or git(root, "status", "--porcelain"):
        raise RuntimeError(
            "El proyecto original cambio desde la base; revisalo antes de retomar esta tarea"
        )
    config = json.loads((directory / "comprobaciones-originales.json").read_text(encoding="utf-8"))
    protected = report.get("protegidos_originales") or protected_hashes(root, config)
    report["protegidos_originales"] = protected
    previous = {key: report.get(key) for key in ("estado", "agente", "despues", "error")}
    previous["fecha"] = dt.datetime.now().astimezone().isoformat()
    report.setdefault("historial", []).append(previous)
    report.pop("error", None)
    phase = "retomar-" + uuid.uuid4().hex[:6]
    print("Retomando:", identifier, "\nWorktree:", worktree, flush=True)
    try:
        report["formato"] = format_candidate(
            worktree, config, directory, phase + "-antes", report["base"]
        )
        before = verify(worktree, config, directory, phase + "-antes")
        report["retomar_antes"] = before
        bad = [x for x in before if x["codigo"] != 0 or x["timeout"]]
        if warm:
            warm_model()
        prompt = (
            "Continuamos la tarea en el mismo worktree. Objetivo: "
            + report["objetivo"]
            + "\nNo hagas commits ni cambies pruebas o configuracion. Usa directamente las herramientas nativas. "
        )
        if bad:
            prompt += (
                "Corrige solo los fallos pendientes indicados abajo, ejecuta las comprobaciones y termina con un resumen de dos frases.\n"
                + "\n\n".join(
                    x["nombre"] + "\nComando: " + x["comando"] + "\n" + x["salida_final"][-1800:]
                    for x in bad
                )[:6000]
            )
        else:
            prompt += (
                "El coordinador acaba de comprobar que todas las pruebas y git diff HEAD --check pasan. "
                "La solucion esta implementada: no edites archivos ni ejecutes nuevas herramientas. "
                "Cierra con dos frases resumiendo el cambio y las comprobaciones que ya constan en la sesion."
            )
        session = (previous.get("agente") or {}).get("sesion")
        report["agente"] = stream_agent(
            worktree, prompt, directory, seconds, max_actions, session_id=session
        )
        if "intentos" not in report and previous.get("agente"):
            report["intentos"] = [previous["agente"]]
        report.setdefault("intentos", []).append(dict(report["agente"]))
        report["formato"] = format_candidate(
            worktree, config, directory, phase + "-despues", report["base"]
        )
        report["despues"] = verify(worktree, config, directory, phase + "-despues")
        passed = (
            all(x["codigo"] == 0 and not x["timeout"] for x in report["despues"])
            and report["formato"]["codigo"] == 0
            and not report["formato"]["timeout"]
        )
        normal = report["agente"]["codigo"] == 0 and not report["agente"]["motivo_parada"]
        report["estado"] = (
            "verificado" if passed and normal and config.get("checks") else "requiere_revision"
        )
    except KeyboardInterrupt:
        report["estado"], report["error"] = "interrumpido", "Interrumpido por el usuario"
    except Exception as exc:
        report["estado"], report["error"] = "error", str(exc)
    finally:
        try:
            current = protected_hashes(worktree, config, list(protected))
            report["protegidos_modificados"] = [
                p for p in protected if current.get(p) != protected[p]
            ]
            if report["protegidos_modificados"]:
                report["estado"] = "requiere_revision"
            report["archivos"], report["hay_cambios"] = snapshot_diff(
                worktree, report["base"], directory
            )
            report["original_sigue_en_base"] = git(root, "rev-parse", "HEAD") == report["base"]
            report["estado_original"] = git(root, "status", "--porcelain")
            if not report["original_sigue_en_base"] or report["estado_original"]:
                report["estado"] = "original_modificado_revisar"
        except Exception as exc:
            report["estado"], report["error"] = "error_al_recoger_cambios", str(exc)
        write_report(directory, report)
    print("Estado:", report["estado"], "\nInforme:", directory / "INFORME.md", flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("preparar")
    run = sub.add_parser("trabajar")
    run.add_argument("objetivo", nargs="+")
    run.add_argument("--segundos", type=int, default=1200)
    run.add_argument("--acciones", type=int, default=60)
    retry = sub.add_parser("retomar")
    retry.add_argument("id")
    retry.add_argument("--segundos", type=int, default=1200)
    retry.add_argument("--acciones", type=int, default=60)
    sub.add_parser("resultados")
    sub.add_parser("verificar")
    bench = sub.add_parser("banco")
    bench.add_argument(
        "--caso", choices=["todos", "python-error", "python-funcion", "web-api"], default="todos"
    )
    opts = parser.parse_args()
    if opts.command == "preparar":
        prepare(Path.cwd())
    elif opts.command == "trabajar":
        if not 30 <= opts.segundos <= 7200 or not 1 <= opts.acciones <= 200:
            raise ValueError("Limites validos: 30-7200 segundos, 1-200 acciones")
        result = task(Path.cwd(), " ".join(opts.objetivo), opts.segundos, opts.acciones)
        return 0 if result["estado"] == "verificado" else 1
    elif opts.command == "verificar":
        root = Path(git(Path.cwd(), "rev-parse", "--show-toplevel"))
        directory = (
            STATE
            / "verificaciones"
            / (dt.datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6])
        )
        config = load_config(root)
        result = verify(root, config, directory, "manual")
        save(directory / "resultados.json", result)
        print("Logs:", directory)
        return (
            0
            if config.get("checks") and all(x["codigo"] == 0 and not x["timeout"] for x in result)
            else 1
        )
    elif opts.command == "retomar":
        if not 30 <= opts.segundos <= 7200 or not 1 <= opts.acciones <= 200:
            raise ValueError("Limites validos: 30-7200 segundos, 1-200 acciones")
        result = resume(opts.id, opts.segundos, opts.acciones)
        return 0 if result["estado"] == "verificado" else 1
    elif opts.command == "resultados":
        for path in sorted((STATE / "tareas").glob("*/informe.json"), reverse=True)[:20]:
            item = json.loads(path.read_text())
            print(
                item["id"], item["estado"], item["objetivo"][:80], "\n ", path.parent / "INFORME.md"
            )
    elif opts.command == "banco":
        from .banco_agente import run_bank

        return run_bank(opts.caso)
    return 0
