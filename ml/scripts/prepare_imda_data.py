"""
prepare_imda_data.py - IMDA Dataset Preparation (Wrapper Script)

PURPOSE:
    Prepare and filter the IMDA National Speech Corpus for LoRA fine-tuning.
    Focuses on extracting Singlish-heavy samples for training.

NOTE: This is a convenience wrapper. The actual implementation is split into:
    - filter_imda.py - Filters IMDA corpus for Singlish-heavy samples
    - prepare_singlish_data.py - Prepares data for MERaLiON fine-tuning

USAGE:
    # Step 1: Filter IMDA corpus for Singlish samples
    python filter_imda.py --imda-path /path/to/imda --output ml/data/raw/filtered_samples.json

    # Step 2: Prepare training data
    python prepare_singlish_data.py --input ml/data/raw/filtered_samples.json --output ml/data/processed

    # Or use this wrapper script:
    python prepare_imda_data.py --imda-path /path/to/imda

REFERENCED BY:
    - train_lora.py - Loads processed data
    - ml/configs/training_config.yaml - Data paths

OUTPUT FORMAT:
    ml/data/processed/
    ├── manifest.json - List of all samples with metadata
    ├── audio/
    │   ├── sample_001.wav
    │   ├── sample_002.wav
    │   └── ...
    └── dataset/
        ├── train/
        ├── validation/
        └── test/

    ml/data/splits/
    ├── train.json - 80% of samples
    ├── val.json - 10% of samples
    └── test.json - 10% of samples

TARGET WORDS FOR FILTERING:
    ['walao', 'cheebai', 'lanjiao', 'lah', 'lor', 'sia', 'meh', 'can', 'paiseh', 'shiok', 'sian']
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description='Prepare IMDA corpus for MERaLiON fine-tuning (wrapper script)'
    )
    parser.add_argument(
        '--imda-path',
        type=str,
        required=True,
        help='Path to IMDA corpus directory'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='ml/data/processed',
        help='Output directory for processed data'
    )
    parser.add_argument(
        '--filtered-output',
        type=str,
        default='ml/data/raw/filtered_samples.json',
        help='Output path for filtered samples (intermediate step)'
    )
    parser.add_argument(
        '--min-word-count',
        type=int,
        default=1,
        help='Minimum Singlish words per sample'
    )
    parser.add_argument(
        '--skip-filter',
        action='store_true',
        help='Skip filtering step (use existing filtered_samples.json)'
    )
    parser.add_argument(
        '--skip-prepare',
        action='store_true',
        help='Skip preparation step (only run filtering)'
    )

    args = parser.parse_args()

    scripts_dir = Path(__file__).parent

    # Step 1: Filter IMDA corpus
    if not args.skip_filter:
        print("=" * 60)
        print("Step 1: Filtering IMDA corpus for Singlish samples...")
        print("=" * 60)

        filter_cmd = [
            sys.executable,
            str(scripts_dir / 'filter_imda.py'),
            '--imda-path', args.imda_path,
            '--output', args.filtered_output,
            '--min-word-count', str(args.min_word_count)
        ]

        result = subprocess.run(filter_cmd)
        if result.returncode != 0:
            print("Filtering failed!")
            sys.exit(1)

    # Step 2: Prepare training data
    if not args.skip_prepare:
        print("\n" + "=" * 60)
        print("Step 2: Preparing training data...")
        print("=" * 60)

        prepare_cmd = [
            sys.executable,
            str(scripts_dir / 'prepare_singlish_data.py'),
            '--input', args.filtered_output,
            '--output', args.output
        ]

        result = subprocess.run(prepare_cmd)
        if result.returncode != 0:
            print("Preparation failed!")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("IMDA data preparation complete!")
    print("=" * 60)
    print(f"Processed data: {args.output}")
    print(f"Split files: ml/data/splits/")


if __name__ == '__main__':
    main()
