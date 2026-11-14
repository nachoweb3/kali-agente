<div align="center">

<img src="assets/banner.gif" alt="NACHO_WEB3: un robot granjero ASCII cosecha codigo bajo un titulo de luz cian y violeta" width="960" />

# Kali Agente

### Tu modelo local. Un objetivo. Codigo que puedes comprobar.

**El agente de programacion local de nachoweb3: de la conversacion a los archivos, el shell y la verificacion.**

[![CI](https://github.com/nachoweb3/kali-agente/actions/workflows/ci.yml/badge.svg)](https://github.com/nachoweb3/kali-agente/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/nachoweb3/kali-agente)](https://github.com/nachoweb3/kali-agente/releases)
[![MIT](https://img.shields.io/badge/license-MIT-9de7ff)](LICENSE)
[![Linux + WSL2](https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20WSL2-8eabff)](#windows-cmd-y-powershell)

[Instalar](#instalacion-en-linux-o-kali) · [Windows](#windows-cmd-y-powershell) · [Como trabaja](#del-objetivo-al-parche) · [English](README.en.md) · [Releases](https://github.com/nachoweb3/kali-agente/releases)

</div>

Kali Agente conecta **OpenCode + Ollama** con un coordinador que crea tareas en worktrees de Git, ejecuta comprobaciones reales y entrega un informe con el parche. Puede inspeccionar proyectos, crear y editar archivos, ejecutar comandos y explicar lo que hace. Funciona con el modelo local que elijas, siempre que soporte herramientas y tu equipo pueda ejecutarlo.

Nacio para usar Qwen3-Coder abliterated desde Kali. Esta distribucion conserva el robot granjero animado, la identidad **NACHO_WEB3** y el flujo de trabajo, con configuracion portable e instaladores para compartirlo. **Es un framework alrededor de un modelo existente; no incluye pesos ni entrena un modelo nuevo.**

## Lo que puedes hacer

| Modo | Para que sirve |
| --- | --- |
| Interactivo | Trabajar con OpenCode, conversar sobre el proyecto y aprobar herramientas. |
| Tarea directa | Pedir una accion desde la terminal con `tarea`; `auto` aprueba permisos automaticamente. |
| Tarea coordinada | `trabajar` crea un worktree, conserva los checks originales, limita tiempo/acciones y verifica resultados. |
| Retomar | Continuar la misma tarea, worktree y sesion, conservando el historial. |
| Revision | Consultar el informe, los logs y `cambios.patch` antes de integrar. |
| Banco optativo | Tres ejercicios pequenos: corregir Python, implementar una funcion y arreglar una API HTTP. |

**Los worktrees separan cambios de Git, pero no son un sandbox.** El shell tiene acceso real a tu cuenta. `auto`, `trabajar`, `retomar` y `banco` aprueban herramientas automaticamente; utilizalos en entornos de confianza y revisa sus resultados. Consulta [el alcance de seguridad](SECURITY.md).

## Requisitos

- Linux, o Windows con **WSL2**. Python 3.11+, `venv`, `pip` y Git en Linux.
- **OpenCode 2.3.0** es la version de integracion probada. Versiones futuras pueden cambiar su CLI o configuracion; revisa la compatibilidad antes de actualizar.
- Ollama en funcionamiento y un modelo con soporte de herramientas ya instalado. El instalador no descarga modelos.
- Ruff es opcional para formatear Python; las herramientas y dependencias de cada proyecto se instalan por separado en Linux.

El modelo de ejemplo de 30B es grande. Comprueba su tamano, memoria necesaria y licencia antes de descargarlo. CPU/GPU y velocidad dependen de Ollama, del modelo y del equipo. No necesitas una API de pago para el flujo local.

## Instalacion en Linux o Kali

Instala Python, Git y el soporte de entornos virtuales con el gestor de tu distribucion. Instala [OpenCode](https://opencode.ai/docs/) y [Ollama](https://ollama.com/download) siguiendo sus instrucciones oficiales. Despues:

```bash
git clone https://github.com/nachoweb3/kali-agente.git
cd kali-agente
bash scripts/install.sh
export PATH="$HOME/.local/bin:$PATH"
kali-agente --help
```

La instalacion usa un entorno virtual propio en `~/.local/share/kali-agente/venv`. No necesita `sudo`. Para actualizar, descarga una release o ejecuta `git pull --ff-only` en este clon y repite el instalador.

Selecciona **un modelo que ya aparezca en `ollama list`**:

```bash
kali-agente configurar --modelo 'huihui_ai/qwen3-coder-abliterated:30b'
kali-agente estado
kali-agente
```

Si ya tienes un alias como `nacho-coder:latest`, utiliza ese nombre. Puedes usar otro modelo compatible. La calidad del razonamiento y de las llamadas a herramientas depende del modelo.

## Windows: CMD y PowerShell

Esta version incluye lanzadores de Windows. **El motor corre dentro de WSL2**, con acceso a carpetas de Windows montadas en Linux. No es una implementacion nativa de las herramientas Kali en Windows.

Instala una distribucion WSL2, Python, Git y OpenCode dentro de ella. El nombre predeterminado es `kali-linux`. Puedes escoger otra distribucion instalada con `KALI_AGENT_WSL_DISTRO`.

En PowerShell, desde el clon del proyecto:

```powershell
# Solo si tu distribucion tiene otro nombre:
# $env:KALI_AGENT_WSL_DISTRO = 'Ubuntu'
powershell -NoProfile -ExecutionPolicy Bypass -File .\windows\install.ps1
```

Abre una terminal nueva. Desde **PowerShell o CMD**:

```text
kali-agente --help
kali-agente configurar --modelo nacho-coder:latest
kali-agente estado
kali-agente tarea "Inspecciona este proyecto y explica como ejecutarlo"
```

El lanzador conserva la carpeta actual y devuelve el codigo de salida del agente. PowerShell puede exigir ejecutar `kali-agente.cmd` si su politica impide cargar scripts; no es necesario cambiar la politica global. Ollama puede ejecutarse en Windows si es accesible desde WSL2. Si `localhost` no conecta, configura la URL alcanzable desde Linux; el instalador no cambia firewall ni expone Ollama.

## Del objetivo al parche

Dentro de un repositorio Git existente con al menos un commit:

```bash
kali-agente preparar
# Revisa .kali-agente.json y AGENTS.md. Ajusta los checks a tu proyecto.
git add .kali-agente.json AGENTS.md
git commit -m "Configurar agente y comprobaciones"
kali-agente trabajar "Corrige el error del endpoint de usuarios" --segundos 1200 --acciones 60
kali-agente resultados
```

`preparar` detecta algunas estructuras Python y scripts npm. Revisa siempre lo generado: no determina por si solo si las pruebas cubren tu objetivo. Conserva un AGENTS.md existente.

1. Exige un repositorio limpio y captura su commit base, checks y archivos protegidos.
2. Crea una rama y un worktree propios. Ejecuta los checks iniciales para registrar el punto de partida.
3. Carga el modelo y ejecuta OpenCode con el objetivo, limites y contexto del proyecto.
4. Formatea Python modificado si Ruff esta disponible y ejecuta de nuevo los checks originales. Puede hacer una ronda correctiva con los errores reales.
5. Escribe un informe y un parche. No integra los cambios automaticamente en tu rama original.

Una tarea solo aparece como **verificada** si el agente termina normalmente, hay checks del proyecto, pasan las comprobaciones y no se detectan cambios en archivos protegidos o en el original. Esto verifica los checks configurados; no garantiza ausencia de defectos. La proteccion detecta cambios al finalizar, no bloquea escrituras.

```bash
kali-agente retomar ID_DE_TAREA --segundos 1200 --acciones 60
kali-agente verificar
```

Los informes muestran la ruta del worktree y de `cambios.patch`. Puedes revisar con `git diff` dentro del worktree o comprobar el parche con `git apply --check /ruta/cambios.patch`. Integra solo tras revisarlo. Los worktrees e informes se conservan hasta que los elimines manualmente con las herramientas de Git y del sistema.

Ejemplo de `.kali-agente.json` que debes versionar junto al proyecto:

```json
{
  "checks": [{"name": "tests", "argv": ["python3", "-m", "pytest", "-q"], "timeout": 90}],
  "protected_files": ["AGENTS.md", "tests/*", "test_*.py"],
  "format_python": true
}
```

## Configuracion y datos

```bash
kali-agente configurar --modelo 'tu-modelo:latest' --url http://127.0.0.1:11434 --contexto 16384 --salida 2048
kali-agente banner
kali-agente banner --estatico
kali-agente opencode --help
```

| Variable | Uso |
| --- | --- |
| `KALI_AGENT_MODEL` | Nombre del modelo Ollama; prevalece sobre el archivo. |
| `KALI_AGENT_OLLAMA_URL` | URL base de Ollama, sin `/v1`. |
| `KALI_AGENT_CONFIG_DIR` | Directorio propio de configuracion. |
| `KALI_AGENT_STATE_DIR` | Directorio de tareas, worktrees, eventos e informes. |
| `KALI_AGENT_OPENCODE_BIN` / `KALI_AGENT_RUFF_BIN` | Ruta del ejecutable si no esta en PATH. |
| `KALI_AGENT_WSL_DISTRO` | Distribucion usada por los lanzadores de Windows. |
| `KALI_AGENT_WSL_BIN` | Ruta Linux alternativa del agente para el lanzador de Windows. |
| `NO_COLOR` | Desactiva el color automatico del banner. |

Se respetan XDG_CONFIG_HOME y XDG_STATE_HOME. Por defecto se usan `~/.config/kali-agente/config.json` y `~/.local/state/kali-agente`. El perfil de OpenCode se pasa por entorno para cada invocacion; no reemplaza tu archivo global. OpenCode puede combinar configuraciones de proyecto, globales o administradas: revisalas si el comportamiento difiere.

Ollama sirve la inferencia local. La configuracion propia selecciona solo ese proveedor y desactiva compartir sesiones. Las herramientas pueden usar la red; no prometemos aislamiento ni funcionamiento completamente sin conexiones. No hay telemetria propia del coordinador. Los informes pueden contener datos privados: revisalos antes de compartir.

## Desarrollo y pruebas

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
ruff format --check src tests scripts
python -m build
python scripts/render_banner.py
```

Las pruebas de control usan repositorios temporales y un ejecutable simulado. Comprueban limites, limpieza de procesos descendientes, reanudacion, conservacion del original, parches y checks independientes. No necesitan descargar modelos ni conectarse a un proveedor.

Consulta [las verificaciones y limites de esta release](VALIDATION.md). El estado de Actions muestra los resultados de la matriz publicada.

El banco con modelo real es independiente y optativo: `kali-agente banco --caso todos`. Puede tardar decenas de minutos y consumir mucha memoria. Sus tres tareas no constituyen un ranking del modelo ni una promesa para proyectos reales.

## Hoja de ruta

- [x] Flujo local OpenCode + Ollama y comprobaciones independientes.
- [x] Worktrees, reanudacion, limites e informes con parches.
- [x] Banner ASCII animado en terminal y GIF de portada reproducible.
- [x] Instalacion en Linux y lanzadores Windows mediante WSL2.
- [ ] Entornos aislados opcionales para ejecutar herramientas.
- [ ] Mas casos de evaluacion y perfiles de modelos con resultados reproducibles.
- [ ] Revision visual de parches y gestion sencilla de tareas antiguas.

Creado por **[nachoweb3](https://github.com/nachoweb3)**. Codigo y arte propios bajo [MIT](LICENSE). Consulta [componentes y licencias externas](THIRD_PARTY.md), [contribuciones](CONTRIBUTING.md) y [changelog](CHANGELOG.md).
