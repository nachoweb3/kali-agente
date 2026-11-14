# Componentes y modelos

Kali Agente es una capa de coordinacion independiente creada por nachoweb3. No es un nuevo modelo fundacional ni una distribucion de Kali Linux.

- Nuestro codigo y arte ASCII: MIT, consulta LICENSE.
- OpenCode y Ollama: dependencias externas; conservan sus licencias y marcas. No se incluyen sus binarios.
- Qwen y las variantes abliterated: modelos externos con sus propias licencias y condiciones; revisa el repositorio concreto antes de descargarlos o redistribuirlos. No se incluyen pesos ni se modifican con este instalador.
- El generador del banner utiliza Pillow y una fuente monoespaciada instalada en el sistema. No se redistribuye el archivo de fuente.
- La galeria se genera con Pillow, WeasyPrint y PyMuPDF, dependencias opcionales que conservan sus propias licencias. No se incluyen sus librerias en el repositorio ni se necesitan para ejecutar el agente.

El proyecto no esta afiliado a Kali Linux, OpenCode, Ollama ni a los autores de los modelos.

Las fichas de `src/kali_agente/playbooks.json` y las skills de `src/kali_agente/skills/` son adaptaciones de Claude-BugHunter (Sachin Sharma / elementalsouls), bajo CC BY 4.0. Esa excepcion al contenido propio MIT y las modificaciones se detallan en [docs/CLAUDE-BUGHUNTER.md](docs/CLAUDE-BUGHUNTER.md). No se ha instalado ni redistribuido su motor, su coleccion completa de skills ni sus instaladores.
