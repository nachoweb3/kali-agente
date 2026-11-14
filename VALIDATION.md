# Validacion

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
