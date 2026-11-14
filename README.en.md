<div align="center">

# Kali Agente · v0.3.0

### Your local model. Your terminal. Changes you can review.

<img src="assets/banner.gif" alt="Kali Agente v0.3.0 and the animated NACHO_WEB3 ASCII farmer robot" width="960" />

[![Version 0.3.0](https://img.shields.io/badge/VERSION-0.3.0-80e9ff?style=for-the-badge&labelColor=0c1626)](https://github.com/nachoweb3/kali-agente/releases/tag/v0.3.0)
[![CI](https://github.com/nachoweb3/kali-agente/actions/workflows/ci.yml/badge.svg)](https://github.com/nachoweb3/kali-agente/actions/workflows/ci.yml)
[![MIT](https://img.shields.io/badge/license-MIT-bd9bff)](LICENSE)

**A local coding agent by [nachoweb3](https://github.com/nachoweb3), built around OpenCode + Ollama.**

[Download v0.3.0](https://github.com/nachoweb3/kali-agente/releases/tag/v0.3.0) · [Full guide](docs/GUIDE.en.md) · [Español](README.md)

</div>

Turn a goal into file changes, real checks and a reviewable patch. Kali Agente coordinates Git worktrees, execution limits, independent verification, reports and confirmed integration around your chosen local model.

## See the workflow

<img src="assets/screenshots/tarea-verificada.png" alt="Controlled demo: an initial failing check becomes passing after a simulated agent edits a real Git worktree" width="1100" />

*Controlled agent fixture; Git and project checks run for real. This is captured coordinator output rendered as a terminal, not a real-model benchmark.*

<img src="assets/screenshots/revision-grafica.png" alt="Generated local HTML review showing passing checks, line numbers and a highlighted patch" width="1100" />

*Static render of the review HTML generated for the demo. No browser, JavaScript or external resources. [Image provenance and regeneration](docs/CAPTURAS.md).*

<img src="assets/screenshots/docker-real.png" alt="Real Docker checks for read-only mounts, disabled networking, explicit writes and timeout cleanup" width="1100" />

*Actual Docker integration check output, rendered as a terminal. No model inference is involved.*

## What's in v0.3.0

- Optional Docker environments for individual commands, without network or project writes by default.
- Six evaluation cases, repetitions and manifests recording model digest, versions, hardware, settings and source hashes.
- Balanced, deterministic and larger-context request profiles for an already installed model.
- Local HTML patch review and interactive confirmation before integration.
- Task archive/restore, allowlisted ZIP export and confirmed worktree cleanup with a patch backup.

Guided setup, progress monitoring and session continuation are also included. [Changelog](CHANGELOG.md).

## Install

Requires Linux or Windows through WSL2, Python 3.11+, Git, OpenCode and Ollama with an installed tool-capable model. Integration is tested with OpenCode 2.3.0. The installer does not download models.

```bash
git clone https://github.com/nachoweb3/kali-agente.git
cd kali-agente
bash scripts/install.sh
export PATH="$HOME/.local/bin:$PATH"
kali-agente iniciar
```

For CMD/PowerShell, extract the [Windows/WSL2 ZIP](https://github.com/nachoweb3/kali-agente/releases/download/v0.3.0/kali-agente-0.3.0-windows-wsl2.zip) and run `powershell -NoProfile -ExecutionPolicy Bypass -File .\windows\install.ps1`. See the [full guide](docs/GUIDE.en.md) for prerequisites and commands. The CLI currently defaults to Spanish.

## Evidence and scope

The v0.3.0 local validation passed 50 tests plus 9 fixture/validator subtests. CI covers Python 3.11–3.14, Windows script parsing and real Docker checks. [Actions](https://github.com/nachoweb3/kali-agente/actions/workflows/ci.yml) · [Validation](VALIDATION.md).

Actual model evaluations remain separate: the published CPU run verified 0/3 new cases within a 180-second budget per task. [Conditions and results](evaluations/README.md). Demo screenshots are not evidence of model capability.

Worktrees are not a sandbox. The optional `aislado` command contains only the command you explicitly run through it. Automatic modes have real account access, and containers share the kernel. Review [SECURITY.md](SECURITY.md).

---

**Created by [nachoweb3](https://github.com/nachoweb3)** · [MIT](LICENSE) · [Third-party licenses](THIRD_PARTY.md) · [Contribute](CONTRIBUTING.md) · [Issues](https://github.com/nachoweb3/kali-agente/issues)
