# Evaluaciones reproducibles

El banco es una prueba pequena de integracion, no una clasificacion general ni una garantia de que un modelo programe correctamente proyectos reales.

Para registrar una ejecucion:

```bash
kali-agente perfiles determinista --modelo MODELO_YA_INSTALADO
kali-agente banco --caso todos --repeticiones 1 --segundos 300 --acciones 40
```

Conserva `manifest.json`, `resultados.json` y la version del codigo. Compara solo ejecuciones con los mismos casos, limites, parametros, contexto real del servidor y versiones compatibles. El hardware, la carga simultanea y las diferencias del backend pueden alterar resultados incluso con seed fija.

Los seis casos empiezan rotos; los tests del proyecto comprueban que los fixtures fallen y que soluciones de referencia independientes satisfagan los tres validadores nuevos. Las pruebas unitarias no miden la capacidad del modelo. Los resultados reales, cuando se incluyen aqui, se identifican como tales y se publican sin logs privados ni rutas de trabajo.

## Ejecucion real local: CPU, 180 segundos

[Resultado JSON y manifiestos](local-cpu-180s.json). Qwen3-Coder abliterated 30.5B Q4_K_M, perfil `determinista`, contexto de 16384, salida 2048, seed 42, 40 acciones y 180 segundos por tarea, una repeticion. El alias local `nacho-coder:latest` usa CPU (`num_gpu 0`). Se ejecutaron otras comprobaciones de desarrollo en paralelo: no es una comparacion controlada de velocidad.

| Caso | Verificado | Tiempo del agente | Resultado |
| --- | --- | --- | --- |
| multiarchivo | No | 180.07 s | Limite de tiempo; el calculo del IVA seguia siendo incorrecto. |
| jsonl | No | 181.27 s | Limite de tiempo; faltaba importar json en la implementacion. |
| cli | No | 180.82 s | Limite de tiempo; se registro --help dos veces en argparse. |

**Resultado estricto: 0/3.** Las tres pruebas iniciales reprodujeron el fallo conocido y los tres checks finales siguieron fallando. No se han convertido timeouts en aciertos ni se han contado recuperaciones posteriores. Esto demuestra que el coordinador detecta esos fallos; no demuestra que el modelo los resuelva con este presupuesto. La ligera superacion de 180 segundos incluye la parada y recogida del proceso.

Para repetir el escenario, instala primero el modelo base bajo su licencia, revisa los digests del manifiesto y crea el alias con `ollama create nacho-coder -f evaluations/Modelfile.cpu`. La configuracion del modelo observada tras la ejecucion se incluye en el JSON; temperatura y seed del perfil se envian como opciones de peticion. Ejecuta cada uno de los tres casos con `--segundos 180 --acciones 40 --repeticiones 1`. No se promete obtener el mismo tiempo o la misma salida.
