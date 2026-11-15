"""Explicit offline QLoRA runner; heavy imports only after all preflight checks."""

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--chat-template", type=Path, required=True)
    parser.add_argument("--parameters-billions", type=float, default=30.5)
    parser.add_argument("--smoke-only", action="store_true")
    parser.add_argument("--run", action="store_true", help="Without this flag, preflight only")
    opts = parser.parse_args()
    if not 0 < opts.parameters_billions <= 1000:
        raise ValueError("Invalid parameter count")
    checkpoint = opts.checkpoint.resolve(strict=True)
    if not checkpoint.is_dir() or not (checkpoint / "config.json").is_file():
        raise ValueError("Use a local Transformers checkpoint, not an Ollama alias or GGUF")
    if not list(checkpoint.rglob("*.safetensors")):
        raise ValueError("Local safetensors weights required; nothing is downloaded automatically")
    if opts.output.exists():
        raise ValueError("Output must not exist; keep baseline and previous adapters intact")
    template = opts.chat_template.read_text(encoding="utf-8")
    if "{% generation %}" not in template:
        raise ValueError("Audited template with assistant generation masks is required")
    rows = {}
    for split in ("train", "dev"):
        rows[split] = [
            json.loads(line)
            for line in (opts.corpus / (split + ".jsonl")).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if not rows[split]:
            raise ValueError("Both train and dev must contain examples")
    for split, examples in rows.items():
        for row in examples:
            if row["split"] != split or not row.get("source"):
                raise ValueError("Missing provenance or incorrect split")
            if row["verification"]["after_exit"] != 0:
                raise ValueError("Unverified training trajectory")
    if {r["family"] for r in rows["train"]} & {r["family"] for r in rows["dev"]}:
        raise ValueError("Task families leak between train and dev")
    if not opts.smoke_only and len(rows["train"]) < 100:
        raise ValueError(
            "Seed corpus is for pipeline validation only; curate a larger corpus first"
        )
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.total,memory.free", "--format=csv,noheader,nounits"],
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )
    total, free = map(int, result.stdout.splitlines()[0].split(","))
    # Lower-bound screening, NOT an assurance that a given training recipe fits.
    minimum_mib = int(opts.parameters_billions * 1e9 * 0.5 / 2**20 + 4096)
    report = {
        "status": "preflight-only",
        "gpu_total_mib": total,
        "gpu_free_mib": free,
        "conservative_minimum_mib": minimum_mib,
        "fit_not_guaranteed": True,
        "train_examples": len(rows["train"]),
        "dev_examples": len(rows["dev"]),
        "smoke_only": opts.smoke_only,
    }
    print(json.dumps(report, indent=2))
    if free < minimum_mib:
        raise RuntimeError("Insufficient free GPU memory; no model was loaded or changed")
    if not opts.run:
        return

    import torch
    from datasets import Dataset
    from peft import LoraConfig, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable")
    tokenizer = AutoTokenizer.from_pretrained(
        checkpoint, local_files_only=True, trust_remote_code=False
    )
    tokenizer.chat_template = template
    for examples in rows.values():
        for row in examples:
            encoded = tokenizer.apply_chat_template(
                row["messages"],
                tools=row["tools"],
                tokenize=True,
                return_dict=True,
                return_assistant_tokens_mask=True,
            )
            if not any(encoded.get("assistant_masks", [])):
                raise ValueError("Template did not produce assistant token masks")
            if len(encoded["input_ids"]) > 2048:
                raise ValueError(
                    "Trajectory exceeds sequence length; do not silently truncate checks"
                )
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    model = AutoModelForCausalLM.from_pretrained(
        checkpoint,
        local_files_only=True,
        trust_remote_code=False,
        device_map={"": 0},
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=dtype,
        ),
    )
    model = prepare_model_for_kbit_training(model)
    model.config.use_cache = False
    config = SFTConfig(
        output_dir=str(opts.output),
        seed=42,
        data_seed=42,
        max_length=2048,
        packing=False,
        assistant_only_loss=True,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=2e-5,
        num_train_epochs=1,
        max_steps=2 if opts.smoke_only else -1,
        gradient_checkpointing=True,
        bf16=dtype == torch.bfloat16,
        fp16=dtype == torch.float16,
        logging_steps=1,
        save_strategy="epoch",
        eval_strategy="epoch",
        report_to="none",
        push_to_hub=False,
    )
    trainer = SFTTrainer(
        model=model,
        args=config,
        processing_class=tokenizer,
        train_dataset=Dataset.from_list(rows["train"]),
        eval_dataset=Dataset.from_list(rows["dev"]),
        peft_config=LoraConfig(
            r=16,
            lora_alpha=32,
            lora_dropout=0.05,
            target_modules=["q_proj", "v_proj"],
            task_type="CAUSAL_LM",
        ),
    )
    trainer.train()
    trainer.save_model()
    tokenizer.save_pretrained(opts.output)
    manifest = {
        "status": "smoke-adapter-not-quality-evaluated"
        if opts.smoke_only
        else "trained-not-quality-evaluated",
        "checkpoint_config_sha256": hashlib.sha256(
            (checkpoint / "config.json").read_bytes()
        ).hexdigest(),
        "template_sha256": hashlib.sha256(template.encode()).hexdigest(),
        "corpus_sha256": {
            split: hashlib.sha256((opts.corpus / (split + ".jsonl")).read_bytes()).hexdigest()
            for split in rows
        },
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("torch", "transformers", "trl", "peft", "datasets", "bitsandbytes")
        },
        "recipe": config.to_dict(),
        "quality_improvement_demonstrated": False,
    }
    (opts.output / "training-manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
