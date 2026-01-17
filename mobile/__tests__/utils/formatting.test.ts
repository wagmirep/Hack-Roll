/**
 * formatting.test.ts - Formatting Utilities Tests
 *
 * PURPOSE:
 *     Test the formatting utility functions.
 *     Covers number, date, and string formatting.
 *
 * REFERENCED BY:
 *     - Jest test runner
 *     - CI/CD pipeline
 *
 * REFERENCES:
 *     - utils/formatting.ts - Functions under test
 *
 * TEST CASES:
 *
 *     formatNumber:
 *         - 0 -> "0"
 *         - 999 -> "999"
 *         - 1000 -> "1K"
 *         - 1500 -> "1.5K"
 *         - 10000 -> "10K"
 *         - 1000000 -> "1M"
 *         - 1500000 -> "1.5M"
 *
 *     formatDuration:
 *         - 0 -> "0:00"
 *         - 5 -> "0:05"
 *         - 65 -> "1:05"
 *         - 3600 -> "1:00:00"
 *         - 3665 -> "1:01:05"
 *
 *     formatPercentage:
 *         - 0.5 -> "50%"
 *         - 0.956 -> "96%" (default 0 decimals)
 *         - 0.956, 1 -> "95.6%"
 *         - 1.0 -> "100%"
 *
 *     pluralize:
 *         - (0, "word") -> "words"
 *         - (1, "word") -> "word"
 *         - (2, "word") -> "words"
 *         - (1, "child", "children") -> "child"
 *         - (2, "child", "children") -> "children"
 *
 *     formatOrdinal:
 *         - 1 -> "1st"
 *         - 2 -> "2nd"
 *         - 3 -> "3rd"
 *         - 4 -> "4th"
 *         - 11 -> "11th"
 *         - 21 -> "21st"
 *         - 22 -> "22nd"
 *
 *     truncate:
 *         - ("hello", 10) -> "hello"
 *         - ("hello world", 8) -> "hello..."
 *         - ("hi", 2) -> "hi"
 */
