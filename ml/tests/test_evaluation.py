"""
test_evaluation.py - Evaluation Script Tests

PURPOSE:
    Test model evaluation metrics and reporting.
    Ensures evaluation is accurate and reproducible.

REFERENCED BY:
    - pytest test runner
    - CI/CD pipeline

REFERENCES:
    - scripts/evaluate.py - Evaluation script

TEST CASES:

    test_wer_calculation:
        - Known reference and hypothesis
        - WER calculated correctly
        - Edge cases (empty, identical) handled

    test_target_word_accuracy:
        - Known transcription with target words
        - Accuracy calculated correctly
        - Per-word breakdown correct

    test_confusion_matrix:
        - Common misrecognitions tracked
        - Matrix format correct

    test_report_generation:
        - Report contains all metrics
        - JSON format valid
        - Comparison section correct

    test_base_vs_finetuned_comparison:
        - Both models evaluated
        - Improvement calculated
        - Negative improvement handled

    test_edge_cases:
        - Empty test set
        - All correct predictions
        - All incorrect predictions
"""
