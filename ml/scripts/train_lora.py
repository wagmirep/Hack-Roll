"""
train_lora.py - LoRA Fine-tuning Script

PURPOSE:
    Fine-tune MERaLiON-2-10B-ASR using LoRA adapters on Singlish data.
    Creates specialized adapters for better Singlish word recognition.

RESPONSIBILITIES:
    - Load base MERaLiON model
    - Apply LoRA configuration
    - Load prepared training data
    - Run training loop with logging
    - Save checkpoints periodically
    - Export final trained adapters

REFERENCED BY:
    - Training pipeline
    - CI/CD for model updates

REFERENCES:
    - ml/configs/lora_config.yaml - LoRA hyperparameters
    - ml/configs/training_config.yaml - Training settings
    - ml/data/splits/ - Training data
    - ml/checkpoints/ - Saved checkpoints
    - ml/outputs/ - Final adapters

LORA CONFIGURATION:
    - Rank (r): 16 (balance of performance vs efficiency)
    - Alpha: 32 (scaling factor)
    - Target modules: q_proj, v_proj (attention layers)
    - Dropout: 0.1
    - Bias: none

TRAINING CONFIGURATION:
    - Epochs: 3-5
    - Batch size: 4-8 (depending on GPU memory)
    - Learning rate: 1e-4
    - Warmup steps: 100
    - Max sequence length: 30s audio
    - Gradient accumulation: 4
    - FP16/BF16: enabled

CHECKPOINTING:
    - Save every 500 steps
    - Keep last 3 checkpoints
    - Save best model by validation loss

USAGE:
    python train_lora.py --config ml/configs/training_config.yaml
    python train_lora.py --resume ml/checkpoints/checkpoint-1000

EXPECTED RESULTS:
    - Training time: 3-4 hours on single GPU
    - Expected improvement: +5-10% accuracy on vulgar slang
    - Output: LoRA adapter weights (~50MB)
"""
