---
name: kali-validar-hallazgo
description: Revisar un posible problema de seguridad, descartar falsos positivos y distinguir indicios, reproduccion e impacto demostrado.
license: CC-BY-4.0
compatibility: OpenCode 2.3.0
---

# Hallazgos con evidencia

Usa esta skill antes de concluir que una salida de scanner, una version, un error o un comportamiento inesperado constituyen una vulnerabilidad confirmada.

1. Registra la observacion exacta y el alcance de lo comprobado. Si falta informacion imprescindible del objetivo o del contexto de prueba, pide ese dato y conserva el resultado como candidato.
2. Describe requisitos y una reproduccion minima con cuentas y datos controlados. No es necesario extraer datos reales de otras personas para escribir un informe util.
3. Identifica una explicacion alternativa y una comprobacion que la descarte. Compara peticiones validas de referencia, roles y respuestas cuando sea pertinente.
4. No infieras orden de middleware a partir de una unica respuesta: parsing, sanitizacion y validacion pueden ejecutarse antes de autenticacion. Un banner de version tampoco demuestra que una configuracion sea explotable.
5. Separa observacion, causa probable e impacto demostrado. Si no has observado el impacto, explica la limitacion y evita asignar una gravedad como si estuviera probada.
6. Un fallo en una hipotesis no es un hallazgo. Documenta el falso positivo y el siguiente paso pertinente; no continues variaciones ilimitadas para intentar confirmar una idea inicial.
7. Para una correccion, reproduce el comportamiento en el codigo o laboratorio y verifica una regresion sobre el archivo real. No presentes resultados de otro proyecto o fixture como evidencia del objetivo actual.

Entrega: estado `candidato`, `no confirmado`, `falso positivo` o `confirmado`, con evidencias y limites. No envies informes automaticamente.

Adaptacion resumida de `triage-validation` de Claude-BugHunter, Sachin Sharma / elementalsouls, revision 8ac4242ee0a108e65ac1343b56cce6c50ba456ef. CC BY 4.0: https://creativecommons.org/licenses/by/4.0/. Fuente: https://github.com/elementalsouls/Claude-BugHunter/blob/8ac4242ee0a108e65ac1343b56cce6c50ba456ef/skills/triage-validation/SKILL.md. Sin garantias ni afiliacion.
