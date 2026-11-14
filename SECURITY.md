# Seguridad y alcance

El agente puede leer, modificar archivos y ejecutar comandos con los permisos de la cuenta que lo inicia. `auto`, `trabajar`, `retomar` y `banco` aprueban automaticamente herramientas que OpenCode no haya denegado. Usa estos modos en proyectos y entornos de confianza, preferiblemente en una VM o cuenta dedicada.

Los worktrees separan cambios de Git; no bloquean el acceso al resto del disco, la red o los procesos. La proteccion de pruebas detecta modificaciones al finalizar; no es un control de acceso. AGENTS.md, archivos del proyecto, servidores MCP y plugins pueden influir en el comportamiento. Revisa la configuracion efectiva de OpenCode.

`aislado` ejecuta solamente el comando indicado en un contenedor Docker. Sus opciones predeterminadas quitan red, escritura del proyecto, capacidades y nuevos privilegios y limitan recursos. `--escribir` y `--red` amplian ese acceso explicitamente. Confia en la imagen y en el daemon local: los contenedores comparten kernel, y acceso al daemon Docker es un privilegio importante. El agente y el resto de sus herramientas no quedan automaticamente dentro del contenedor. No se promete aislamiento frente a ataques al kernel o a Docker.

Las revisiones HTML escapan el contenido del parche, no incluyen scripts ni cargan recursos externos. Los ZIP de exportacion pueden contener rutas y objetivos privados. La limpieza de worktrees exige confirmacion, conserva un parche y la rama y rechaza archivos ignorados; revisa y exporta cualquier dato importante antes de descartar un candidato.

No ejecutes el agente como root. Revisa comandos, informes y parches. Utiliza herramientas de seguridad exclusivamente en sistemas propios o con autorizacion.

Los informes contienen rutas, objetivos, salidas de comandos y mensajes del modelo. Permanecen en el directorio de estado local salvo que tu los compartas. La configuracion propia desactiva compartir sesiones y selecciona Ollama; plugins, herramientas de red y configuraciones externas pueden realizar conexiones.

Para reportar una vulnerabilidad, utiliza la seccion Security del repositorio si dispone de reporte privado. No publiques credenciales, datos personales ni instrucciones contra servicios de terceros en un issue.
