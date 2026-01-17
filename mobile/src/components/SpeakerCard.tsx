/**
 * SpeakerCard.tsx - Speaker Claiming Card
 *
 * PURPOSE:
 *     Display a speaker's information for claiming.
 *     Shows audio sample player, word preview, and claim button.
 *
 * RESPONSIBILITIES:
 *     - Display speaker identifier (Speaker A, B, C...)
 *     - Embed AudioPlayer for sample playback
 *     - Show word count preview (top 3 words)
 *     - Display "That's me!" claim button
 *     - Show claimed status if already claimed
 *     - Disable interaction for claimed speakers
 *
 * REFERENCED BY:
 *     - screens/ClaimingScreen.tsx - List of speakers
 *
 * REFERENCES:
 *     - components/AudioPlayer.tsx - Sample playback
 *     - components/WordBadge.tsx - Word preview
 *     - api/client.ts - Claim submission
 *
 * PROPS:
 *     speaker: Speaker - Speaker data object
 *     onClaim: (speakerId: string) => void - Claim handler
 *     isClaiming?: boolean - Show loading state
 *     disabled?: boolean - Disable interaction
 *     style?: ViewStyle - Container style override
 *
 * TYPES:
 *     Speaker: {
 *         speakerId: string - 'SPEAKER_00', 'SPEAKER_01'
 *         displayName: string - 'Speaker A', 'Speaker B'
 *         sampleAudioUrl: string
 *         totalWords: { word: string, count: number }[]
 *         claimedBy: string | null
 *         claimedByName: string | null
 *     }
 *
 * UI STATES:
 *     Unclaimed: Show audio player + "That's me!" button
 *     Claiming: Show loading spinner
 *     Claimed by me: Show "You" badge, green checkmark
 *     Claimed by other: Show claimer name, disabled state
 */
