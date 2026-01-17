#!/usr/bin/env python3
"""
Quick test to verify PyTorch 2.6 compatibility patches are working
"""

import sys
import logging
import os
from pathlib import Path

# Load environment variables from .env
from dotenv import load_dotenv
dotenv_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 80)
print("TESTING PYTORCH 2.6 DIARIZATION COMPATIBILITY PATCHES")
print("=" * 80)

# Test 1: Check PyTorch version
print("\n1. Checking PyTorch version...")
import torch
print(f"   PyTorch version: {torch.__version__}")

# Test 2: Check if patches are applied
print("\n2. Testing torch.load patch...")
print(f"   torch.load function: {torch.load.__name__}")
print(f"   Is patched: {'_patched' in torch.load.__name__}")

# Test 3: Try importing diarization module (this applies all patches)
print("\n3. Importing diarization module (this will apply all patches)...")
try:
    from services.diarization import get_diarization_pipeline
    print("   ✅ Diarization module imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import: {e}")
    sys.exit(1)

# Test 4: Try to load the pipeline
print("\n4. Attempting to load diarization pipeline...")
print("   This will download the model if not cached (may take a while)...")
try:
    pipeline = get_diarization_pipeline()
    print("   ✅ Pipeline loaded successfully!")
    print(f"   Pipeline type: {type(pipeline)}")
except Exception as e:
    print(f"   ❌ Failed to load pipeline: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED - Diarization is working!")
print("=" * 80)
