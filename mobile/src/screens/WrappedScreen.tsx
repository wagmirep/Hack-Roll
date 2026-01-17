/**
 * WrappedScreen.tsx - Spotify Wrapped-Style Yearly Recap
 *
 * PURPOSE:
 *     Fun, shareable yearly statistics in Spotify Wrapped style.
 *     Animated, visually engaging summary of Singlish usage.
 *
 * RESPONSIBILITIES:
 *     - Fetch yearly wrapped data from backend
 *     - Display animated statistics cards
 *     - Show fun facts and insights
 *     - Provide sharing functionality (screenshot/export)
 *     - Create memorable, shareable experience
 *
 * REFERENCED BY:
 *     - StatsScreen.tsx - "View Your Wrapped" button
 *     - Push notification - Annual wrapped reminder
 *     - Navigation stack
 *
 * REFERENCES:
 *     - api/client.ts - Fetch wrapped data
 *     - utils/formatting.ts - Number formatting
 *
 * FEATURES:
 *     - Animated card transitions
 *     - "You said 'lah' 2,847 times this year"
 *     - "That's more than 95% of users!"
 *     - "Your signature word: walao"
 *     - "Peak Singlish day: December 15"
 *     - Share button for social media
 *
 * ANIMATION SEQUENCE:
 *     1. Intro card: "Your 2024 Wrapped"
 *     2. Total words card
 *     3. Top word card (with big animation)
 *     4. Percentile card
 *     5. Fun facts cards
 *     6. Share card
 *
 * PROPS:
 *     route.params.year?: number - Default current year
 *     route.params.userId?: string
 *     navigation: NavigationProp
 *
 * STATE:
 *     wrappedData: WrappedData
 *     currentCard: number
 *     loading: boolean
 *
 * TYPES:
 *     WrappedData: {
 *         topWords: { word: string, count: number }[]
 *         totalWords: number
 *         favoriteWord: string
 *         percentile: number
 *         funFacts: string[]
 *         peakDay: Date
 *     }
 */
