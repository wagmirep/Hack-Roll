"""
prepare_imda_data.py - IMDA Dataset Preparation

PURPOSE:
    Prepare and filter the IMDA National Speech Corpus for LoRA fine-tuning.
    Focuses on extracting Singlish-heavy samples for training.

RESPONSIBILITIES:
    - Download/load IMDA dataset
    - Filter for Singlish-heavy samples
    - Extract audio segments with transcriptions
    - Create train/validation/test splits
    - Save processed data in training-ready format

REFERENCED BY:
    - train_lora.py - Loads processed data
    - ml/configs/training_config.yaml - Data paths

REFERENCES:
    - ml/data/raw/ - Raw IMDA downloads
    - ml/data/processed/ - Filtered samples
    - ml/data/splits/ - Train/val/test splits

FILTERING CRITERIA:
    - Contains target Singlish words (walao, lah, lor, sia, etc.)
    - Clear audio quality (SNR > 15dB)
    - Single speaker per segment
    - Duration: 5-30 seconds
    - Language: English/Singlish (not Mandarin/Malay/Tamil only)

OUTPUT FORMAT:
    ml/data/processed/
    ├── manifest.json - List of all samples with metadata
    ├── audio/
    │   ├── sample_001.wav
    │   ├── sample_002.wav
    │   └── ...
    └── transcripts/
        ├── sample_001.txt
        ├── sample_002.txt
        └── ...

    ml/data/splits/
    ├── train.json - 80% of samples
    ├── val.json - 10% of samples
    └── test.json - 10% of samples

USAGE:
    python prepare_imda_data.py --input /path/to/imda --output ml/data/processed
    python prepare_imda_data.py --create-splits

TARGET WORDS FOR FILTERING:
    ['walao', 'cheebai', 'lanjiao', 'lah', 'lor', 'sia', 'meh', 'can', 'paiseh', 'shiok', 'sian']
"""
