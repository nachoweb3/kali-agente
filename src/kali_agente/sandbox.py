"""Explicit, optional Docker environments for individual tool commands."""

import argparse
import os
from pathlib import Path
import subprocess
import uuid

from .settings import executable


def command(image, root, argv, name, writable=False, network=False, seconds=90):
    if not argv or image.startswith("-") or not image.strip():
        raise ValueError("Indica una imagen y un comando despues de --")
    root = Path(root).resolve()
    if not root.is_dir() or root == Path(root.anchor) or "," in str(root):
        raise ValueError("Elige una carpeta de proyecto concreta, sin comas en su ruta")
    mount = f"type=bind,src={root},dst=/workspace" + ("" if writable else ",readonly")
    return [
        executable("docker"),
        "run",
        "--rm",
        "--pull=never",
        "--name",
        name,
        "--init",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--network=" + ("bridge" if network else "none"),
        "--pids-limit=128",
        "--memory=512m",
        "--memory-swap=512m",
        "--cpus=1",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,noexec,size=64m,mode=1777",
        "--workdir",
        "/workspace",
        "--env",
        "HOME=/tmp",
        "--mount",
        mount,
        image,
        *argv,
    ]


def run(argv):
    parser = argparse.ArgumentParser(
        description="Ejecuta solo este comando en Docker; no aisla el agente completo"
    )
    parser.add_argument("--imagen", required=True)
    parser.add_argument("--carpeta", type=Path, default=Path.cwd())
    parser.add_argument("--escribir", action="store_true")
    parser.add_argument("--red", action="store_true")
    parser.add_argument("--segundos", type=int, default=90)
    parser.add_argument("comando", nargs=argparse.REMAINDER)
    opts = parser.parse_args(argv)
    if not 1 <= opts.segundos <= 3600:
        raise ValueError("Limite valido: 1..3600 segundos")
    args = opts.comando[1:] if opts.comando[:1] == ["--"] else opts.comando
    name = "kali-agente-" + uuid.uuid4().hex
    invocation = command(opts.imagen, opts.carpeta, args, name, opts.escribir, opts.red)
    # No implicit downloads, inherited secrets, Docker socket or home mounts.
    subprocess.run(
        [executable("docker"), "image", "inspect", opts.imagen],
        stdout=subprocess.DEVNULL,
        check=True,
        timeout=15,
    )
    process = None
    try:
        process = subprocess.Popen(invocation, stdin=subprocess.DEVNULL)
        try:
            return process.wait(timeout=opts.segundos)
        except subprocess.TimeoutExpired:
            print("Limite del contenedor alcanzado; eliminando su ejecucion.")
            return 124
    finally:
        try:
            subprocess.run(
                [executable("docker"), "rm", "--force", name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
            )
        finally:
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
