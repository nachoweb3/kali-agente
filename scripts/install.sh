#!/usr/bin/env bash
set -euo pipefail
source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
install_dir="${KALI_AGENT_INSTALL_DIR:-$HOME/.local/share/kali-agente/venv}"
python3 -m venv "$install_dir"
"$install_dir/bin/python" -m pip install --upgrade "$source_dir"
mkdir -p "$HOME/.local/bin"
ln -sfn "$install_dir/bin/kali-agente" "$HOME/.local/bin/kali-agente"
printf '\nInstalado. Ejecuta: %s/.local/bin/kali-agente --help\n' "$HOME"
printf 'Si hace falta, anade $HOME/.local/bin a PATH. OpenCode, Git y Ollama se instalan por separado.\n'
