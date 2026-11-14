---
name: kali-herramientas
description: Elegir y utilizar herramientas instaladas en Kali/Linux, explicar opciones, consultar ayuda local y diagnosticar comandos que fallan.
license: CC-BY-4.0
compatibility: OpenCode 2.3.0; Linux o WSL2
---

# Herramientas segun el objetivo

Usa esta skill cuando el usuario tenga una idea y necesite saber con que herramienta resolverla, cuando desconozca una opcion o cuando un comando no funcione.

1. Identifica el resultado deseado y los datos disponibles. No confundas aprender una herramienta con ejecutar una operacion contra un destino.
2. Consulta `kali-agente herramientas listar` para herramientas conocidas. Para otra herramienta, usa `kali-agente herramientas listar --todas --buscar NOMBRE`. Ese inventario no ejecuta los programas ni garantiza que funcionen.
3. Recupera `kali-agente herramientas ayuda NOMBRE`. Las recetas conocidas invocan ayuda informativa; para otras se consulta `man`. Si la ayuda esta incompleta, consulta el subcomando y la documentacion oficial pertinente. No inventes que una opcion existe.
4. Elige una o dos alternativas instaladas y explica por que encajan. Especifica los requisitos: permisos, interfaz, archivo, servicio o dependencias. Pide un dato solo si impide construir el comando correcto.
5. Propone el comando minimo que responda a una pregunta concreta. Explica argumentos, salida esperada y como interpretar un resultado negativo.
6. Si el usuario pide ejecucion, usa la herramienta del framework y comprueba la salida. Si pide una explicacion, no ejecutes trabajo adicional por iniciativa propia.
7. Ante un error, utiliza su mensaje para ajustar el siguiente paso. No repitas variantes al azar ni encadenes scanners sin relacion con el objetivo.

Entrega: herramienta elegida, comando contextualizado, explicacion y siguiente paso. Distingue presencia, ejecucion correcta y resultado util.

Adaptacion resumida y traducida de Claude-BugHunter, Sachin Sharma / elementalsouls: `bb-local-toolkit` y `bb-methodology`, revision 8ac4242ee0a108e65ac1343b56cce6c50ba456ef. CC BY 4.0: https://creativecommons.org/licenses/by/4.0/. Original: https://github.com/elementalsouls/Claude-BugHunter/tree/8ac4242ee0a108e65ac1343b56cce6c50ba456ef. Sin garantias; sin respaldo de los autores originales.
