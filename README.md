<div align="center">

# Kali Agente Â· v0.4.0

### Tu modelo local. Tu terminal. Cambios que puedes revisar.

<img src="assets/banner.gif" alt="Kali Agente v0.4.0: NACHO_WEB3 y su robot granjero ASCII animado, con luz cian y violeta" width="960" />

[![Version 0.4.0](https://img.shields.io/badge/VERSION-0.4.0-80e9ff?style=for-the-badge&labelColor=0c1626)](https://github.com/nachoweb3/kali-agente/releases/tag/v0.4.0)
[![CI](https://github.com/nachoweb3/kali-agente/actions/workflows/ci.yml/badge.svg)](https://github.com/nachoweb3/kali-agente/actions/workflows/ci.yml)
[![MIT](https://img.shields.io/badge/license-MIT-bd9bff)](LICENSE)
[![Linux and Windows WSL2](https://img.shields.io/badge/Linux%20%2B%20Windows-WSL2-6b9fff)](#instalacion)

**Un copiloto de ciberseguridad y programaciÃ³n local de [nachoweb3](https://github.com/nachoweb3), construido con OpenCode + Ollama.**

[Descargar v0.4.0](https://github.com/nachoweb3/kali-agente/releases/tag/v0.4.0) Â· [Capturas](#galeria) Â· [InstalaciÃ³n](#instalacion) Â· [GuÃ­a completa](docs/GUIA.es.md) Â· [English](README.en.md)

</div>

## Una conversaciÃ³n. Tu objetivo.

**Explica lo que necesitas con tus palabras.** El modelo interpreta cada peticiÃ³n en su contexto y elige los recursos pertinentes: herramientas, lectura de resultados, cÃ³digo o validaciÃ³n.

<img src="assets/story/conversation.gif" alt="IlustraciÃ³n animada: entender una peticiÃ³n, elegir recursos y actuar; el siguiente turno conserva el contexto" width="1100" />

*IlustraciÃ³n del flujo; no es una grabaciÃ³n del modelo ni representa tiempos reales.* [Alternativa estÃ¡tica](assets/story/conversation.png)

```bash
kali-agente
```

> Â«ExplÃ­came este errorÂ». Luego: Â«Lee este registroÂ». DespuÃ©s: Â«Crea un script para procesarlo y comprueba el resultadoÂ».

No necesitas elegir skills ni memorizar subcomandos. Puedes pegar salidas o indicar archivos dentro del chat. [CÃ³mo usar el copiloto â†’](docs/COPILOTO.md)

## Seis capacidades, una interfaz

<img src="assets/story/capabilities.png" alt="Seis recursos internos: herramientas, interpretaciÃ³n, desarrollo, validaciÃ³n, evidencias y web/API" width="1100" />

Las skills se cargan bajo demanda. El agente puede trabajar con archivos y shell mediante OpenCode y sus permisos; sus decisiones dependen de la capacidad del modelo. Compilar y desplegar requiere herramientas, destino y acceso disponibles.

<p align="center">
<strong>Ollama local</strong> Â· <strong>Kali / Linux / WSL2</strong> Â· <strong>CMD y PowerShell</strong> Â· <strong>Parches revisables</strong>
</p>

Kali Agente tambiÃ©n aÃ±ade **worktrees de Git, comprobaciones independientes, lÃ­mites de ejecuciÃ³n, informes y parches** alrededor de tu modelo local.

| Programar | Comprobar | Revisar |
| --- | --- | --- |
| Inspecciona el proyecto, crea archivos y ejecuta herramientas con OpenCode. | Conserva los checks originales y registra sus resultados antes y despuÃ©s. | Consulta el diff en terminal o HTML e integra con confirmaciÃ³n explÃ­cita. |

**VersiÃ³n actual: 0.4.0** Â· Linux y Windows mediante WSL2 Â· Modelo configurable Â· CÃ³digo propio bajo MIT.

<a id="galeria"></a>
## AsÃ­ se ve

<details>
<summary><strong>Ver el catÃ¡logo interno de skills</strong></summary>

<img src="assets/screenshots/skills-copiloto.png" alt="Catalogo real de las seis skills nativas del copiloto" width="1100" />

*Salida real del paquete; muestra el catalogo, sin simular respuestas del modelo.*

</details>

### Del fallo inicial al parche

<img src="assets/screenshots/tarea-verificada.png" alt="Demo controlada: el check de una suma falla al principio y pasa despuÃ©s; el coordinador conserva informe y parche" width="1100" />

*Salida del coordinador sobre un proyecto de demostraciÃ³n. El agente estÃ¡ simulado; Git y las comprobaciones se ejecutan realmente.*

### RevisiÃ³n grÃ¡fica antes de integrar

<img src="assets/screenshots/revision-grafica.png" alt="Vista HTML del parche: comprobaciones aprobadas, nÃºmeros de lÃ­nea y cambio de multiplicaciÃ³n a suma resaltado" width="1100" />

*HTML generado por la herramienta para la misma demo, renderizado estÃ¡ticamente. Muestra los checks y las lÃ­neas modificadas; la integraciÃ³n se confirma desde la terminal.*

<details>
<summary><strong>Ver aislamiento comprobado con Docker real</strong></summary>

<img src="assets/screenshots/docker-real.png" alt="Salida real de las comprobaciones Docker: solo lectura, sin red, sin secretos del host, escritura explicita y limpieza por timeout" width="1100" />

*Prueba real del contenedor con una imagen local. No utiliza un modelo simulado ni ejecuta inferencia.*

</details>

<details>
<summary><strong>Ver la versiÃ³n y los perfiles del modelo</strong></summary>

<img src="assets/screenshots/version-perfiles.png" alt="Salida real de Kali Agente 0.4.0 y sus perfiles equilibrado, determinista y contexto amplio" width="1100" />

*Salidas reales de `--version` y `perfiles`, renderizadas como terminal.*

</details>

[Procedencia y regeneraciÃ³n de las capturas](docs/CAPTURAS.md) Â· [Ejemplo HTML descargable](assets/revision-demo.html)


La interfaz habitual es una unica conversacion: ejecuta `kali-agente` y escribe lo que necesitas con tus palabras. El modelo elige y combina capacidades en cada turno segun el contexto; no necesitas escribir IDs de skills, elegir categorias ni usar subcomandos para conversar. Puedes pegar una salida, pedir que lea un archivo, consultar una herramienta y despues encargar codigo en la misma sesion. Los comandos del manual son accesos opcionales para automatizacion y diagnostico. La seleccion depende del modelo y puede equivocarse; no garantiza comprension perfecta.

## Lo nuevo en v0.4.0

El modo principal ahora es un **copiloto para Kali y desarrollo de software**. Consulta herramientas instaladas, incorpora su ayuda real y analiza las salidas que compartas. Puede trabajar con archivos y shell mediante OpenCode, con los permisos configurados.

<details>
<summary><strong>Accesos opcionales para automatizacion y diagnostico</strong></summary>

| Capacidad | Uso |
| --- | --- |
| Inventario local | `kali-agente herramientas listar --todas`; 20 recetas de ayuda conocidas y deteccion de otros ejecutables. |
| Consultas precisas | `kali-agente copiloto --herramienta nmap "Explica -sV usando la ayuda local"` |
| Otra terminal | `registrar --salida sesion.log -- comando argumentos`; despues `copiloto --salida sesion.log "Explica este resultado"`. |
| Seis skills nativas | Herramientas, interpretacion, desarrollo, validacion, evidencias e informes, auditoria web. OpenCode las carga bajo demanda. |
| Cuadernos locales | Objetivo, alcance, scripts, evidencias y plantilla de informe separados por trabajo. |
| Desarrollo completo | Crear y modificar codigo, comprobarlo y compilarlo; desplegar requiere destino y acceso disponibles. |

```bash
kali-agente skills
kali-agente skills kali-herramientas
kali-agente copiloto "Crea una utilidad Python para resumir mis registros y prueba su funcionamiento"
```

</details>

[Manual del copiloto y las seis skills](docs/COPILOTO.md) Â· [Que adaptamos de Claude-BugHunter, fuentes y licencias](docs/CLAUDE-BUGHUNTER.md)

Las skills y fichas adaptadas de Sachin Sharma / elementalsouls conservan **CC BY 4.0**; el codigo propio es MIT. No se instalan plugins ni motores externos. La integracion nativa se ha verificado con OpenCode real y un modelo simulado; eso no demuestra que cualquier modelo seleccione bien todas las skills. Una consulta real a Nmap con el modelo local tardo **117 segundos en CPU**. Las evaluaciones anteriores del modelo siguen siendo limitadas y no se convierten en resultados mejores por incorporar estas guias.

Conserva Docker opcional, seis casos de evaluacion, perfiles reproducibles, worktrees, revision HTML y gestion de tareas de v0.3.0. [Historial](CHANGELOG.md).

## CÃ³mo trabaja

<img src="assets/story/workflow.png" alt="ConversaciÃ³n con contexto y skills, o tarea con worktree, checks y revisiÃ³n de parche" width="1100" />

El chat es la entrada habitual. Para tareas con cambios separados en Git y comprobaciones independientes existe el flujo adicional de worktrees.

<details>
<summary><strong>Ver el diagrama tÃ©cnico y los comandos del flujo con worktree</strong></summary>

```mermaid
flowchart LR
    A[Objetivo] --> B[Worktree Git]
    B --> C[OpenCode + Ollama]
    C --> D[Checks originales]
    D --> E[Informe y parche]
    E --> F[RevisiÃ³n y confirmaciÃ³n]
```

```bash
kali-agente iniciar
kali-agente preparar
# Revisa y versiona la configuraciÃ³n del proyecto antes de trabajar.
kali-agente trabajar "Corrige el error del endpoint de usuarios"
kali-agente tareas --seguir
kali-agente revisar ID --grafico
kali-agente aplicar ID
```

`aplicar` requiere una terminal interactiva. Comprueba de nuevo el estado y los checks, prepara los cambios en Git y **no crea un commit**. [Flujo completo y requisitos â†’](docs/GUIA.es.md#del-objetivo-al-parche)

</details>

<a id="instalacion"></a>
## Empieza aquÃ­

Necesitas **Python 3.11+, Git, OpenCode y Ollama**, con un modelo compatible con herramientas ya instalado. La integraciÃ³n estÃ¡ probada con OpenCode 2.3.0. El instalador no descarga modelos.

**Linux / Kali / WSL2**

```bash
git clone https://github.com/nachoweb3/kali-agente.git
cd kali-agente
bash scripts/install.sh
export PATH="$HOME/.local/bin:$PATH"
kali-agente iniciar
```

**Windows Â· CMD y PowerShell**

Descarga y extrae el [ZIP de Windows / WSL2 v0.4.0](https://github.com/nachoweb3/kali-agente/releases/download/v0.4.0/kali-agente-0.4.0-windows-wsl2.zip). Desde la carpeta extraÃ­da:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\windows\install.ps1
```

El motor corre dentro de WSL2. La distribuciÃ³n predeterminada es `kali-linux`; puedes escoger otra instalada. [Preparar Windows y configurar Ollama â†’](docs/GUIA.es.md#windows-cmd-y-powershell)

## Evidencias y lÃ­mites

- **63 pruebas automÃ¡ticas**, mÃ¡s 9 subtests de fixtures y validadores, aprobadas en la validaciÃ³n local de v0.4.0.
- **CI para Python 3.11, 3.12, 3.13 y 3.14**, scripts de Windows y prueba real de Docker. [Consultar Actions](https://github.com/nachoweb3/kali-agente/actions/workflows/ci.yml).
- **Wheel instalado en un entorno independiente**, flujo de revisiÃ³n/integraciÃ³n y parÃ¡metros enviados por OpenCode comprobados. [Detalle de validaciÃ³n](VALIDATION.md).
- **EvaluaciÃ³n del modelo publicada por separado:** 0/3 casos nuevos verificados en la ejecuciÃ³n local de CPU con 180 segundos por tarea. No se confunde ese resultado con los tests del coordinador. [Condiciones y resultados](evaluations/README.md).

**Los worktrees separan cambios de Git; no aÃ­slan el shell.** El comando opcional `aislado` contiene solo la herramienta que ejecutes mediante Ã©l. Los modos automÃ¡ticos tienen acceso real a tu cuenta y los contenedores comparten kernel. Consulta [seguridad y alcance](SECURITY.md).

## DocumentaciÃ³n y comunidad

| Quieroâ€¦ | Ir aâ€¦ |
| --- | --- |
| Instalar, configurar modelos y aprender los comandos | [GuÃ­a completa en espaÃ±ol](docs/GUIA.es.md) |
| Read the installation and command guide in English | [English guide](docs/GUIDE.en.md) |
| Ver cÃ³mo se hicieron las imÃ¡genes | [Arte y capturas reproducibles](docs/CAPTURAS.md) |
| Repetir una evaluaciÃ³n | [Casos, manifiestos y resultados](evaluations/README.md) |
| Proponer una mejora o reportar un problema | [Issues](https://github.com/nachoweb3/kali-agente/issues) Â· [Discussions](https://github.com/nachoweb3/kali-agente/discussions) |
| Contribuir cÃ³digo | [CONTRIBUTING.md](CONTRIBUTING.md) |

---

<div align="center">

**Creado por [nachoweb3](https://github.com/nachoweb3)** Â· Cultivando ideas. Cosechando cÃ³digo.

[CÃ³digo y arte propios: MIT](LICENSE) Â· [Licencias de componentes externos](THIRD_PARTY.md) Â· [Descargas](https://github.com/nachoweb3/kali-agente/releases)

</div>
