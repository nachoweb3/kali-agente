---
name: kali-auditoria-web
description: Entender aplicaciones HTTP/API, autenticacion y autorizacion, planificar comprobaciones concretas y corregir el codigo de una aplicacion.
license: CC-BY-4.0
compatibility: OpenCode 2.3.0; herramientas HTTP disponibles
---

# Aplicaciones web y APIs con contexto

1. Identifica la funcionalidad, el resultado esperado y que datos de prueba y acceso estan disponibles. Si faltan un destino o un archivo, no inventes uno.
2. Dibuja un recorrido minimo: peticion del cliente, parsing, autenticacion, autorizacion, logica y respuesta. No conviertas esta explicacion en un escaneo automatico de todo el entorno.
3. Comprueba herramientas locales antes de elegir cliente HTTP, proxy o scanner. Una peticion sencilla con una herramienta existente suele ser suficiente para aislar un problema.
4. Compara una peticion valida con la salida observada. Distingue conectividad, TLS, formato del cuerpo, permisos y estado del recurso. Un codigo HTTP aislado no prueba un fallo de seguridad.
5. Para revisar acceso a datos, usa identidades y datos de prueba controlados. Documenta el rol que envia la peticion y el comportamiento permitido; evita deducir impacto a partir de nombres de endpoints.
6. Si el objetivo es corregir codigo, implementa la validacion en la capa adecuada y verifica una prueba de regresion. No des por corregida una autorizacion porque se haya ocultado un boton en el cliente.
7. Ante un posible hallazgo, carga `kali-validar-hallazgo`. Para preparar resultados, carga `kali-informe-evidencias`. Selecciona lo pertinente sin cargar toda la biblioteca.

Entrega: recorrido observado, comando o cambio concreto, interpretacion y comprobacion siguiente.

Adaptacion de `bb-methodology` y `triage-validation` de Claude-BugHunter, Sachin Sharma / elementalsouls, revision 8ac4242ee0a108e65ac1343b56cce6c50ba456ef. CC BY 4.0: https://creativecommons.org/licenses/by/4.0/. Fuente: https://github.com/elementalsouls/Claude-BugHunter/tree/8ac4242ee0a108e65ac1343b56cce6c50ba456ef. Sin garantias ni afiliacion.
