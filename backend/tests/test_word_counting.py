"""
tests/test_word_counting.py - Word Counting Logic Tests

PURPOSE:
    Test the Singlish word detection and counting logic.
    Focuses on corrections dictionary and target word matching.

RESPONSIBILITIES:
    - Test corrections dictionary completeness
    - Test word boundary detection
    - Test case insensitivity
    - Test counting accuracy
    - Test edge cases (punctuation, multiple occurrences)

REFERENCED BY:
    - pytest (test discovery)
    - CI/CD pipeline

REFERENCES:
    - conftest.py - Test fixtures
    - services/transcription.py - Word counting functions
    - processor.py - Uses word counting

TEST CASES:
    test_count_single_word:
        - Text: "walao that's crazy"
        - Returns: {'walao': 1}

    test_count_multiple_same_word:
        - Text: "lah lah lah you know lah"
        - Returns: {'lah': 4}

    test_count_multiple_different_words:
        - Text: "walao sia this is shiok"
        - Returns: {'walao': 1, 'sia': 1, 'shiok': 1}

    test_correction_while_up:
        - Text: "while up why you do that"
        - Corrected: "walao why you do that"
        - Returns: {'walao': 1}

    test_correction_wa_lao:
        - Text: "wa lao eh"
        - Corrected: "walao eh"
        - Returns: {'walao': 1}

    test_case_insensitive:
        - Text: "WALAO Walao walao"
        - Returns: {'walao': 3}

    test_word_boundaries:
        - Text: "salah" (not "lah")
        - Returns: {} (no match)

    test_punctuation_handling:
        - Text: "walao! lah... sia?"
        - Returns: {'walao': 1, 'lah': 1, 'sia': 1}

    test_empty_text:
        - Text: ""
        - Returns: {}

    test_no_target_words:
        - Text: "hello how are you today"
        - Returns: {}

    test_all_target_words:
        - Text containing all target words
        - Returns count for each
"""

import pytest
from services.transcription import (
    apply_corrections,
    count_target_words,
    process_transcription,
    CORRECTIONS,
    WORD_CORRECTIONS,
    TARGET_WORDS,
)


# ============================================================================
# Tests for count_target_words()
# ============================================================================

class TestCountTargetWords:
    """Tests for the count_target_words function."""

    def test_count_single_word(self):
        """Count a single occurrence of a target word."""
        text = "walao that's crazy"
        result = count_target_words(text)
        assert result == {'walao': 1}

    def test_count_multiple_same_word(self):
        """Count multiple occurrences of the same word."""
        text = "lah lah lah you know lah"
        result = count_target_words(text)
        assert result == {'lah': 4}

    def test_count_multiple_different_words(self):
        """Count multiple different target words."""
        text = "walao sia this is shiok"
        result = count_target_words(text)
        assert result == {'walao': 1, 'sia': 1, 'shiok': 1}

    def test_case_insensitive(self):
        """Ensure counting is case-insensitive."""
        text = "WALAO Walao walao"
        result = count_target_words(text)
        assert result == {'walao': 3}

    def test_word_boundaries_no_false_positive(self):
        """Ensure 'salah' doesn't count as 'lah'."""
        text = "salah is a different word"
        result = count_target_words(text)
        assert result == {}

    def test_word_boundaries_partial_match(self):
        """Ensure partial matches within words are not counted."""
        text = "malaysia is a beautiful country"
        result = count_target_words(text)
        # 'sia' should not match within 'malaysia'
        assert 'sia' not in result

    def test_punctuation_handling(self):
        """Ensure punctuation doesn't break word detection."""
        text = "walao! lah... sia?"
        result = count_target_words(text)
        assert result == {'walao': 1, 'lah': 1, 'sia': 1}

    def test_punctuation_adjacent(self):
        """Test words surrounded by various punctuation."""
        text = "(walao) [lah] {sia} 'shiok' \"sian\""
        result = count_target_words(text)
        assert result == {'walao': 1, 'lah': 1, 'sia': 1, 'shiok': 1, 'sian': 1}

    def test_empty_text(self):
        """Return empty dict for empty input."""
        result = count_target_words("")
        assert result == {}

    def test_none_text(self):
        """Return empty dict for None input (handled gracefully)."""
        result = count_target_words(None)
        assert result == {}

    def test_no_target_words(self):
        """Return empty dict when no target words present."""
        text = "hello how are you today"
        result = count_target_words(text)
        assert result == {}

    def test_word_at_start(self):
        """Count word at the beginning of text."""
        text = "lah I tell you"
        result = count_target_words(text)
        assert result == {'lah': 1}

    def test_word_at_end(self):
        """Count word at the end of text."""
        text = "you know lah"
        result = count_target_words(text)
        assert result == {'lah': 1}

    def test_word_only(self):
        """Count when text is just the target word."""
        text = "walao"
        result = count_target_words(text)
        assert result == {'walao': 1}

    def test_multiple_same_word_with_punctuation(self):
        """Count multiple occurrences with punctuation."""
        text = "lah! lah? lah."
        result = count_target_words(text)
        assert result == {'lah': 3}

    def test_newlines_and_tabs(self):
        """Handle whitespace variations."""
        text = "walao\nlah\tsia"
        result = count_target_words(text)
        assert result == {'walao': 1, 'lah': 1, 'sia': 1}

    def test_can_word_standalone(self):
        """Ensure 'can' is counted when standalone."""
        text = "can you do it? yes can!"
        result = count_target_words(text)
        assert result == {'can': 2}

    def test_meh_particle(self):
        """Test counting 'meh' particle."""
        text = "good meh? not bad meh"
        result = count_target_words(text)
        assert result == {'meh': 2}


# ============================================================================
# Tests for apply_corrections()
# ============================================================================

class TestApplyCorrections:
    """Tests for the apply_corrections function."""

    def test_correction_while_up(self):
        """Correct 'while up' to 'walao'."""
        text = "while up why you do that"
        result = apply_corrections(text)
        assert "walao" in result.lower()
        assert "while up" not in result.lower()

    def test_correction_wa_lao(self):
        """Correct 'wa lao' to 'walao'."""
        text = "wa lao eh"
        result = apply_corrections(text)
        assert "walao" in result.lower()

    def test_correction_wah_lao(self):
        """Correct 'wah lao' to 'walao'."""
        text = "wah lao this is crazy"
        result = apply_corrections(text)
        assert "walao" in result.lower()

    def test_correction_cheap_buy(self):
        """Correct 'cheap buy' to 'cheebai'."""
        text = "you are such a cheap buy"
        result = apply_corrections(text)
        assert "cheebai" in result.lower()

    def test_correction_lunch_hour(self):
        """Correct 'lunch hour' to 'lanjiao'."""
        text = "lunch hour man"
        result = apply_corrections(text)
        assert "lanjiao" in result.lower()

    def test_correction_pie_say(self):
        """Correct 'pie say' to 'paiseh'."""
        text = "so pie say"
        result = apply_corrections(text)
        assert "paiseh" in result.lower()

    def test_correction_shook(self):
        """Correct 'shook' to 'shiok'."""
        text = "this food is shook"
        result = apply_corrections(text)
        assert "shiok" in result.lower()

    def test_correction_case_insensitive(self):
        """Corrections should be case-insensitive."""
        text = "WHILE UP why you do that"
        result = apply_corrections(text)
        assert "walao" in result.lower()

    def test_correction_la_to_lah(self):
        """Correct standalone 'la' to 'lah'."""
        text = "okay la"
        result = apply_corrections(text)
        assert "lah" in result.lower()

    def test_correction_low_to_lor(self):
        """Correct standalone 'low' to 'lor'."""
        text = "okay low"
        result = apply_corrections(text)
        assert "lor" in result.lower()

    def test_no_correction_low_in_word(self):
        """Don't correct 'low' within other words like 'below'."""
        text = "the price is below average"
        result = apply_corrections(text)
        assert "below" in result.lower()
        assert "belor" not in result.lower()

    def test_empty_text(self):
        """Return empty string for empty input."""
        result = apply_corrections("")
        assert result == ""

    def test_none_text(self):
        """Handle None input gracefully."""
        result = apply_corrections(None)
        assert result is None

    def test_no_corrections_needed(self):
        """Return unchanged text when no corrections apply."""
        text = "hello world"
        result = apply_corrections(text)
        assert result == "hello world"

    def test_multiple_corrections(self):
        """Apply multiple corrections in one text."""
        text = "while up this is shook la"
        result = apply_corrections(text)
        assert "walao" in result.lower()
        assert "shiok" in result.lower()
        assert "lah" in result.lower()

    def test_see_ya_to_sia(self):
        """Correct 'see ya' to 'sia'."""
        text = "good see ya"
        result = apply_corrections(text)
        assert "sia" in result.lower()


# ============================================================================
# Tests for process_transcription()
# ============================================================================

class TestProcessTranscription:
    """Tests for the combined process_transcription function."""

    def test_process_with_corrections_and_counting(self):
        """Test full pipeline: corrections then counting."""
        text = "while up this is shook la"
        corrected, counts = process_transcription(text)

        # Check corrections applied
        assert "walao" in corrected.lower()
        assert "shiok" in corrected.lower()
        assert "lah" in corrected.lower()

        # Check counting
        assert counts.get('walao', 0) >= 1
        assert counts.get('shiok', 0) >= 1
        assert counts.get('lah', 0) >= 1

    def test_process_no_corrections_needed(self):
        """Test when text already has correct spelling."""
        text = "walao this is shiok lah"
        corrected, counts = process_transcription(text)

        assert corrected == text
        assert counts == {'walao': 1, 'shiok': 1, 'lah': 1}

    def test_process_empty_text(self):
        """Test with empty input."""
        corrected, counts = process_transcription("")
        assert corrected == ""
        assert counts == {}

    def test_process_realistic_sentence(self):
        """Test with a realistic Singlish sentence."""
        text = "wa lao eh why you never jio me? so pie say sia"
        corrected, counts = process_transcription(text)

        # Should have corrected words
        assert "walao" in corrected.lower()
        assert "paiseh" in corrected.lower()
        assert "sia" in corrected.lower()


# ============================================================================
# Tests for edge cases and integration
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_all_target_words_present(self):
        """Verify all target words can be detected."""
        # Build a sentence with all target words
        all_words_text = " ".join(TARGET_WORDS)
        counts = count_target_words(all_words_text)

        for word in TARGET_WORDS:
            assert word in counts, f"Missing target word: {word}"
            assert counts[word] == 1

    def test_repeated_corrections(self):
        """Ensure corrections don't stack incorrectly."""
        text = "wa lao wa lao wa lao"
        result = apply_corrections(text)
        # Should become "walao walao walao"
        count = result.lower().count("walao")
        assert count == 3

    def test_mixed_case_throughout(self):
        """Test mixed case handling throughout the pipeline."""
        text = "WaLaO SiA this is ShIoK LAH"
        counts = count_target_words(text)
        assert counts == {'walao': 1, 'sia': 1, 'shiok': 1, 'lah': 1}

    def test_word_adjacent_to_numbers(self):
        """Test words next to numbers."""
        text = "walao123 456lah lah789"
        counts = count_target_words(text)
        # Only 'lah' that's separated should count
        # The exact behavior depends on implementation
        # At minimum, the standalone one should work

    def test_hyphenated_words(self):
        """Test handling of hyphenated contexts."""
        text = "super-shiok lah-worthy"
        counts = count_target_words(text)
        assert 'shiok' in counts
        assert 'lah' in counts

    def test_long_text_performance(self):
        """Test with longer text to ensure no issues."""
        base = "walao sia this is shiok lah "
        text = base * 100
        counts = count_target_words(text)
        assert counts == {'walao': 100, 'sia': 100, 'shiok': 100, 'lah': 100}

    def test_unicode_handling(self):
        """Test handling of unicode characters."""
        text = "walao 你好 sia"
        counts = count_target_words(text)
        assert counts == {'walao': 1, 'sia': 1}


# ============================================================================
# Tests for corrections dictionary coverage
# ============================================================================

class TestCorrectionsCoverage:
    """Tests to verify corrections dictionary is comprehensive."""

    def test_walao_variations(self):
        """Test all walao spelling variations."""
        variations = ['while up', 'wa lao', 'wah lao', 'wah low', 'wa low', 'wah lau', 'wa lau']
        for variation in variations:
            result = apply_corrections(variation)
            assert 'walao' in result.lower(), f"Failed for: {variation}"

    def test_cheebai_variations(self):
        """Test all cheebai spelling variations."""
        variations = ['cheap buy', 'chee bye', 'chi bye', 'chee bai', 'chi bai']
        for variation in variations:
            result = apply_corrections(variation)
            assert 'cheebai' in result.lower(), f"Failed for: {variation}"

    def test_lanjiao_variations(self):
        """Test all lanjiao spelling variations."""
        variations = ['lunch hour', 'lan jiao', 'lan chow', 'lan chiao']
        for variation in variations:
            result = apply_corrections(variation)
            assert 'lanjiao' in result.lower(), f"Failed for: {variation}"

    def test_paiseh_variations(self):
        """Test all paiseh spelling variations."""
        variations = ['pie say', 'pai seh', 'pie seh', 'pai say']
        for variation in variations:
            result = apply_corrections(variation)
            assert 'paiseh' in result.lower(), f"Failed for: {variation}"
