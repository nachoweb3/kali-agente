# Capacidades adaptadas de Claude-BugHunter

Referencia revisada: [elementalsouls/Claude-BugHunter](https://github.com/elementalsouls/Claude-BugHunter/tree/8ac4242ee0a108e65ac1343b56cce6c50ba456ef), revision `8ac4242ee0a108e65ac1343b56cce6c50ba456ef`.

Se ha tratado como material de referencia. No se han ejecutado sus instaladores, instalado su plugin, activado servicios MCP ni copiado su motor de escaneo. El copiloto sigue utilizando OpenCode y Ollama.

| Capacidad de referencia | Adaptacion en Kali Agente |
| --- | --- |
| Organizar una sesion alrededor de un objetivo y la evidencia disponible | Cuadernos locales y una ficha breve por objetivo. |
| Resolver las herramientas presentes antes de proponer mas instalaciones | Inventario del PATH de Linux y recuperacion acotada de ayuda local. |
| Separar indicios de hallazgos validados y contrastar explicaciones alternativas | Fichas `web-api` y `validacion`; sin convertir un banner o codigo HTTP en prueba de vulnerabilidad. |
| Conservar evidencia util y redactar resultados reproducibles | Ficha `evidencias`, registro optativo de salida de terminal y plantilla de informe. |
| Reservar el modelo para interpretar y decidir | Descubrimiento y lectura local deterministas; no cargar la coleccion completa de skills en cada pregunta. |

La ficha `codigo` combina estos principios con nuestro flujo de implementacion, pruebas, compilacion y preparacion de despliegues. Las fichas no convierten automaticamente el modelo en un experto ni trasladan los resultados de otros modelos a Qwen. Es necesario evaluar respuestas y ejecuciones.

## Atribucion y licencia del contenido

Las seis skills nativas de `src/kali_agente/skills/` tambien son adaptaciones bajo CC BY 4.0, con fuentes y cambios indicados en cada SKILL.md. Se empaquetan y registran con OpenCode para carga selectiva mediante la herramienta `skill`; no se instalan en otros agentes. El [manual del copiloto](COPILOTO.md) explica cada skill, sus comandos y el flujo de dos terminales.

La integracion se comprobo con OpenCode 2.3.0 real y un servidor local simulado: la skill aparece anunciada, se carga mediante `skill` y su contenido llega al siguiente turno. Esto verifica el harness; no demuestra mejora de razonamiento del modelo.

Claude-BugHunter, por **Sachin Sharma / elementalsouls**, distingue codigo MIT y documentacion/metodologia **CC BY 4.0** en su [NOTICE](https://github.com/elementalsouls/Claude-BugHunter/blob/8ac4242ee0a108e65ac1343b56cce6c50ba456ef/NOTICE).

Las adaptaciones de las fichas de `src/kali_agente/playbooks.json` se distribuyen bajo [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/). Se ha traducido, resumido, seleccionado y reformulado el contenido para este copiloto. Cada ficha identifica sus documentos de referencia. El contenido se proporciona sin garantias, segun la licencia original. No implica afiliacion ni respaldo de los autores originales.

Fuentes revisadas: `bb-methodology`, `bb-local-toolkit`, `triage-validation`, `evidence-hygiene`, `report-writing`, `engine/README.md` y `eval/README.md`. Nuestro codigo de integracion permanece bajo MIT; los pesos y componentes externos conservan sus licencias.
