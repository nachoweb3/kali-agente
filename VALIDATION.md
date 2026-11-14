# Validacion

## Presentacion del repositorio

La portada muestra la version 0.3.0, una galeria y enlaces al manual completo. Las vistas de terminal se generan a partir de salidas del programa; el flujo utiliza un agente simulado identificado como tal. La vista de revision es un render estatico del HTML generado por la herramienta, sin navegador, JavaScript ni recursos externos. Las cuatro imagenes y el banner actualizado se inspeccionaron visualmente. [Procedencia y regeneracion](docs/CAPTURAS.md).

## 0.3.0

- 50 pruebas locales aprobadas (y 9 subtests de fixtures/validadores) en Python 3.14 sobre Linux / WSL2.
- Docker real: proyecto y raiz de solo lectura, red deshabilitada, ausencia del socket y de una variable privada del host, escritura explicita y limpieza por timeout comprobados con `scripts/check_sandbox.py`.
- OpenCode 2.3.0 real conectado a un servidor local de prueba: se comprobo que su peticion transmite `temperature=0`, `seed=42` y `max_tokens=2048` con `scripts/check_profile_request.py`. No requiere un modelo real.
- Perfil validado contra el esquema oficial de OpenCode. Pruebas de contenido HTML escapado y CSP aprobadas; la apertura visual automatizada de archivos locales fue bloqueada por la politica del navegador y no se afirma una inspeccion visual de esa pagina.
- Revision HTML, perfiles, archivo/restauracion y exportacion incluidos en la prueba completa del paquete instalado. La limpieza conserva la rama y el parche y se prueba con cancelacion, cambios pendientes y archivos ignorados.
- Las evaluaciones reales se documentan por separado en `evaluations/`; sus resultados no se sustituyen por los de las pruebas unitarias.

## 0.2.0

- 37 pruebas locales aprobadas en Linux / WSL2, Python 3.14: incluye revision, integracion, confirmacion, cambios concurrentes del original, parches modificados y primer arranque.
- Ruff: formato y comprobaciones de nombres/importaciones aprobados.
- Flujo completo con fixtures de Ollama y OpenCode: asistente, tarea, panel, revision, rechazo de confirmacion por tuberia e integracion confirmada mediante pseudoterminal.
- Las pruebas automatizadas no descargan modelos ni necesitan una API de pago. Consulta Actions para la matriz de versiones y las pruebas del wheel instalado.

## 0.1.0

Comprobaciones locales realizadas antes de publicar:

- Linux / WSL2, Python 3.14: **20 pruebas automatizadas aprobadas**.
- Ruff: formato y deteccion de nombres/importaciones incorrectos aprobados.
- Construccion de sdist y wheel mediante PEP 517 aprobada.
- Wheel instalado en un entorno virtual nuevo y ejecutado fuera del codigo fuente: ayuda, configuracion, banner estatico y una tarea completa con fixtures de OpenCode/Ollama, worktree, checks y parche.
- Instalador Linux probado con HOME temporal: crea su entorno virtual y lanzador sin depender de la configuracion personal.
- Conexion del paquete instalado con Ollama y OpenCode 2.3.0: correcta. Peticion minima al modelo ya instalado: respondio `AGENTE_OK`.
- Lanzadores de Windows ejecutados desde PowerShell y CMD; version, carpeta actual y argumentos con espacios verificados. Comillas, signos de dolar y punto y coma comprobados en el lanzador PowerShell con un ejecutable de prueba.
- Banner GIF: 28 fotogramas generados desde las mismas funciones ASCII del programa; vista estatica inspeccionada.

La CI del repositorio ejecuta las pruebas en Python 3.11, 3.12, 3.13 y 3.14 sobre Ubuntu y comprueba la sintaxis PowerShell sobre Windows. Consulta su resultado real en Actions.

Limites: no se ha probado una instalacion completa de WSL2 en un Windows virgen. Los lanzadores dependen de una distribucion y herramientas Linux ya instaladas. La peticion minima al modelo no mide su calidad como programador; las pruebas normales usan fixtures, y el banco real de tres tareas es optativo. No se afirma soporte nativo del motor en Windows, aislamiento del shell ni rendimiento garantizado.
