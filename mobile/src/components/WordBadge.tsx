/**
 * WordBadge.tsx - Singlish Word Display Badge
 *
 * PURPOSE:
 *     Display a Singlish word with its count in a styled badge.
 *     Visual indicator of word usage.
 *
 * RESPONSIBILITIES:
 *     - Display word text
 *     - Show count with formatting
 *     - Apply color coding based on word category
 *     - Handle different sizes (small/medium/large)
 *
 * REFERENCED BY:
 *     - screens/ResultsScreen.tsx - Show word counts
 *     - screens/StatsScreen.tsx - Statistics display
 *     - screens/WrappedScreen.tsx - Wrapped cards
 *     - components/SpeakerCard.tsx - Preview counts
 *
 * REFERENCES:
 *     - utils/formatting.ts - Number formatting
 *
 * PROPS:
 *     word: string - The Singlish word (e.g., 'walao', 'lah')
 *     count: number - Number of occurrences
 *     size?: 'small' | 'medium' | 'large' - Badge size (default: medium)
 *     showCount?: boolean - Whether to show count (default: true)
 *     style?: ViewStyle - Container style override
 *
 * COLOR CODING:
 *     Vulgar (walao, cheebai, lanjiao): Red/pink tones
 *     Particles (lah, lor, sia, meh): Blue tones
 *     Colloquial (can, paiseh, shiok, sian): Green tones
 *
 * VARIANTS:
 *     Small: Compact, inline use
 *     Medium: Default, card use
 *     Large: Wrapped screen, hero display
 */
