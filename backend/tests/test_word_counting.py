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
