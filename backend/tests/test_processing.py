"""
tests/test_processing.py - Audio Processing Pipeline Tests

Tests the processing pipeline with mocked services to verify the flow works
without requiring actual ML models or audio files.
"""

import os
import sys
import uuid
import pytest
import tempfile
from unittest.mock import MagicMock, AsyncMock, patch
from decimal import Decimal

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTranscriptionFlow:
    """Test transcription and word counting flow (no database)."""

    def test_apply_corrections_basic(self):
        """Test that corrections are applied to known misrecognitions."""
        from services.transcription import apply_corrections

        # Test known corrections
        assert "walao" in apply_corrections("while up").lower()
        assert "walao" in apply_corrections("wa lao").lower()
        assert "lah" in apply_corrections("Just do it la").lower()

    def test_count_target_words(self):
        """Test word counting on known text."""
        from services.transcription import count_target_words

        text = "Wah this one damn shiok lah! Cannot lor, very jialat sia."
        counts = count_target_words(text)

        assert counts.get("wah", 0) >= 1
        assert counts.get("shiok", 0) >= 1
        assert counts.get("lah", 0) >= 1
        assert counts.get("cannot", 0) >= 1
        assert counts.get("lor", 0) >= 1
        assert counts.get("jialat", 0) >= 1
        assert counts.get("sia", 0) >= 1

    def test_count_target_words_case_insensitive(self):
        """Test that counting is case insensitive."""
        from services.transcription import count_target_words

        text = "WAH shiok SHIOK Shiok"
        counts = count_target_words(text)

        assert counts.get("wah", 0) >= 1
        assert counts.get("shiok", 0) >= 3

    def test_process_transcription_combined(self):
        """Test combined correction and counting."""
        from services.transcription import process_transcription

        # Text with misrecognitions
        text = "while up eh the traffic today really jialat"
        corrected, counts = process_transcription(text)

        # Should correct "while up" to "walao"
        assert "walao" in corrected.lower()
        assert counts.get("walao", 0) >= 1
        assert counts.get("jialat", 0) >= 1


class TestDiarizationIntegration:
    """Test diarization service integration."""

    def test_speaker_segment_dataclass(self):
        """Test SpeakerSegment creation."""
        from services.diarization import SpeakerSegment

        segment = SpeakerSegment(
            speaker_id="SPEAKER_00",
            start_time=0.0,
            end_time=5.0,
            duration=5.0,
        )

        assert segment.speaker_id == "SPEAKER_00"
        assert segment.start_time == 0.0
        assert segment.end_time == 5.0
        assert segment.duration == 5.0


class TestProcessorHelpers:
    """Test processor helper functions."""

    def test_progress_calculation(self):
        """Test progress stage calculations."""
        from processor import PROGRESS_STAGES

        # Verify stage weights add up correctly
        assert PROGRESS_STAGES["concatenating"] == (0, 10)
        assert PROGRESS_STAGES["diarizing"] == (10, 40)
        assert PROGRESS_STAGES["transcribing"] == (40, 85)
        assert PROGRESS_STAGES["saving_results"] == (85, 95)
        assert PROGRESS_STAGES["generating_samples"] == (95, 100)


class TestProcessorPipelineFlow:
    """Test the pipeline flow with mocked services."""

    @pytest.fixture
    def mock_all_services(self):
        """Mock all external services for pipeline testing."""
        from services.diarization import SpeakerSegment

        mock_segments = [
            SpeakerSegment("SPEAKER_00", 0.0, 5.0, 5.0),
            SpeakerSegment("SPEAKER_01", 5.5, 10.0, 4.5),
            SpeakerSegment("SPEAKER_00", 10.5, 15.0, 4.5),
        ]

        patches = {
            "diarize": patch("processor.diarize_audio", return_value=mock_segments),
            "transcribe": patch(
                "processor.transcribe_audio",
                side_effect=[
                    "Wah this one damn good lah",
                    "Cannot lor I got other things",
                    "Walao eh really jialat sia",
                ],
            ),
            "extract": patch(
                "processor.extract_speaker_segment",
                return_value=b"RIFF" + b"\x00" * 100,
            ),
            "storage": patch("processor.storage"),
        }

        started = {k: p.start() for k, p in patches.items()}
        started["storage"].get_public_url = MagicMock(
            side_effect=lambda p: f"https://storage.example.com/{p}"
        )
        started["storage"].upload_processed_audio = AsyncMock(
            side_effect=lambda sid, content, fname: f"sessions/{sid}/{fname}"
        )

        yield started, mock_segments

        for p in patches.values():
            p.stop()

    def test_run_diarization_calls_service(self, mock_all_services):
        """Test that run_diarization calls the diarization service."""
        from processor import run_diarization

        mocks, expected_segments = mock_all_services

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"fake audio")
            temp_path = f.name

        try:
            segments = run_diarization(temp_path)

            assert len(segments) == 3
            assert segments[0].speaker_id == "SPEAKER_00"
            assert segments[1].speaker_id == "SPEAKER_01"
            mocks["diarize"].assert_called_once_with(temp_path)
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_transcribe_and_count_aggregates_per_speaker(
        self, db, sample_session, mock_all_services
    ):
        """Test that transcribe_and_count aggregates words per speaker."""
        from processor import transcribe_and_count

        mocks, mock_segments = mock_all_services

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"fake audio")
            temp_path = f.name

        try:
            # Refresh session in this db session
            from models import Session

            session = db.query(Session).filter(Session.id == sample_session.id).first()

            speaker_results = await transcribe_and_count(
                temp_path, mock_segments, db, session
            )

            # Should have 2 speakers
            assert "SPEAKER_00" in speaker_results
            assert "SPEAKER_01" in speaker_results

            # SPEAKER_00 had 2 segments
            speaker_00_counts = speaker_results["SPEAKER_00"]
            assert "wah" in speaker_00_counts or "walao" in speaker_00_counts

        finally:
            os.unlink(temp_path)


class TestWordCountingEdgeCases:
    """Test edge cases in word counting."""

    def test_empty_text(self):
        """Test counting with empty text."""
        from services.transcription import count_target_words

        counts = count_target_words("")
        assert counts == {} or all(v == 0 for v in counts.values())

    def test_no_target_words(self):
        """Test counting when no target words present."""
        from services.transcription import count_target_words

        counts = count_target_words("Hello world this is a test")
        # Should have zero counts or empty dict
        total = sum(counts.values()) if counts else 0
        assert total == 0

    def test_repeated_words(self):
        """Test counting repeated target words."""
        from services.transcription import count_target_words

        counts = count_target_words("lah lah lah lah lah")
        assert counts.get("lah", 0) == 5

    def test_words_in_context(self):
        """Test that words are found in natural context."""
        from services.transcription import count_target_words

        text = "Aiyo, I forgot lah! So paiseh sia, really jialat one."
        counts = count_target_words(text)

        assert counts.get("aiyo", 0) >= 1
        assert counts.get("lah", 0) >= 1
        assert counts.get("paiseh", 0) >= 1
        assert counts.get("sia", 0) >= 1
        assert counts.get("jialat", 0) >= 1


class TestCorrectionsComprehensive:
    """Comprehensive tests for correction patterns."""

    def test_common_misrecognitions(self):
        """Test common ASR misrecognitions are corrected."""
        from services.transcription import apply_corrections

        test_cases = [
            ("while up", "walao"),
            ("wa lao", "walao"),
            ("la", "lah"),
            ("low", "lor"),
        ]

        for input_text, expected_word in test_cases:
            corrected = apply_corrections(input_text).lower()
            assert expected_word in corrected, f"'{input_text}' should contain '{expected_word}' after correction"

    def test_corrections_preserve_other_text(self):
        """Test that corrections don't destroy surrounding text."""
        from services.transcription import apply_corrections

        text = "The meeting is at three while up we need to go"
        corrected = apply_corrections(text)

        # Should fix "while up" but keep other words
        assert "meeting" in corrected.lower()
        assert "three" in corrected.lower()
        assert "walao" in corrected.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
