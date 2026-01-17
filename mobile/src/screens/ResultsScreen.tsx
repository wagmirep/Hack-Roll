/**
 * ResultsScreen.tsx - Session Results Display
 *
 * PURPOSE:
 *     Show word count results for the just-completed session.
 *     Displays per-user breakdown of Singlish words detected.
 *
 * RESPONSIBILITIES:
 *     - Fetch final word counts from backend
 *     - Display results grouped by user
 *     - Show word badges with counts
 *     - Provide sharing functionality
 *     - Navigate to StatsScreen for overall stats
 *
 * REFERENCED BY:
 *     - ClaimingScreen.tsx - Navigates here after all claims
 *     - Navigation stack - Results step in flow
 *
 * REFERENCES:
 *     - api/client.ts - Fetch session results
 *     - components/WordBadge.tsx - Word count badges
 *     - utils/formatting.ts - Number formatting
 *
 * USER FLOW:
 *     1. Arrives after claiming complete
 *     2. Shows session summary:
 *        "Jeff: walao (10), lah (15)"
 *        "Alice: sia (8), lor (14)"
 *     3. User can share results
 *     4. User can view overall stats (StatsScreen)
 *     5. User can start new recording
 *
 * PROPS:
 *     route.params.sessionId: string
 *     navigation: NavigationProp
 *
 * STATE:
 *     results: UserResult[] - Per-user word counts
 *     loading: boolean
 *     error: string | null
 *
 * TYPES:
 *     UserResult: {
 *         userId: string
 *         userName: string
 *         words: { word: string, count: number }[]
 *         totalWords: number
 *     }
 */
