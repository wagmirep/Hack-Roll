"""
tests/test_transcription.py - Transcription Service Unit Tests

Tests for the MERaLiON ASR transcription service.
These tests use mocking to avoid loading the actual 10B parameter model.
"""

import pytest
import sys
import os
import io
import numpy as np
from unittest.mock import Mock, patch, MagicMock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestGetTranscriber:
    """Tests for get_transcriber() singleton pattern."""

    def setup_method(self):
        """Reset singleton before each test."""
        import services.transcription as t
        t._transcriber = None

    def teardown_method(self):
        """Cleanup after each test."""
        import services.transcription as t
        t._transcriber = None

    def test_returns_pipeline_instance(self):
        """Test that get_transcriber returns a pipeline."""
        import services.transcription as t

        mock_pipeline_func = Mock(return_value=Mock())
        mock_torch = Mock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.float32 = "float32"

        with patch.dict("sys.modules", {"transformers": Mock(pipeline=mock_pipeline_func), "torch": mock_torch}):
            with patch("services.transcription.pipeline", mock_pipeline_func, create=True):
                with patch("services.transcription.torch", mock_torch, create=True):
                    # Need to reload the function to use patched modules
                    result = t.get_transcriber()

                    assert result is not None

    def test_singleton_returns_same_instance(self):
        """Test that multiple calls return the same instance."""
        import services.transcription as t

        # Set a mock transcriber
        mock_transcriber = Mock()
        t._transcriber = mock_transcriber

        result1 = t.get_transcriber()
        result2 = t.get_transcriber()

        assert result1 is result2
        assert result1 is mock_transcriber

    def test_is_model_loaded_reflects_state(self):
        """Test is_model_loaded accurately reflects singleton state."""
        import services.transcription as t

        assert t.is_model_loaded() is False

        t._transcriber = Mock()
        assert t.is_model_loaded() is True

        t._transcriber = None
        assert t.is_model_loaded() is False


class TestTranscribeAudio:
    """Tests for transcribe_audio() function."""

    def setup_method(self):
        """Reset singleton before each test."""
        import services.transcription as t
        t._transcriber = None

    def teardown_method(self):
        """Cleanup after each test."""
        import services.transcription as t
        t._transcriber = None

    def test_raises_on_missing_file(self):
        """Test that FileNotFoundError is raised for missing files."""
        import services.transcription as t

        with pytest.raises(FileNotFoundError):
            t.transcribe_audio("/nonexistent/path/audio.wav")

    def test_returns_transcription_text(self, tmp_path):
        """Test that transcription returns text."""
        import services.transcription as t

        # Create a dummy audio file
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        mock_transcriber = Mock()
        mock_transcriber.return_value = {"text": "hello world lah"}
        t._transcriber = mock_transcriber

        result = t.transcribe_audio(str(audio_file))

        assert result == "hello world lah"
        mock_transcriber.assert_called_once_with(str(audio_file))

    def test_strips_whitespace(self, tmp_path):
        """Test that transcription strips leading/trailing whitespace."""
        import services.transcription as t

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        mock_transcriber = Mock()
        mock_transcriber.return_value = {"text": "  hello world  "}
        t._transcriber = mock_transcriber

        result = t.transcribe_audio(str(audio_file))

        assert result == "hello world"

    def test_handles_empty_transcription(self, tmp_path):
        """Test handling of empty transcription result."""
        import services.transcription as t

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        mock_transcriber = Mock()
        mock_transcriber.return_value = {"text": ""}
        t._transcriber = mock_transcriber

        result = t.transcribe_audio(str(audio_file))

        assert result == ""

    def test_handles_missing_text_key(self, tmp_path):
        """Test handling when 'text' key is missing from result."""
        import services.transcription as t

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        mock_transcriber = Mock()
        mock_transcriber.return_value = {}  # No 'text' key
        t._transcriber = mock_transcriber

        result = t.transcribe_audio(str(audio_file))

        assert result == ""

    def test_raises_runtime_error_on_failure(self, tmp_path):
        """Test that RuntimeError is raised on transcription failure."""
        import services.transcription as t

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        mock_transcriber = Mock()
        mock_transcriber.side_effect = Exception("Model error")
        t._transcriber = mock_transcriber

        with pytest.raises(RuntimeError, match="Transcription failed"):
            t.transcribe_audio(str(audio_file))


try:
    import soundfile
    import librosa
    HAS_AUDIO_DEPS = True
except ImportError:
    HAS_AUDIO_DEPS = False


@pytest.mark.skipif(not HAS_AUDIO_DEPS, reason="soundfile/librosa not installed")
class TestTranscribeSegment:
    """Tests for transcribe_segment() function.

    These tests require soundfile and librosa to be installed.
    They test the bytes-based transcription functionality.
    """

    def setup_method(self):
        """Reset singleton before each test."""
        import services.transcription as t
        t._transcriber = None

    def teardown_method(self):
        """Cleanup after each test."""
        import services.transcription as t
        t._transcriber = None

    def test_transcribes_audio_bytes(self):
        """Test transcription from audio bytes."""
        import services.transcription as t

        # Create real audio bytes using soundfile
        audio_data = np.zeros(16000, dtype=np.float32)
        buffer = io.BytesIO()
        soundfile.write(buffer, audio_data, 16000, format="WAV")
        audio_bytes = buffer.getvalue()

        mock_transcriber = Mock()
        mock_transcriber.return_value = {"text": "test transcription"}
        t._transcriber = mock_transcriber

        result = t.transcribe_segment(audio_bytes)

        assert result == "test transcription"

    def test_converts_stereo_to_mono(self):
        """Test that stereo audio is converted to mono."""
        import services.transcription as t

        # Create stereo audio
        stereo_audio = np.column_stack([
            np.zeros(16000, dtype=np.float32),
            np.ones(16000, dtype=np.float32) * 0.5
        ])
        buffer = io.BytesIO()
        soundfile.write(buffer, stereo_audio, 16000, format="WAV")
        audio_bytes = buffer.getvalue()

        mock_transcriber = Mock()
        mock_transcriber.return_value = {"text": "mono test"}
        t._transcriber = mock_transcriber

        result = t.transcribe_segment(audio_bytes)

        # Check that the input to transcriber is mono (1D)
        call_args = mock_transcriber.call_args[0][0]
        assert len(call_args["raw"].shape) == 1
        assert result == "mono test"

    def test_resamples_non_16khz_audio(self):
        """Test that audio is resampled to 16kHz if needed."""
        import services.transcription as t

        # Create 44.1kHz audio
        audio_data = np.zeros(44100, dtype=np.float32)  # 1 second at 44.1kHz
        buffer = io.BytesIO()
        soundfile.write(buffer, audio_data, 44100, format="WAV")
        audio_bytes = buffer.getvalue()

        mock_transcriber = Mock()
        mock_transcriber.return_value = {"text": "resampled"}
        t._transcriber = mock_transcriber

        result = t.transcribe_segment(audio_bytes)

        # Check input was resampled to 16kHz
        call_args = mock_transcriber.call_args[0][0]
        assert call_args["sampling_rate"] == 16000
        assert result == "resampled"

    def test_handles_runtime_error(self):
        """Test that RuntimeError is raised on failure."""
        import services.transcription as t

        mock_transcriber = Mock()
        mock_transcriber.side_effect = Exception("Model error")
        t._transcriber = mock_transcriber

        # Create valid audio bytes
        audio_data = np.zeros(16000, dtype=np.float32)
        buffer = io.BytesIO()
        soundfile.write(buffer, audio_data, 16000, format="WAV")
        audio_bytes = buffer.getvalue()

        with pytest.raises(RuntimeError, match="Segment transcription failed"):
            t.transcribe_segment(audio_bytes)


class TestModelManagement:
    """Tests for model loading/unloading utilities."""

    def setup_method(self):
        """Reset singleton before each test."""
        import services.transcription as t
        t._transcriber = None

    def teardown_method(self):
        """Cleanup after each test."""
        import services.transcription as t
        t._transcriber = None

    def test_is_model_loaded_false_initially(self):
        """Test is_model_loaded returns False when no model loaded."""
        import services.transcription as t

        assert t.is_model_loaded() is False

    def test_is_model_loaded_true_after_load(self):
        """Test is_model_loaded returns True after model is set."""
        import services.transcription as t
        t._transcriber = Mock()

        assert t.is_model_loaded() is True

    @patch("torch.cuda.is_available", return_value=False)
    @patch("torch.cuda.empty_cache")
    def test_unload_model_clears_singleton(self, mock_empty_cache, mock_cuda_avail):
        """Test unload_model clears the singleton."""
        import services.transcription as t

        t._transcriber = Mock()
        t.unload_model()

        assert t._transcriber is None

    @patch("torch.cuda.is_available", return_value=True)
    @patch("torch.cuda.empty_cache")
    def test_unload_model_clears_cuda_cache(self, mock_empty_cache, mock_cuda_avail):
        """Test unload_model clears CUDA cache when available."""
        import services.transcription as t

        t._transcriber = Mock()
        t.unload_model()

        mock_empty_cache.assert_called_once()


class TestConstants:
    """Tests for module constants."""

    def test_model_name_is_meralion(self):
        """Test that correct model name is configured."""
        import services.transcription as t

        assert t.MODEL_NAME == "MERaLiON/MERaLiON-2-10B-ASR"

    def test_sample_rate_is_16khz(self):
        """Test that sample rate is 16kHz."""
        import services.transcription as t

        assert t.SAMPLE_RATE == 16000
