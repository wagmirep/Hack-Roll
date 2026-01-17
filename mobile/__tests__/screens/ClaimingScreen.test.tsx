/**
 * ClaimingScreen.test.tsx - Claiming Screen Tests
 *
 * PURPOSE:
 *     Test the ClaimingScreen component behavior.
 *     Covers speaker claiming flow.
 *
 * REFERENCED BY:
 *     - Jest test runner
 *     - CI/CD pipeline
 *
 * REFERENCES:
 *     - screens/ClaimingScreen.tsx - Component under test
 *     - api/client.ts - Mocked API
 *
 * TEST CASES:
 *
 *     renders_speaker_list:
 *         - Shows all speakers from API
 *         - Each has audio player and claim button
 *
 *     plays_audio_sample:
 *         - Press play on speaker card
 *         - Audio starts playing
 *         - Play button becomes pause
 *
 *     claims_speaker_on_button_press:
 *         - Press "That's me!" button
 *         - API claim endpoint called
 *         - Speaker marked as claimed
 *
 *     shows_claimed_status:
 *         - After claiming
 *         - Shows "You" badge on claimed speaker
 *         - Claim button disabled
 *
 *     shows_other_claims:
 *         - Other user claimed speaker
 *         - Shows their name
 *         - Card is disabled
 *
 *     prevents_double_claim:
 *         - User already claimed a speaker
 *         - Cannot claim another
 *         - Shows message
 *
 *     navigates_when_all_claimed:
 *         - All speakers claimed
 *         - Auto-navigates to ResultsScreen
 *
 *     handles_claim_error:
 *         - API returns error
 *         - Shows error message
 *         - Can retry
 *
 * MOCKS:
 *     - API client
 *     - Audio playback
 *     - Navigation
 */
