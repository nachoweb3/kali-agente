# Ajuste de entrenamiento: laboratorio reproducible

Estado: **preparación experimental; ningún adaptador entrenado ni mejora de calidad demostrada**.

El objetivo es mejorar programación y uso de herramientas en el equipo del usuario. No se modifican los pesos activos, no se descarga otro modelo, no se contrata una GPU y no se publica un adaptador automáticamente. El modelo actual es una variante externa de Qwen; un cambio de prompt no es un fine-tuning.

## Lo que ya se puede ejecutar

```bash
# Solo biblioteca estándar. Directorio nuevo; no sobrescribe datos.
python training/prepare.py --output /tmp/kali-training-seed
```

Genera ocho trayectorias de entrenamiento y dos de desarrollo, separadas por familia. Cada ejemplo contiene lectura de archivo, observación de fallo, edición y comprobación. Las implementaciones y los checks se ejecutan realmente en directorios temporales, antes y después. El manifiesto registra hashes y procedencia MIT.

**Son diez ejemplos originales escritos a mano para verificar la canalización**, no respuestas de un modelo ni un corpus suficiente para mejorar un agente. No usamos los seis casos públicos del banco como ejemplos de entrenamiento. Las dos familias de desarrollo también son públicas: sirven para depurar, no como test final ciego.

## Receta QLoRA y requisitos

`train_lora.py` prepara una receta de adaptación de atención (`q_proj`, `v_proj`), rango 16, longitud 2048, una época y seed 42. No es un barrido de hiperparámetros ni una receta validada para este checkpoint concreto.

Requiere un entorno separado con PyTorch/CUDA, Transformers, TRL, PEFT, datasets y bitsandbytes compatibles entre sí. Sus versiones se guardan cuando se entrena. No se incluyen versiones fijadas como si ya se hubieran probado: **el entrenamiento no se ha ejecutado**.

Necesita:

- Un checkpoint local completo en formato Transformers/safetensors y su tokenizer, con procedencia, licencia y revisión exactas. Un alias de Ollama o su GGUF no sustituye ese checkpoint.
- Una plantilla de chat auditada para el modelo y sus herramientas, con bloques Jinja `{% generation %}`. El script comprueba que produce máscaras de tokens del asistente y rechaza ejemplos que excedan el contexto; no trunca comprobaciones silenciosamente.
- Un corpus revisado, sin secretos y con permiso de uso. Mínimo operativo de 100 ejemplos para salir del modo smoke; ese número es una barrera de uso, no garantía de calidad.
- Una GPU con memoria suficiente. El preflight calcula un límite conservador de pesos a 4 bits más 4 GiB de margen; superarlo **no garantiza** que quepan activaciones y entrenamiento. El modelo MoE de 30,5B conserva todos sus pesos aunque active menos parámetros por token.

Comando de preflight, sin entrenamiento ni descargas:

```bash
python training/train_lora.py \
  --checkpoint /ruta/checkpoint-local \
  --corpus /tmp/kali-training-seed \
  --chat-template /ruta/plantilla-auditada.jinja \
  --output /ruta/adaptador-nuevo \
  --smoke-only
```

Solo añadir `--run` carga el modelo y entrena. Con `--smoke-only` hace dos pasos y marca el adaptador como prueba de canalización, nunca como mejora. Para una corrida real se elimina ese flag, una vez revisados corpus y recursos. No se fusiona ni sustituye el modelo activo. La exportación, cuantización e integración con Ollama requieren validación aparte.

## Cómo demostrar una mejora

Antes de entrenar, congelar al menos 30 tareas de test nuevas, con repositorios y checks independientes. Deben incluir cambios en varios archivos, errores de ejecución, recuperación tras fallos de herramientas, compilación y conservación de trabajo existente. No incluir sus soluciones en entrenamiento ni usar el test para seleccionar hiperparámetros. Separar también los repositorios/familias entre train, desarrollo y test.

Registrar para base y candidato exactamente las mismas tareas, esquema de herramientas de despliegue, backend, hardware, presupuestos de tiempo/acciones/contexto/salida y seed. Conservar todos los fallos y timeouts. Para afirmar generalidad, repetir con varias seeds y tareas independientes y publicar intervalos y límites.

`compare.py` exige resultados pareados y metadatos compatibles. Su puerta de promoción exige al menos 30 tareas, ganancia absoluta de 10 puntos, prueba exacta pareada bilateral p < 0,05 y cero regresiones. Es una política del proyecto, no una demostración de pericia general ni una corrección por búsquedas repetidas. Los hashes permiten revisar artefactos; no certifican que un resultado sea auténtico.

```bash
python training/compare.py baseline.json candidate.json
```

Formato de cada resultado:

```json
{
  "model_digest": "hash-del-modelo-y-adaptador",
  "conditions": {
    "suite_sha256": "hash-suite",
    "runner_sha256": "hash-runner",
    "budget_seconds": 600,
    "action_limit": 40,
    "context": 16384,
    "output_tokens": 2048,
    "seed": 42,
    "backend": "version-exacta",
    "hardware": "configuracion-comparable",
    "deployment_schema_sha256": "hash-esquema-herramientas"
  },
  "tasks": [
    {"id": "test-001", "split": "test", "training_overlap": false,
     "passed": false, "seconds": 600, "verification_sha256": "hash-checks-y-resultado"}
  ]
}
```

Este JSON es una ilustración del esquema, **no una evaluación realizada**. El comparador no ejecuta un benchmark por sí mismo.

## Trabajo pendiente para un modelo utilizable

Ampliar el corpus con trayectorias verificadas de tareas reales y revisar el esquema de llamadas frente al OpenCode instalado. Congelar test y medir baseline. Seleccionar recursos, ejecutar smoke de GPU, entrenar y evaluar candidato sin cambiar presupuestos. Probar exportación y llamadas reales en el motor de destino. Publicar solo resultados medidos, incluidos los negativos. Si no mejora, conservar el baseline y revisar hipótesis; nunca entrenar contra el test hasta memorizarlo.

## Fuentes primarias consultadas

- [Qwen3-Coder: integración y formato de herramientas](https://github.com/QwenLM/Qwen3-Coder).
- [TRL SFTTrainer: conversaciones, herramientas y pérdida del asistente](https://huggingface.co/docs/trl/sft_trainer).
- [PEFT: entrenamiento cuantizado y QLoRA](https://huggingface.co/docs/peft/developer_guides/quantization).
- [SWE-bench: evaluación de agentes de programación](https://www.swebench.com/SWE-bench/guides/evaluation/).

Consulta de documentación: 15 de noviembre de 2026. No se atribuyen al proyecto resultados de otros modelos.
