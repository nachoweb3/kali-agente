---
name: kali-desarrollar-utilidad
description: Crear scripts o aplicaciones, carpetas y archivos; modificar codigo, ejecutar pruebas, compilar y preparar o realizar un despliegue solicitado.
license: CC-BY-4.0
compatibility: OpenCode 2.3.0; herramientas de desarrollo instaladas en Linux
---

# De la idea a una utilidad ejecutable

Utiliza esta skill cuando el usuario pida implementar codigo o automatizar una tarea de herramientas, seguridad o cualquier otro proyecto de software.

1. Inspecciona los archivos pertinentes, lenguaje, dependencias y estado de Git. Conserva el trabajo existente. No hagas cambios de ramas, commits o publicaciones que no formen parte del objetivo.
2. Define entradas, salidas, parametros, codigos de salida y como comprobaremos el resultado. Para scripts de terminal incluye ayuda y errores comprensibles; evita credenciales incrustadas y rutas personales.
3. Crea o modifica los archivos reales usando herramientas de edicion. No sustituyas la implementacion por pseudocodigo, una copia en un archivo temporal o un mensaje de exito fijo.
4. Ejecuta las comprobaciones pertinentes sobre el codigo real. Si hay compilador o build, comprueba su resultado y el artefacto. No cambies pruebas solo para ocultar fallos.
5. Cuando proceda, usa el flujo `preparar` / `trabajar` / `revisar` / `aplicar` de Kali Agente. No exijas un worktree para responder una duda o para una tarea que no necesita ese flujo.
6. Si se pide desplegar, identifica destino, acceso disponible, configuracion, secretos de entorno, dependencias y forma de revertir. Usa el proveedor o procedimiento adecuado al proyecto. Verifica el servicio o artefacto resultante; no declares desplegado algo que solo se ha compilado.
7. Termina con archivos cambiados, comprobaciones ejecutadas, resultado y limitaciones. Distingue preparado, probado, compilado y desplegado.

Adaptacion orientada al desarrollo a partir de principios de `bb-local-toolkit` y `report-writing` de Claude-BugHunter, Sachin Sharma / elementalsouls, revision 8ac4242ee0a108e65ac1343b56cce6c50ba456ef; ampliada para nuestro coordinador. CC BY 4.0: https://creativecommons.org/licenses/by/4.0/. Fuente: https://github.com/elementalsouls/Claude-BugHunter/tree/8ac4242ee0a108e65ac1343b56cce6c50ba456ef. Sin garantias ni respaldo de los autores originales.
