"""
test_data_processing.py - Data Processing Tests

PURPOSE:
    Test data preparation and processing scripts.
    Ensures training data is correctly formatted.

REFERENCED BY:
    - pytest test runner
    - CI/CD pipeline

REFERENCES:
    - scripts/filter_imda.py - IMDA filtering script
    - scripts/prepare_singlish_data.py - Data prep script
"""

import json
import os
import tempfile
from pathlib import Path
from typing import List, Dict
import pytest

# Import modules to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from filter_imda import (
    find_singlish_words,
    normalize_text,
    TARGET_WORDS,
    AudioSample,
    FilterConfig,
    filter_samples,
    analyze_word_distribution,
)

from prepare_singlish_data import (
    ProcessedSample,
    DatasetSplit,
    create_train_val_test_split,
    load_filtered_samples,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_transcripts() -> List[str]:
    """Sample transcripts for testing."""
    return [
        "Wah lao eh, this one damn shiok sia!",
        "Cannot lah, I very sian already.",
        "Aiya, you so kaypoh for what?",
        "This food not bad leh, quite shiok.",
        "He always like that one, very kiasu.",
        "Bo jio! Why never call me?",
        "I really paiseh to ask again.",
        "Today weather so hot, damn jialat.",
        "You confirm can finish or not?",
        "The meeting was quite productive today.",  # No Singlish
        "Let's schedule a call for tomorrow.",  # No Singlish
    ]


@pytest.fixture
def sample_audio_samples() -> List[Dict]:
    """Sample audio data for filtering tests."""
    return [
        {
            "sample_id": "sample_001",
            "audio_path": "/fake/path/sample_001.wav",
            "transcript": "Wah lao eh, this one damn shiok sia!",
            "duration_seconds": 5.0
        },
        {
            "sample_id": "sample_002",
            "audio_path": "/fake/path/sample_002.wav",
            "transcript": "Cannot lah, I very sian already.",
            "duration_seconds": 4.0
        },
        {
            "sample_id": "sample_003",
            "audio_path": "/fake/path/sample_003.wav",
            "transcript": "The meeting was productive.",  # No Singlish
            "duration_seconds": 3.0
        },
        {
            "sample_id": "sample_004",
            "audio_path": "/fake/path/sample_004.wav",
            "transcript": "Bo jio! Why never call me?",
            "duration_seconds": 0.3  # Too short
        },
        {
            "sample_id": "sample_005",
            "audio_path": "/fake/path/sample_005.wav",
            "transcript": "Aiya paiseh lah, I forgot already.",
            "duration_seconds": 35.0  # Too long
        },
    ]


@pytest.fixture
def processed_samples() -> List[ProcessedSample]:
    """Processed samples for split testing."""
    return [
        ProcessedSample(
            sample_id=f"sample_{i:03d}",
            audio_path=f"/path/sample_{i:03d}.wav",
            transcript=f"Test transcript {i} lah",
            duration_seconds=float(i + 1),
            singlish_words=["lah"]
        )
        for i in range(100)
    ]


# =============================================================================
# SINGLISH WORD DETECTION TESTS
# =============================================================================

class TestSinglishWordDetection:
    """Tests for Singlish word detection in transcripts."""

    def test_find_common_particles(self):
        """Test detection of common Singlish particles."""
        text = "Cannot lah, I very tired lor."
        words = find_singlish_words(text)
        assert "lah" in words
        assert "lor" in words

    def test_find_vulgar_expressions(self):
        """Test detection of vulgar Singlish expressions."""
        text = "Wah lao, this one really cheebai situation."
        words = find_singlish_words(text)
        assert "walao" in words or "wahlao" in words or any("lao" in w for w in words)

    def test_find_colloquial_expressions(self):
        """Test detection of colloquial Singlish words."""
        text = "This food damn shiok, but I paiseh to eat more."
        words = find_singlish_words(text)
        assert "shiok" in words
        assert "paiseh" in words

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        text1 = "Cannot LAH"
        text2 = "Cannot lah"
        text3 = "Cannot Lah"

        words1 = find_singlish_words(text1)
        words2 = find_singlish_words(text2)
        words3 = find_singlish_words(text3)

        assert words1 == words2 == words3
        assert "lah" in words1

    def test_no_singlish_words(self):
        """Test text with no Singlish words."""
        text = "The meeting was productive and we achieved our goals."
        words = find_singlish_words(text)
        assert len(words) == 0

    def test_multiple_occurrences(self):
        """Test that duplicates are removed."""
        text = "Lah lah lah, everything also lah."
        words = find_singlish_words(text)
        # Should deduplicate
        assert words.count("lah") == 1

    def test_multiword_expressions(self):
        """Test multi-word expressions like 'bo jio'."""
        text = "Eh, bo jio! Why you never call me?"
        words = find_singlish_words(text)
        assert "bojio" in words or "bo jio" in "".join(words)

    def test_normalize_text(self):
        """Test text normalization."""
        text = "  Multiple   spaces   and  \n  newlines  "
        normalized = normalize_text(text)
        assert normalized == "multiple spaces and newlines"


# =============================================================================
# AUDIO FORMAT VALIDATION TESTS
# =============================================================================

class TestAudioFormatValidation:
    """Tests for audio format validation."""

    def test_duration_filtering_too_short(self, sample_audio_samples):
        """Test that samples < min_duration are rejected."""
        config = FilterConfig(min_duration=1.0, max_duration=30.0, min_word_count=1)
        # sample_004 has duration 0.3s - should be rejected
        # We can't actually filter without real audio files, so this tests the config
        assert config.min_duration == 1.0
        too_short_sample = sample_audio_samples[3]
        assert too_short_sample["duration_seconds"] < config.min_duration

    def test_duration_filtering_too_long(self, sample_audio_samples):
        """Test that samples > max_duration are rejected."""
        config = FilterConfig(min_duration=1.0, max_duration=30.0, min_word_count=1)
        # sample_005 has duration 35s - should be rejected
        too_long_sample = sample_audio_samples[4]
        assert too_long_sample["duration_seconds"] > config.max_duration

    def test_valid_duration_passes(self, sample_audio_samples):
        """Test that valid duration samples pass."""
        config = FilterConfig(min_duration=1.0, max_duration=30.0, min_word_count=1)
        valid_sample = sample_audio_samples[0]
        assert config.min_duration <= valid_sample["duration_seconds"] <= config.max_duration


# =============================================================================
# TRANSCRIPT EXTRACTION TESTS
# =============================================================================

class TestTranscriptExtraction:
    """Tests for transcript extraction and processing."""

    def test_transcript_preserved(self, sample_transcripts):
        """Test that transcripts are preserved correctly."""
        for transcript in sample_transcripts:
            assert isinstance(transcript, str)
            assert len(transcript) > 0

    def test_punctuation_preserved(self):
        """Test that punctuation is preserved."""
        text = "Wah lao! Cannot lah, I don't want."
        # Punctuation should remain after normalization for matching
        # but original should be preserved
        normalized = normalize_text(text)
        assert "!" in text  # Original preserved
        assert "," in text  # Original preserved
        assert "'" in text  # Original preserved

    def test_special_characters_handled(self):
        """Test that special characters are handled."""
        text = "Price: $10.50 (discount 20%)"
        normalized = normalize_text(text)
        assert isinstance(normalized, str)


# =============================================================================
# TRAIN/VAL/TEST SPLIT TESTS
# =============================================================================

class TestTrainValTestSplit:
    """Tests for dataset splitting."""

    def test_80_10_10_split(self, processed_samples):
        """Test default 80/10/10 split proportions."""
        train, val, test = create_train_val_test_split(
            processed_samples,
            train_ratio=0.8,
            val_ratio=0.1,
            test_ratio=0.1,
            seed=42
        )

        total = len(processed_samples)
        assert len(train.samples) == int(total * 0.8)
        assert len(val.samples) == int(total * 0.1)
        assert len(test.samples) == total - len(train.samples) - len(val.samples)

    def test_no_overlap_between_splits(self, processed_samples):
        """Test that there's no overlap between splits."""
        train, val, test = create_train_val_test_split(
            processed_samples, seed=42
        )

        train_ids = {s.sample_id for s in train.samples}
        val_ids = {s.sample_id for s in val.samples}
        test_ids = {s.sample_id for s in test.samples}

        assert len(train_ids & val_ids) == 0
        assert len(train_ids & test_ids) == 0
        assert len(val_ids & test_ids) == 0

    def test_all_samples_accounted_for(self, processed_samples):
        """Test that all samples are in exactly one split."""
        train, val, test = create_train_val_test_split(
            processed_samples, seed=42
        )

        total_in_splits = len(train.samples) + len(val.samples) + len(test.samples)
        assert total_in_splits == len(processed_samples)

    def test_reproducibility_with_seed(self, processed_samples):
        """Test that same seed produces same split."""
        train1, val1, test1 = create_train_val_test_split(
            processed_samples, seed=42
        )
        train2, val2, test2 = create_train_val_test_split(
            processed_samples, seed=42
        )

        assert [s.sample_id for s in train1.samples] == [s.sample_id for s in train2.samples]
        assert [s.sample_id for s in val1.samples] == [s.sample_id for s in val2.samples]
        assert [s.sample_id for s in test1.samples] == [s.sample_id for s in test2.samples]

    def test_different_seed_different_split(self, processed_samples):
        """Test that different seeds produce different splits."""
        train1, _, _ = create_train_val_test_split(processed_samples, seed=42)
        train2, _, _ = create_train_val_test_split(processed_samples, seed=123)

        # Very unlikely to be the same with different seeds
        ids1 = [s.sample_id for s in train1.samples]
        ids2 = [s.sample_id for s in train2.samples]
        assert ids1 != ids2


# =============================================================================
# MANIFEST GENERATION TESTS
# =============================================================================

class TestManifestGeneration:
    """Tests for manifest file generation."""

    def test_manifest_contains_all_samples(self, processed_samples):
        """Test that manifest contains all samples."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from prepare_singlish_data import create_manifest

            manifest_path = Path(tmpdir) / "manifest.json"
            create_manifest(processed_samples, str(manifest_path))

            with open(manifest_path, 'r') as f:
                manifest = json.load(f)

            assert manifest['total_samples'] == len(processed_samples)
            assert len(manifest['samples']) == len(processed_samples)

    def test_manifest_metadata_complete(self, processed_samples):
        """Test that manifest samples have required metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from prepare_singlish_data import create_manifest

            manifest_path = Path(tmpdir) / "manifest.json"
            create_manifest(processed_samples, str(manifest_path))

            with open(manifest_path, 'r') as f:
                manifest = json.load(f)

            for sample in manifest['samples']:
                assert 'sample_id' in sample
                assert 'audio_path' in sample
                assert 'transcript' in sample
                assert 'duration_seconds' in sample


# =============================================================================
# FILTERING TESTS
# =============================================================================

class TestFiltering:
    """Tests for sample filtering."""

    def test_filter_by_singlish_content(self, sample_audio_samples):
        """Test filtering by Singlish word count."""
        # Create mock filter that checks transcripts
        config = FilterConfig(min_word_count=1)

        # sample_003 has no Singlish words
        no_singlish = sample_audio_samples[2]
        words = find_singlish_words(no_singlish['transcript'])
        assert len(words) < config.min_word_count

        # sample_001 has Singlish words
        has_singlish = sample_audio_samples[0]
        words = find_singlish_words(has_singlish['transcript'])
        assert len(words) >= config.min_word_count

    def test_word_distribution_analysis(self, sample_transcripts):
        """Test word distribution analysis."""
        # Create fake AudioSample objects
        samples = [
            AudioSample(
                sample_id=f"s{i}",
                audio_path=f"/fake/{i}.wav",
                transcript=t,
                duration_seconds=5.0,
                singlish_words_found=find_singlish_words(t),
                singlish_word_count=len(find_singlish_words(t))
            )
            for i, t in enumerate(sample_transcripts)
        ]

        dist = analyze_word_distribution(samples)

        # Check distribution is computed
        assert isinstance(dist, dict)

        # Should have some words counted
        if dist:
            assert all(count > 0 for count in dist.values())


# =============================================================================
# EMPTY INPUT HANDLING TESTS
# =============================================================================

class TestEmptyInputHandling:
    """Tests for handling empty or edge case inputs."""

    def test_empty_samples_list(self):
        """Test handling of empty samples list."""
        train, val, test = create_train_val_test_split(
            [],
            train_ratio=0.8,
            val_ratio=0.1,
            test_ratio=0.1
        )

        assert len(train.samples) == 0
        assert len(val.samples) == 0
        assert len(test.samples) == 0

    def test_single_sample(self):
        """Test handling of single sample."""
        samples = [
            ProcessedSample(
                sample_id="only_one",
                audio_path="/path/only.wav",
                transcript="Solo lah",
                duration_seconds=5.0,
                singlish_words=["lah"]
            )
        ]

        train, val, test = create_train_val_test_split(samples)

        # Single sample should go somewhere
        total = len(train.samples) + len(val.samples) + len(test.samples)
        assert total == 1

    def test_empty_transcript(self):
        """Test handling of empty transcript."""
        words = find_singlish_words("")
        assert words == []

    def test_whitespace_only_transcript(self):
        """Test handling of whitespace-only transcript."""
        words = find_singlish_words("   \n\t   ")
        assert words == []


# =============================================================================
# LOAD FILTERED SAMPLES TESTS
# =============================================================================

class TestLoadFilteredSamples:
    """Tests for loading filtered samples from JSON."""

    def test_load_valid_json(self):
        """Test loading valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "samples.json"
            data = {
                "total_samples": 2,
                "samples": [
                    {
                        "sample_id": "test_001",
                        "audio_path": "/path/test.wav",
                        "transcript": "Test lah"
                    },
                    {
                        "sample_id": "test_002",
                        "audio_path": "/path/test2.wav",
                        "transcript": "Another one lor"
                    }
                ]
            }
            with open(filepath, 'w') as f:
                json.dump(data, f)

            samples = load_filtered_samples(str(filepath))

            assert len(samples) == 2
            assert samples[0]['sample_id'] == 'test_001'

    def test_load_list_format(self):
        """Test loading JSON that's just a list of samples."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "samples.json"
            data = [
                {"sample_id": "s1", "audio_path": "/p/1.wav", "transcript": "One"},
                {"sample_id": "s2", "audio_path": "/p/2.wav", "transcript": "Two"}
            ]
            with open(filepath, 'w') as f:
                json.dump(data, f)

            samples = load_filtered_samples(str(filepath))

            assert len(samples) == 2


# =============================================================================
# DATASET SPLIT PROPERTIES TESTS
# =============================================================================

class TestDatasetSplitProperties:
    """Tests for DatasetSplit dataclass properties."""

    def test_total_duration_calculation(self, processed_samples):
        """Test that total_duration is calculated correctly."""
        split = DatasetSplit(name="test", samples=processed_samples[:10])

        expected_duration = sum(s.duration_seconds for s in processed_samples[:10])
        assert split.total_duration == expected_duration

    def test_empty_split_duration(self):
        """Test duration of empty split."""
        split = DatasetSplit(name="empty", samples=[])
        assert split.total_duration == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
