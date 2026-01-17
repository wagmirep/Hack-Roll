# LoRA Fine-tuning for Singlish ASR - Research

**Researched:** 2026-01-17
**Domain:** LoRA fine-tuning for Speech Recognition (MERaLiON/Whisper-based ASR)
**Confidence:** HIGH

## Summary

Researched the PEFT/LoRA ecosystem for fine-tuning large ASR models like Whisper/MERaLiON on low-resource data. The standard approach uses HuggingFace PEFT with LoRA adapters targeting attention layers, combined with 8-bit quantization to fit on consumer GPUs.

Key finding: LoRA can achieve **comparable performance to full fine-tuning with only 1-5% of trainable parameters**. For Singlish word recognition, applying LoRA to attention projections (q_proj, v_proj) with rank 16-32 is the recommended starting point. Research shows WER improvements of 15-50% are achievable with properly tuned LoRA on domain-specific data.

**Primary recommendation:** Use PEFT + BitsAndBytes 8-bit quantization + Seq2SeqTrainer. Target q_proj and v_proj in both encoder and decoder. Start with r=32, alpha=64, lr=1e-4 for your ~1000 sample dataset.

---

## Standard Stack

### Core Libraries
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| peft | >=0.7.0 | LoRA adapter implementation | HuggingFace official, battle-tested |
| transformers | >=4.36.0 | Model loading, Seq2SeqTrainer | Required for Whisper/MERaLiON |
| bitsandbytes | >=0.41.0 | 8-bit quantization | Enables training on 16GB GPU |
| accelerate | >=0.25.0 | Mixed precision, distributed | Memory optimization |
| datasets | >=2.14.0 | Data loading and preprocessing | HuggingFace ecosystem |

### Supporting Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| librosa | >=0.10.0 | Audio preprocessing | Loading/resampling audio |
| soundfile | >=0.12.0 | Audio I/O | Writing processed audio |
| evaluate | >=0.4.0 | Metrics computation | WER calculation |
| jiwer | >=3.0.0 | Word Error Rate | ASR evaluation |

### Installation
```bash
pip install peft transformers bitsandbytes accelerate datasets librosa soundfile evaluate jiwer torch torchaudio
```

---

## LoRA Configuration

### Recommended Hyperparameters

| Parameter | Recommended | Range | Notes |
|-----------|-------------|-------|-------|
| **rank (r)** | 32 | 8-64 | r=32 found optimal for Whisper-small; higher ranks risk overfitting |
| **lora_alpha** | 64 | 2x rank | Scaling factor; 2x rank is standard practice |
| **lora_dropout** | 0.05 | 0.0-0.1 | Light regularization |
| **target_modules** | ["q_proj", "v_proj"] | See below | Minimum effective set |
| **bias** | "none" | "none", "all" | "none" is more stable |

### Target Module Options

**Minimal (recommended for small datasets):**
```python
target_modules = ["q_proj", "v_proj"]
# ~1% trainable params
```

**Comprehensive (for larger datasets):**
```python
target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "fc1", "fc2"]
# ~2-3% trainable params
```

**Decoder-only (preserves encoder knowledge):**
```python
# Filter to only decoder layers
target_modules = [name for name, _ in model.named_modules()
                  if 'model.decoder' in name and ('q_proj' in name or 'v_proj' in name)]
```

### LoRA Config Code
```python
from peft import LoraConfig, get_peft_model

lora_config = LoraConfig(
    r=32,
    lora_alpha=64,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="SEQ_2_SEQ_LM"  # For encoder-decoder ASR
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# Expected: ~1% trainable params
```

---

## Training Configuration

### Hyperparameters for ~1000 Samples

| Parameter | Value | Notes |
|-----------|-------|-------|
| **learning_rate** | 1e-4 | Higher than full fine-tuning (which uses 1e-5) |
| **epochs** | 3-5 | More epochs risk overfitting |
| **batch_size** | 4-8 | Limited by GPU memory |
| **gradient_accumulation** | 4 | Effective batch = 16-32 |
| **warmup_steps** | 50-100 | ~10% of total steps |
| **fp16** | True | Required for memory efficiency |
| **gradient_checkpointing** | True | Trades compute for memory |

### Training Arguments Code
```python
from transformers import Seq2SeqTrainingArguments

training_args = Seq2SeqTrainingArguments(
    output_dir="./checkpoints",
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=1e-4,
    num_train_epochs=3,
    warmup_steps=50,
    fp16=True,
    gradient_checkpointing=True,
    evaluation_strategy="steps",
    eval_steps=100,
    save_steps=100,
    logging_steps=25,
    load_best_model_at_end=True,
    metric_for_best_model="wer",
    greater_is_better=False,
    predict_with_generate=True,
    generation_max_length=225,
)
```

### 8-bit Quantization (for 16GB GPU)
```python
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_8bit=True,
)

model = WhisperForConditionalGeneration.from_pretrained(
    "MERaLiON/MERaLiON-2-10B-ASR",
    quantization_config=bnb_config,
    device_map="auto"
)
```

---

## Data Preprocessing

### Audio Requirements
- **Sample rate:** 16kHz (mandatory for Whisper/MERaLiON)
- **Format:** Mono WAV
- **Duration:** 1-30 seconds per sample
- **Quality:** Clear audio, minimal background noise

### Dataset Format
```python
# Expected structure
{
    "audio": {
        "array": np.ndarray,  # Audio waveform
        "sampling_rate": 16000
    },
    "transcript": "the text transcription"
}
```

### Preprocessing Function
```python
def prepare_dataset(batch, processor):
    audio = batch["audio"]

    # Compute log-Mel spectrogram
    batch["input_features"] = processor.feature_extractor(
        audio["array"],
        sampling_rate=audio["sampling_rate"]
    ).input_features[0]

    # Tokenize transcript
    batch["labels"] = processor.tokenizer(batch["transcript"]).input_ids

    return batch

# Apply to dataset
dataset = dataset.map(
    lambda x: prepare_dataset(x, processor),
    remove_columns=dataset.column_names,
    num_proc=4
)
```

### Data Collator
```python
from dataclasses import dataclass
from typing import Any, Dict, List, Union
import torch

@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    processor: Any

    def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]) -> Dict[str, torch.Tensor]:
        # Pad input features
        input_features = [{"input_features": f["input_features"]} for f in features]
        batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")

        # Pad labels
        label_features = [{"input_ids": f["labels"]} for f in features]
        labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")

        # Replace padding with -100 to ignore in loss
        labels = labels_batch["input_ids"].masked_fill(
            labels_batch.attention_mask.ne(1), -100
        )

        batch["labels"] = labels
        return batch
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LoRA implementation | Custom low-rank matrices | `peft` library | Edge cases, gradient handling, merge/unload |
| 8-bit quantization | Manual quantization | `bitsandbytes` | Complex CUDA kernels, memory management |
| Audio preprocessing | Manual spectrogram | `transformers` processor | Must match model's exact preprocessing |
| Training loop | Custom loop | `Seq2SeqTrainer` | Handles generate(), metrics, checkpointing |
| WER calculation | String matching | `jiwer` | Handles normalization, edge cases |

**Key insight:** The HuggingFace ecosystem has solved ASR fine-tuning with LoRA specifically. The PEFT Whisper example notebook is battle-tested on Colab T4 GPUs.

---

## Common Pitfalls

### Pitfall 1: Catastrophic Forgetting
**What goes wrong:** Model forgets base language capabilities after fine-tuning
**Why it happens:** LoRA updates can introduce "intruder dimensions" that overwrite learned features
**How to avoid:**
- Use lower rank (r=16-32 instead of 64+)
- Shorter training (3 epochs, not 10)
- Conservative learning rate (1e-4, not 1e-3)
- Consider decoder-only fine-tuning to preserve encoder
**Warning signs:** WER on general English suddenly increases

### Pitfall 2: Overfitting on Small Datasets
**What goes wrong:** Perfect training loss but poor eval/real-world performance
**Why it happens:** With ~1000 samples, 3+ epochs can memorize training data
**How to avoid:**
- Monitor eval loss closely
- Use early stopping (load_best_model_at_end=True)
- Apply dropout (lora_dropout=0.05)
- Consider data augmentation (speed perturbation, noise injection)
**Warning signs:** Training WER near 0 but eval WER not improving

### Pitfall 3: Wrong Learning Rate
**What goes wrong:** Training doesn't converge or diverges
**Why it happens:** LoRA needs different LR than full fine-tuning
**How to avoid:**
- LoRA: 1e-4 to 5e-4 (higher than full fine-tuning)
- Full fine-tuning: 1e-5 to 3e-5
- Use warmup (50-100 steps)
**Warning signs:** Loss spikes, NaN gradients, no improvement

### Pitfall 4: Memory OOM on Colab
**What goes wrong:** CUDA out of memory during training
**Why it happens:** 10B model + gradients + optimizer states exceed GPU RAM
**How to avoid:**
- Enable 8-bit quantization (`load_in_8bit=True`)
- Enable gradient checkpointing
- Reduce batch size, increase gradient accumulation
- Use `device_map="auto"` for model sharding
**Warning signs:** Training crashes after a few steps

### Pitfall 5: Mismatched Audio Format
**What goes wrong:** Model produces garbage output
**Why it happens:** Audio not at 16kHz or wrong preprocessing
**How to avoid:**
- Always resample to 16kHz: `Audio(sampling_rate=16000)`
- Use the model's processor for feature extraction
- Verify input_features shape matches expected
**Warning signs:** Completely wrong transcriptions

---

## Code Examples

### Complete Training Setup (Colab-Ready)
```python
# Source: HuggingFace PEFT examples + Whisper fine-tuning blog
import torch
from datasets import load_dataset, Audio
from transformers import (
    WhisperForConditionalGeneration,
    WhisperProcessor,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# 1. Load model with 8-bit quantization
bnb_config = BitsAndBytesConfig(load_in_8bit=True)
model = WhisperForConditionalGeneration.from_pretrained(
    "openai/whisper-large-v2",  # or MERaLiON
    quantization_config=bnb_config,
    device_map="auto"
)
processor = WhisperProcessor.from_pretrained("openai/whisper-large-v2")

# 2. Prepare for k-bit training
model = prepare_model_for_kbit_training(model)

# 3. Apply LoRA
lora_config = LoraConfig(
    r=32,
    lora_alpha=64,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none"
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# 4. Load and preprocess data
dataset = load_dataset("your_dataset")
dataset = dataset.cast_column("audio", Audio(sampling_rate=16000))

def prepare_dataset(batch):
    audio = batch["audio"]
    batch["input_features"] = processor.feature_extractor(
        audio["array"], sampling_rate=audio["sampling_rate"]
    ).input_features[0]
    batch["labels"] = processor.tokenizer(batch["transcript"]).input_ids
    return batch

dataset = dataset.map(prepare_dataset, remove_columns=dataset.column_names["train"])

# 5. Train
training_args = Seq2SeqTrainingArguments(
    output_dir="./whisper-lora",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=1e-4,
    num_train_epochs=3,
    fp16=True,
    gradient_checkpointing=True,
    evaluation_strategy="steps",
    eval_steps=100,
    save_steps=100,
    load_best_model_at_end=True,
    metric_for_best_model="wer",
    predict_with_generate=True,
)

trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["test"],
    data_collator=DataCollatorSpeechSeq2SeqWithPadding(processor),
)

trainer.train()
```

### Save and Load LoRA Adapter
```python
# Save adapter only (~50MB)
model.save_pretrained("./lora-adapter")

# Load for inference
from peft import PeftModel
base_model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-large-v2")
model = PeftModel.from_pretrained(base_model, "./lora-adapter")

# Or merge permanently (larger file, faster inference)
merged_model = model.merge_and_unload()
merged_model.save_pretrained("./merged-model")
```

---

## State of the Art (2024-2025)

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Full fine-tuning | LoRA + 8-bit quantization | 3x less VRAM, 10x smaller checkpoints |
| r=8 default | r=16-32 for ASR | Better accuracy on complex audio |
| Single language LoRA | LoRA Expert Fusion | 10-15% gains on multilingual |
| Manual early stopping | `load_best_model_at_end` | Automatic best checkpoint selection |

**New techniques to consider:**
- **O-LoRA:** Orthogonal gradient projection to reduce catastrophic forgetting
- **LoRA Expert Fusion:** Combine multiple language-specific adapters
- **QLoRA:** 4-bit quantization for even smaller memory footprint

**References:**
- [LoRA-Whisper: Parameter-Efficient Multilingual ASR](https://arxiv.org/html/2406.06619v1)
- [Towards Rehearsal-Free Multilingual ASR](https://arxiv.org/html/2408.10680v1)

---

## Data Requirements for Your Use Case

### For ~1000 Samples (Your Team Recordings)

| Metric | Expected |
|--------|----------|
| Trainable params | ~1% of model |
| Training time (A100) | 30-60 minutes |
| Training time (T4) | 2-3 hours |
| Expected WER improvement | 5-15% on target words |
| Checkpoint size | ~50-100MB |

### Recommendations
1. **Quality > Quantity:** 1000 high-quality, varied samples beats 5000 noisy ones
2. **Coverage matters:** Ensure each target word appears 30-50 times minimum
3. **Vary speakers:** 4 team members × 250 samples each = good speaker diversity
4. **Include context:** Words in sentences > isolated words
5. **Hold out 15%:** For honest evaluation

---

## Open Questions

1. **MERaLiON-specific LoRA settings**
   - What we know: MERaLiON is Whisper-based, so Whisper settings should work
   - What's unclear: Exact module names may differ from standard Whisper
   - Recommendation: Print `model.named_modules()` to verify target module names

2. **Optimal rank for Singlish particles**
   - What we know: r=16-32 works well for multilingual ASR
   - What's unclear: Whether Singlish particles need higher/lower rank
   - Recommendation: Start with r=32, experiment with r=16 and r=64

---

## Sources

### Primary (HIGH confidence)
- [HuggingFace PEFT Documentation](https://huggingface.co/docs/peft) - LoRA config, get_peft_model, merge
- [HuggingFace Transformers ASR Guide](https://huggingface.co/docs/transformers/tasks/asr) - Preprocessing, Seq2SeqTrainer
- [PEFT Whisper INT8 Training Notebook](https://github.com/huggingface/peft/blob/main/examples/int8_training/peft_bnb_whisper_large_v2_training.ipynb) - Complete Colab example

### Secondary (MEDIUM confidence)
- [Fine-Tune Whisper Blog](https://huggingface.co/blog/fine-tune-whisper) - Training hyperparameters, preprocessing
- [AWS LoRA Whisper Blog](https://aws.amazon.com/blogs/machine-learning/fine-tune-whisper-models-on-amazon-sagemaker-with-lora/) - Target modules, hyperparameters
- [LoRA-Whisper Paper](https://arxiv.org/html/2406.06619v1) - Research findings on r=32, multilingual

### Tertiary (verified via multiple sources)
- [Databricks LoRA Guide](https://www.databricks.com/blog/efficient-fine-tuning-lora-guide-llms) - Best practices, learning rates
- [LoRA Learns Less and Forgets Less](https://arxiv.org/html/2405.09673v2) - Catastrophic forgetting analysis

---

## Metadata

**Research scope:**
- Core technology: PEFT LoRA for ASR
- Ecosystem: transformers, bitsandbytes, accelerate
- Patterns: 8-bit quantization, Seq2SeqTrainer, data preprocessing
- Pitfalls: Catastrophic forgetting, overfitting, memory, learning rate

**Confidence breakdown:**
- Standard stack: HIGH - from Context7 + official docs
- LoRA config: HIGH - verified across multiple papers and examples
- Training config: HIGH - from official HuggingFace examples
- Pitfalls: HIGH - documented in research papers
- MERaLiON-specific: MEDIUM - extrapolated from Whisper

**Research date:** 2026-01-17
**Valid until:** 2026-02-17 (30 days - PEFT ecosystem relatively stable)

---

*Domain: LoRA Fine-tuning for Singlish ASR*
*Research completed: 2026-01-17*
*Ready for implementation: yes*
