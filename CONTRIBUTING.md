# Contribuir

Abre un issue con el comportamiento esperado, el resultado observado, sistema y versiones. Elimina secretos y datos personales de informes y eventos antes de adjuntarlos.

En Linux, crea un entorno virtual e instala `python -m pip install -e '.[dev]'`. Ejecuta `ruff format src tests scripts` y `python -m pytest -q`. Las pruebas normales usan ejecutables simulados y repositorios temporales: no necesitan modelos, cuentas ni GPU. El banco real es optativo y consume recursos.

Manten los checks originales como autoridad de verificacion. Un worktree no es un sandbox. No introduzcas instalaciones silenciosas de modelos, telemetria propia, secretos ni servicios de pago como requisito del funcionamiento local.
