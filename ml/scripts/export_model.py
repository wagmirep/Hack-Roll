"""
export_model.py - Model Export Script

PURPOSE:
    Export trained LoRA adapters for production deployment.
    Prepares model for integration with backend.

RESPONSIBILITIES:
    - Load trained LoRA checkpoint
    - Merge LoRA weights with base model (optional)
    - Export in deployment-ready format
    - Generate model card with metadata
    - Validate exported model

REFERENCED BY:
    - Deployment pipeline
    - backend/services/transcription.py - Loads exported model

REFERENCES:
    - ml/checkpoints/ - Training checkpoints
    - ml/outputs/ - Export destination

EXPORT OPTIONS:
    1. LoRA adapters only (recommended for hackathon):
       - Small file size (~50MB)
       - Requires base model at inference
       - Easy to swap/update

    2. Merged model:
       - Larger file size (~20GB)
       - Self-contained
       - Slightly faster inference

    3. ONNX export:
       - Cross-platform compatibility
       - Optimized inference
       - More complex setup

OUTPUT STRUCTURE:
    ml/outputs/
    ├── lora_adapter/
    │   ├── adapter_config.json
    │   ├── adapter_model.bin
    │   └── README.md (model card)
    ├── merged_model/ (if merged)
    │   ├── config.json
    │   ├── pytorch_model.bin
    │   └── ...
    └── model_card.md

MODEL CARD INCLUDES:
    - Model name and version
    - Base model reference
    - Training data description
    - Performance metrics
    - Usage instructions
    - Limitations

USAGE:
    python export_model.py --checkpoint ml/checkpoints/best --output ml/outputs/lora_adapter
    python export_model.py --merge --checkpoint ml/checkpoints/best --output ml/outputs/merged
"""
