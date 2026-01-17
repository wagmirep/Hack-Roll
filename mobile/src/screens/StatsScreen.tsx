/**
 * StatsScreen.tsx - Weekly/Monthly Statistics
 *
 * PURPOSE:
 *     Display aggregated statistics over time.
 *     Shows trends, leaderboards, and historical data.
 *
 * RESPONSIBILITIES:
 *     - Fetch group statistics from backend
 *     - Display time-period selector (week/month/all-time)
 *     - Show word leaderboards
 *     - Display personal stats and trends
 *     - Visualize word usage over time
 *
 * REFERENCED BY:
 *     - ResultsScreen.tsx - "View Stats" button
 *     - Bottom tab navigation - Stats tab
 *     - Navigation stack
 *
 * REFERENCES:
 *     - api/client.ts - Fetch group stats
 *     - components/WordBadge.tsx - Word display
 *     - utils/formatting.ts - Number formatting
 *
 * FEATURES:
 *     - Period selector: This Week | This Month | All Time
 *     - Personal stats: Your top words, total count
 *     - Group leaderboard: Who says what the most
 *     - Trends: Word usage over time (if time permits)
 *
 * PROPS:
 *     route.params.groupId?: string - Optional group filter
 *     navigation: NavigationProp
 *
 * STATE:
 *     period: 'week' | 'month' | 'all'
 *     stats: GroupStats
 *     loading: boolean
 *
 * TYPES:
 *     GroupStats: {
 *         userStats: Map<userId, WordCounts>
 *         leaderboard: LeaderboardEntry[]
 *         totalSessions: number
 *         dateRange: { start: Date, end: Date }
 *     }
 */
