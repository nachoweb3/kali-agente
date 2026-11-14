# Copiloto de ciberseguridad y desarrollo · v0.4.0

La interfaz habitual es una unica conversacion: ejecuta `kali-agente` y escribe lo que necesitas con tus palabras. El modelo elige y combina capacidades en cada turno segun el contexto; no necesitas escribir IDs de skills, elegir categorias ni usar subcomandos para conversar. Puedes pegar una salida, pedir que lea un archivo, consultar una herramienta y despues encargar codigo en la misma sesion. Los comandos del manual son accesos opcionales para automatizacion y diagnostico. La seleccion depende del modelo y puede equivocarse; no garantiza comprension perfecta.


Combina dos capacidades: elegir y comprender herramientas de Kali y actuar sobre codigo, archivos y comandos cuando el usuario lo pide. Sigue usando OpenCode y tu modelo Ollama. No entrena el modelo ni garantiza que domine todas las herramientas.

## Arranque y herramientas

```bash
kali-agente iniciar
kali-agente
kali-agente herramientas listar
kali-agente herramientas listar --todas --buscar dns
kali-agente herramientas ayuda nmap --buscar=-sV
kali-agente copiloto --herramienta nmap "Explica -sV segun la ayuda; no ejecutes un escaneo"
```

Sin argumentos se abre el copiloto interactivo. `trabajar` conserva el agente de programacion `nacho` y sus worktrees/checks. Se conservan tambien `sesiones`, `continuar`, `plan` y `revision`.

El inventario recorre el PATH de Linux y directorios habituales y omite los montajes de Windows. Detectar un ejecutable no prueba que funcione. Hay recetas informativas para 20 herramientas conocidas: Nmap, TShark, tcpdump, Wireshark, curl, OpenSSL, Nikto, Gobuster, ffuf, sqlmap, Metasploit, John, Hydra, WhatWeb, SearchSploit, ss, ip, dig, Git y Python. Para otros comandos se consulta `man`, sin ejecutar el programa desconocido.

La ayuda tiene tiempo y tamano acotados. Subcomandos y herramientas sin manual pueden requerir documentacion oficial adicional. `--buscar` filtra la ayuda y no llama al modelo; resulta util para dudas sencillas. Las explicaciones del copiloto dependen de la velocidad y calidad de la inferencia.

## Dos terminales

En la terminal de la herramienta, registra un comando elegido por ti:

```bash
kali-agente registrar --salida captura.txt -- python3 -u mi_script.py
```

En la terminal del asistente:

```bash
kali-agente copiloto --salida captura.txt "Interpreta este error y propon el siguiente paso"
kali-agente copiloto --continuar --salida captura.txt "Esta es la salida actualizada"
```

El registro usa una pseudoterminal de `script` (util-linux), conserva el codigo de salida y crea un archivo privado sin sobrescribir archivos existentes. Limita el registro a 10 MB. El comportamiento de cada herramienta interactiva puede variar. La salida puede contener secretos: revisala antes de compartirla.

El copiloto lee una cola acotada del archivo indicado al enviar la pregunta. No vigila automaticamente otra terminal, no lee su historial ni recibe actualizaciones continuas. Vuelve a pasar `--salida` para compartir resultados nuevos. `--continuar` utiliza la ultima sesion de OpenCode del contexto actual; puedes consultar sesiones con `kali-agente sesiones`.

## Programar, compilar y desplegar

```bash
kali-agente copiloto "Implementa una CLI para analizar estos resultados, con argumentos y comprobaciones"
kali-agente copiloto "Inspecciona el proyecto y compila la aplicacion; corrige los errores reales"
```

El rol conserva las herramientas nativas para crear carpetas, escribir y modificar archivos y ejecutar comandos. Cuando se pide actuar, debe implementar y comprobar, no limitarse a un ejemplo. Para cambios coordinados puedes utilizar `preparar`, `trabajar`, `revisar` y `aplicar`.

Desplegar requiere un destino y accesos concretos: servidor/cuenta, configuracion, dependencias y procedimiento adecuado. El agente debe verificar el resultado y distinguir escrito, probado, compilado y desplegado. Anadir el rol no instala proveedores, no publica aplicaciones ni crea credenciales.

El modo habitual conserva las preguntas de permisos de OpenCode. `copiloto --auto OBJETIVO` aprueba las herramientas que OpenCode no deniegue; utilizalo cuando quieras delegar esa ejecucion. El shell sigue teniendo acceso real al sistema. `aislado` permanece disponible para comandos concretos.

## Skills que puede cargar el agente

```bash
kali-agente skills
kali-agente skills kali-herramientas
kali-agente copiloto --salida captura.txt "Usa @kali-interpretar-salida para explicar esta salida"
```

| Skill | Uso |
| --- | --- |
| `kali-herramientas` | Elegir herramientas y consultar opciones locales. |
| `kali-interpretar-salida` | Explicar errores y decidir una comprobacion siguiente. |
| `kali-desarrollar-utilidad` | Implementar scripts/aplicaciones, probar, compilar y preparar despliegues. |
| `kali-validar-hallazgo` | Separar indicios, falsos positivos y resultados comprobados. |
| `kali-informe-evidencias` | Conservar evidencias y redactar informes sin inventar resultados. |
| `kali-auditoria-web` | Entender HTTP/API, permisos y logica y verificar correcciones. |

Van dentro del paquete y se registran mediante la configuracion `skills` de OpenCode, con la ruta absoluta calculada en cada instalacion. No se copian a `~/.claude`, `~/.agents` ni a otros agentes. OpenCode anuncia nombres/descripciones y el modelo puede cargar el cuerpo con su herramienta `skill`; tambien puedes mencionar `@ID`. No se introduce toda la biblioteca en cada pregunta.

Hay cinco fichas compactas adicionales (`kali-agente guias`) seleccionadas por palabras del objetivo. Es una heuristica, no una clasificacion perfecta; `--guia NOMBRE` permite elegir otra.

Las fichas y skills son adaptaciones CC BY 4.0 de Claude-BugHunter, con fuentes, revision y cambios declarados. [Atribucion, extraccion y limites](CLAUDE-BUGHUNTER.md). La prueba con OpenCode real y servidor simulado comprueba descubrimiento y carga, no que el modelo elija siempre la skill correcta.

## Cuadernos locales

```bash
kali-agente cuaderno mi-lab --objetivo "Entender los errores de mi API" --alcance "Aplicacion local de pruebas"
kali-agente copiloto --cuaderno .kali-cuadernos/mi-lab "Ayudame con el siguiente paso"
```

Se crean `objetivo.json`, `notas.md`, `scripts/`, `evidencias/` e `informes/plantilla.md`, sin sobrescribir cuadernos existentes. El alcance escrito documenta el trabajo; no es una barrera tecnica para el shell. No se envia ni publica ningun informe automaticamente.
