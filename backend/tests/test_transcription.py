"""
tests/test_transcription.py - Transcription Service Unit Tests

Tests for the external API transcription service and Singlish corrections.
Uses mocking to avoid actual API calls.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestTranscribeAudio:
    """Tests for transcribe_audio() function."""

    def test_raises_on_missing_file(self):
        """Test that FileNotFoundError is raised for missing files."""
        from services.transcription import transcribe_audio

        with pytest.raises(FileNotFoundError):
            transcribe_audio("/nonexistent/path/audio.wav")

    def test_raises_when_api_not_configured(self, tmp_path):
        """Test that RuntimeError is raised when API URL not set."""
        from services.transcription import transcribe_audio

        # Create a dummy audio file
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        with patch("services.transcription._get_transcription_api_url", return_value=None):
            with pytest.raises(RuntimeError, match="TRANSCRIPTION_API_URL not configured"):
                transcribe_audio(str(audio_file))

    def test_calls_external_api(self, tmp_path):
        """Test that transcription calls external API."""
        from services.transcription import transcribe_audio

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"raw_transcription": "hello world lah"}

        with patch("services.transcription._get_transcription_api_url", return_value="https://api.example.com"):
            with patch("services.transcription._convert_to_wav", return_value=b"wav_bytes"):
                with patch("httpx.Client") as mock_client:
                    mock_client.return_value.__enter__.return_value.post.return_value = mock_response
                    result = transcribe_audio(str(audio_file))

        assert result == "hello world lah"

    def test_handles_api_error(self, tmp_path):
        """Test handling of API error responses."""
        from services.transcription import transcribe_audio

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("services.transcription._get_transcription_api_url", return_value="https://api.example.com"):
            with patch("services.transcription._convert_to_wav", return_value=b"wav_bytes"):
                with patch("httpx.Client") as mock_client:
                    mock_client.return_value.__enter__.return_value.post.return_value = mock_response
                    with pytest.raises(RuntimeError, match="API returned 500"):
                        transcribe_audio(str(audio_file))


class TestTranscribeSegment:
    """Tests for transcribe_segment() function."""

    def test_raises_when_api_not_configured(self):
        """Test that RuntimeError is raised when API URL not set."""
        from services.transcription import transcribe_segment

        with patch("services.transcription._get_transcription_api_url", return_value=None):
            with pytest.raises(RuntimeError, match="TRANSCRIPTION_API_URL not configured"):
                transcribe_segment(b"fake audio bytes")

    def test_calls_external_api(self):
        """Test that transcription calls external API."""
        from services.transcription import transcribe_segment

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"raw_transcription": "test transcription"}

        with patch("services.transcription._get_transcription_api_url", return_value="https://api.example.com"):
            with patch("httpx.Client") as mock_client:
                mock_client.return_value.__enter__.return_value.post.return_value = mock_response
                result = transcribe_segment(b"fake audio bytes")

        assert result == "test transcription"


class TestIsUsingExternalApi:
    """Tests for is_using_external_api() function."""

    def test_returns_true_when_url_configured(self):
        """Test returns True when API URL is set."""
        from services.transcription import is_using_external_api

        with patch("services.transcription._get_transcription_api_url", return_value="https://api.example.com"):
            assert is_using_external_api() is True

    def test_returns_false_when_url_not_configured(self):
        """Test returns False when API URL is not set."""
        from services.transcription import is_using_external_api

        with patch("services.transcription._get_transcription_api_url", return_value=None):
            assert is_using_external_api() is False

    def test_returns_false_for_empty_string(self):
        """Test returns False when API URL is empty string."""
        from services.transcription import is_using_external_api

        with patch("services.transcription._get_transcription_api_url", return_value=""):
            assert is_using_external_api() is False


class TestConstants:
    """Tests for module constants."""

    def test_sample_rate_is_16khz(self):
        """Test that sample rate is 16kHz."""
        from services.transcription import SAMPLE_RATE

        assert SAMPLE_RATE == 16000

    def test_target_words_includes_key_singlish(self):
        """Test that TARGET_WORDS includes key Singlish words."""
        from services.transcription import TARGET_WORDS

        assert "lah" in TARGET_WORDS
        assert "walao" in TARGET_WORDS
        assert "shiok" in TARGET_WORDS
        assert "paiseh" in TARGET_WORDS

    def test_corrections_handles_common_misrecognitions(self):
        """Test that CORRECTIONS includes common ASR mistakes."""
        from services.transcription import CORRECTIONS

        assert CORRECTIONS.get("wa lao") == "walao"
        assert CORRECTIONS.get("cheap buy") == "cheebai"
        assert CORRECTIONS.get("lunch hour") == "lanjiao"
