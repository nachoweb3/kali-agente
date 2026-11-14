# Changelog

## Sin publicar como release adicional

- Interfaz conversacional unica: seleccion semantica de capacidades por turno, combinables, sin pedir IDs al usuario. Se elimina la ficha automatica fijada por palabras clave al arrancar; las referencias manuales quedan como opcion avanzada.

## 0.4.0

- Copiloto de ciberseguridad y programacion como modo principal, con permisos de OpenCode y continuidad de sesiones.
- Inventario de ejecutables locales y 20 recetas de ayuda sin destinos de red ni ejecucion automatica de herramientas desconocidas.
- Registro explicito de una terminal y consulta acotada de su salida; no observa otras terminales por su cuenta.
- Seis skills nativas bajo demanda y cinco fichas compactas; adaptaciones atribuidas de Claude-BugHunter bajo CC BY 4.0.
- Cuadernos locales exclusivos para objetivos, alcance, scripts, evidencias e informes.
- Pruebas de integracion de carga nativa de skills y documentacion de limites y rendimiento real.

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
