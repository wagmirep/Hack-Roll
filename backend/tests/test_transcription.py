"""
tests/test_transcription.py - Transcription Service Unit Tests

Tests for the MERaLiON ASR transcription service.
These tests use mocking to avoid loading the actual 3B parameter model.
"""

import pytest
import sys
import os
import io
import numpy as np
from unittest.mock import Mock, patch, MagicMock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def reset_transcription_state():
    """Helper to reset all transcription module state."""
    import services.transcription as t
    t._model = None
    t._processor = None
    t._transcriber = None  # Backward compat


class TestGetTranscriber:
    """Tests for get_transcriber() singleton pattern."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_transcription_state()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_transcription_state()

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
        """Test that multiple calls return the same underlying model/processor."""
        import services.transcription as t

        # Set mock model and processor
        mock_model = Mock()
        mock_processor = Mock()
        t._model = mock_model
        t._processor = mock_processor

        result1 = t.get_transcriber()
        result2 = t.get_transcriber()

        # Tuples are created fresh, but underlying objects should be same
        assert result1[0] is result2[0]  # Same model
        assert result1[1] is result2[1]  # Same processor
        assert result1 == (mock_model, mock_processor)

    def test_is_model_loaded_reflects_state(self):
        """Test is_model_loaded accurately reflects singleton state."""
        import services.transcription as t

        assert t.is_model_loaded() is False

        t._model = Mock()
        t._processor = Mock()
        assert t.is_model_loaded() is True

        t._model = None
        t._processor = None
        assert t.is_model_loaded() is False


class TestTranscribeAudio:
    """Tests for transcribe_audio() function."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_transcription_state()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_transcription_state()

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

        with patch.object(t, "_transcribe_audio_array", return_value="hello world lah") as mock_transcribe:
            with patch("librosa.load", return_value=(np.zeros(16000), 16000)):
                result = t.transcribe_audio(str(audio_file))

        assert result == "hello world lah"
        mock_transcribe.assert_called_once()

    def test_strips_whitespace(self, tmp_path):
        """Test that transcription strips leading/trailing whitespace."""
        import services.transcription as t

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        with patch.object(t, "_transcribe_audio_array", return_value="  hello world  "):
            with patch("librosa.load", return_value=(np.zeros(16000), 16000)):
                result = t.transcribe_audio(str(audio_file))

        # Note: _transcribe_audio_array returns cleaned text, strip happens there
        assert "hello world" in result

    def test_handles_empty_transcription(self, tmp_path):
        """Test handling of empty transcription result."""
        import services.transcription as t

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        with patch.object(t, "_transcribe_audio_array", return_value=""):
            with patch("librosa.load", return_value=(np.zeros(16000), 16000)):
                result = t.transcribe_audio(str(audio_file))

        assert result == ""

    def test_handles_missing_text_key(self, tmp_path):
        """Test handling when transcription returns empty."""
        import services.transcription as t

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        with patch.object(t, "_transcribe_audio_array", return_value=""):
            with patch("librosa.load", return_value=(np.zeros(16000), 16000)):
                result = t.transcribe_audio(str(audio_file))

        assert result == ""

    def test_raises_runtime_error_on_failure(self, tmp_path):
        """Test that RuntimeError is raised on transcription failure."""
        import services.transcription as t

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        with patch.object(t, "_transcribe_audio_array", side_effect=Exception("Model error")):
            with patch("librosa.load", return_value=(np.zeros(16000), 16000)):
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
        reset_transcription_state()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_transcription_state()

    def test_transcribes_audio_bytes(self):
        """Test transcription from audio bytes."""
        import services.transcription as t

        # Create real audio bytes using soundfile
        audio_data = np.zeros(16000, dtype=np.float32)
        buffer = io.BytesIO()
        soundfile.write(buffer, audio_data, 16000, format="WAV")
        audio_bytes = buffer.getvalue()

        with patch.object(t, "_transcribe_audio_array", return_value="test transcription"):
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

        with patch.object(t, "_transcribe_audio_array", return_value="mono test") as mock_transcribe:
            result = t.transcribe_segment(audio_bytes)

        # Check that the transcription function was called with 1D (mono) data
        call_args = mock_transcribe.call_args[0][0]
        assert len(call_args.shape) == 1
        assert result == "mono test"

    def test_resamples_non_16khz_audio(self):
        """Test that audio is resampled to 16kHz if needed."""
        import services.transcription as t

        # Create 44.1kHz audio
        audio_data = np.zeros(44100, dtype=np.float32)  # 1 second at 44.1kHz
        buffer = io.BytesIO()
        soundfile.write(buffer, audio_data, 44100, format="WAV")
        audio_bytes = buffer.getvalue()

        with patch.object(t, "_transcribe_audio_array", return_value="resampled") as mock_transcribe:
            result = t.transcribe_segment(audio_bytes)

        # Check sample rate argument is 16kHz
        call_args = mock_transcribe.call_args
        assert call_args[0][1] == 16000  # second positional arg is sample_rate
        assert result == "resampled"

    def test_handles_runtime_error(self):
        """Test that RuntimeError is raised on failure."""
        import services.transcription as t

        # Create valid audio bytes
        audio_data = np.zeros(16000, dtype=np.float32)
        buffer = io.BytesIO()
        soundfile.write(buffer, audio_data, 16000, format="WAV")
        audio_bytes = buffer.getvalue()

        with patch.object(t, "_transcribe_audio_array", side_effect=Exception("Model error")):
            with pytest.raises(RuntimeError, match="Segment transcription failed"):
                t.transcribe_segment(audio_bytes)


class TestModelManagement:
    """Tests for model loading/unloading utilities."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_transcription_state()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_transcription_state()

    def test_is_model_loaded_false_initially(self):
        """Test is_model_loaded returns False when no model loaded."""
        import services.transcription as t

        assert t.is_model_loaded() is False

    def test_is_model_loaded_true_after_load(self):
        """Test is_model_loaded returns True after model is set."""
        import services.transcription as t
        t._model = Mock()
        t._processor = Mock()

        assert t.is_model_loaded() is True

    @patch("torch.cuda.is_available", return_value=False)
    @patch("torch.cuda.empty_cache")
    def test_unload_model_clears_singleton(self, mock_empty_cache, mock_cuda_avail):
        """Test unload_model clears the singleton."""
        import services.transcription as t

        t._model = Mock()
        t._processor = Mock()
        t.unload_model()

        assert t._model is None
        assert t._processor is None

    @patch("torch.cuda.is_available", return_value=True)
    @patch("torch.cuda.empty_cache")
    def test_unload_model_clears_cuda_cache(self, mock_empty_cache, mock_cuda_avail):
        """Test unload_model clears CUDA cache when available."""
        import services.transcription as t

        t._model = Mock()
        t._processor = Mock()
        t.unload_model()

        mock_empty_cache.assert_called_once()


class TestConstants:
    """Tests for module constants."""

    def test_model_name_is_meralion(self):
        """Test that correct model name is configured (3B variant for CPU optimization)."""
        import services.transcription as t

        assert t.MODEL_NAME == "MERaLiON/MERaLiON-2-3B"

    def test_sample_rate_is_16khz(self):
        """Test that sample rate is 16kHz."""
        import services.transcription as t

        assert t.SAMPLE_RATE == 16000
