# Arte y capturas de la portada

Las imagenes de la galeria corresponden a **Kali Agente v0.4.0**. No son capturas de una sesion de inferencia real presentada como un exito del modelo.

| Archivo | Procedencia |
| --- | --- |
| `assets/banner.gif` | Los mismos 28 fotogramas ASCII usados por el banner de terminal, con version de la release. |
| `assets/screenshots/tarea-verificada.png` | Salida capturada del coordinador sobre un repositorio temporal. El agente se sustituye por un fixture que corrige una suma; Git y los checks se ejecutan realmente. Se identifica como demo controlada en la imagen. |
| `assets/screenshots/revision-grafica.png` | HTML generado por `revisar --grafico` para esa demo, renderizado estaticamente con WeasyPrint y rasterizado. No es una captura de navegador. La tipografia y el tamano de pagina se adaptan al formato de la imagen. |
| `assets/screenshots/version-perfiles.png` | Salidas reales de `--version` y `perfiles`, renderizadas como una terminal con Pillow. |
| `assets/screenshots/docker-real.png` | Salida real de `scripts/check_sandbox.py`, ejecutado contra Docker con una imagen local ya instalada. |

Los identificadores aleatorios y las rutas temporales se sustituyen por valores de demostracion. No se publican sesiones personales, prompts privados, credenciales ni logs de otros proyectos. Los transcripts de las dos vistas de terminal y `provenance.json` permiten inspeccionar la procedencia.

## Regenerar

En Linux, con Git, fuentes DejaVu y Pango instalados:

```bash
python -m pip install -e '.[media]'
python scripts/render_banner.py
python scripts/render_readme_media.py
# Opcional: con Docker y python:3.13-alpine ya instalados:
python scripts/render_readme_media.py --docker
```

El script de la galeria utiliza repositorios temporales y un agente de prueba: no descarga modelos, no pide claves, no inicia un navegador ni ejecuta JavaScript. El render HTML bloquea la carga de recursos externos. Las dependencias de generacion son opcionales y no se necesitan para usar el agente.

Las capturas son una demostracion de interfaz y flujo. Los resultados del modelo real estan publicados por separado en [evaluations](../evaluations/README.md).

La captura `skills-copiloto.png` muestra la salida real de `kali-agente skills`, sin inferencia ni decisiones simuladas.
