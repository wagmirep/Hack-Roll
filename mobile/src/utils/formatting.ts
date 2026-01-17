/**
 * formatting.ts - Display Formatting Utilities
 *
 * PURPOSE:
 *     Utility functions for formatting data for display.
 *     Handles numbers, dates, durations, and text.
 *
 * RESPONSIBILITIES:
 *     - Format large numbers (1000 -> 1K, 1000000 -> 1M)
 *     - Format durations (seconds -> MM:SS)
 *     - Format dates for display
 *     - Format percentages
 *     - Pluralize words correctly
 *
 * REFERENCED BY:
 *     - components/WordBadge.tsx - Count formatting
 *     - components/ProgressBar.tsx - Duration formatting
 *     - screens/ResultsScreen.tsx - Results formatting
 *     - screens/StatsScreen.tsx - Stats formatting
 *     - screens/WrappedScreen.tsx - Wrapped stats
 *
 * FUNCTIONS:
 *
 *     formatNumber(num: number): string
 *         Format number with K/M suffix
 *         Examples: 999 -> "999", 1500 -> "1.5K", 1000000 -> "1M"
 *
 *     formatDuration(seconds: number): string
 *         Format seconds as duration string
 *         Examples: 65 -> "1:05", 3600 -> "1:00:00"
 *
 *     formatDate(date: Date, format?: string): string
 *         Format date for display
 *         Default format: "MMM D, YYYY"
 *
 *     formatPercentage(value: number, decimals?: number): string
 *         Format decimal as percentage
 *         Examples: 0.95 -> "95%", 0.956 -> "95.6%"
 *
 *     pluralize(count: number, singular: string, plural?: string): string
 *         Return correctly pluralized word
 *         Examples: (1, "word") -> "word", (5, "word") -> "words"
 *
 *     formatOrdinal(num: number): string
 *         Format number as ordinal
 *         Examples: 1 -> "1st", 2 -> "2nd", 3 -> "3rd"
 *
 *     truncate(text: string, maxLength: number): string
 *         Truncate text with ellipsis
 */
