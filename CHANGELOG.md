# Changelog

## 0.3.0

- Comandos aislados opcionales en Docker con limites, sin red ni escritura por defecto y sin descargas implicitas.
- Tres casos nuevos de evaluacion: varios archivos, JSONL y CLI. Repeticiones y manifiestos de modelo, versiones, hardware y hashes.
- Perfiles de peticion equilibrado, determinista y contexto-amplio, con temperatura y seed.
- Revision grafica HTML local, archivo/restauracion de tareas, exportacion ZIP y limpieza confirmada de worktrees con respaldo del parche.
- Pruebas de los limites del contenedor y CI Docker separada.

## 0.2.0

- Primer arranque guiado con comprobacion de Git, OpenCode y Ollama y seleccion de modelos ya instalados.
- Panel `tareas --seguir`, fases persistentes y avisos durante la carga del modelo.
- `revisar ID` muestra los checks y registra la huella del parche.
- `aplicar ID` vuelve a verificar los checks, protege el trabajo posterior y exige confirmacion interactiva. Prepara los cambios en Git sin crear commits.
- Pruebas de rechazo de parches modificados, proyectos originales cambiados, checks fallidos y confirmaciones no interactivas; prueba del flujo completo en una pseudoterminal.

## 0.1.0

Primera version publica: paquete Python instalable, modelo y servidor configurables, interfaz de terminal con robot granjero animado, tareas verificadas en worktrees, reanudacion de sesiones, informes y parches, banco optativo de tres tareas, lanzadores para CMD y PowerShell mediante WSL2 y CI para Linux.
