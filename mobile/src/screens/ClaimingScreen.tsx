/**
 * ClaimingScreen.tsx - Speaker Claiming Interface
 *
 * PURPOSE:
 *     Allow users to identify themselves by listening to audio samples.
 *     Maps anonymous SPEAKER_XX to actual user identities.
 *
 * RESPONSIBILITIES:
 *     - Fetch speaker data from backend
 *     - Display audio sample player for each speaker
 *     - Show word counts per speaker (preview)
 *     - Handle "That's me!" button clicks
 *     - Track which speakers have been claimed
 *     - Navigate to ResultsScreen when all claimed
 *
 * REFERENCED BY:
 *     - ProcessingScreen.tsx - Navigates here when processing complete
 *     - Navigation stack - Claiming step in flow
 *
 * REFERENCES:
 *     - hooks/useAudioPlayback.ts - Audio sample playback
 *     - api/client.ts - Fetch speakers, submit claims
 *     - components/SpeakerCard.tsx - Speaker display card
 *     - components/AudioPlayer.tsx - Playback controls
 *
 * USER FLOW:
 *     1. Arrives with sessionId, shows list of speakers
 *     2. Each speaker has: 5s audio sample, word count preview
 *     3. User plays sample, clicks "That's me!"
 *     4. Speaker card updates to show claimed status
 *     5. Other users in group claim other speakers
 *     6. When done, navigate to ResultsScreen
 *
 * PROPS:
 *     route.params.sessionId: string
 *     navigation: NavigationProp
 *
 * STATE:
 *     speakers: Speaker[] - List of speaker data
 *     claimedSpeakers: Map<speakerId, userId>
 *     playingId: string | null - Currently playing sample
 */
