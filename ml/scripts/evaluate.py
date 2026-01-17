"""
evaluate.py - Model Evaluation Script

PURPOSE:
    Evaluate ASR model performance on Singlish test set.
    Compare base model vs fine-tuned model accuracy.

RESPONSIBILITIES:
    - Load test dataset
    - Run inference with base model
    - Run inference with fine-tuned model (if available)
    - Calculate Word Error Rate (WER)
    - Calculate target word accuracy
    - Generate evaluation report

REFERENCED BY:
    - Training pipeline (post-training eval)
    - CI/CD for model validation

REFERENCES:
    - ml/data/splits/test.json - Test data
    - ml/outputs/ - Trained LoRA adapters
    - backend/services/transcription.py - Same corrections used

METRICS:
    - Word Error Rate (WER): Overall transcription accuracy
    - Target Word Accuracy: Accuracy on specific Singlish words
    - Per-word breakdown: Accuracy per target word
    - Confusion matrix: Common misrecognitions

EVALUATION PROCESS:
    1. Load test samples
    2. Transcribe with base model
    3. Apply post-processing corrections
    4. Transcribe with fine-tuned model (if available)
    5. Apply post-processing corrections
    6. Compare against ground truth
    7. Calculate metrics
    8. Generate report

OUTPUT:
    ml/outputs/evaluation_report.json
    {
        "base_model": {
            "wer": 0.15,
            "target_word_accuracy": 0.85,
            "per_word": {"walao": 0.82, "lah": 0.95, ...}
        },
        "finetuned_model": {
            "wer": 0.10,
            "target_word_accuracy": 0.92,
            "per_word": {"walao": 0.91, "lah": 0.97, ...}
        },
        "improvement": {
            "wer": 0.05,
            "target_word_accuracy": 0.07
        }
    }

USAGE:
    python evaluate.py --test-set ml/data/splits/test.json
    python evaluate.py --model ml/outputs/lora_adapter --compare-base
"""
