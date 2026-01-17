/**
 * ProgressBar.tsx - Progress Indicator Component
 *
 * PURPOSE:
 *     Reusable progress bar for various progress displays.
 *     Used for recording duration, processing progress, etc.
 *
 * RESPONSIBILITIES:
 *     - Display visual progress bar
 *     - Show percentage or custom label
 *     - Animate progress changes smoothly
 *     - Support different color themes
 *
 * REFERENCED BY:
 *     - screens/RecordingScreen.tsx - Recording duration
 *     - screens/ProcessingScreen.tsx - Processing progress
 *     - components/AudioPlayer.tsx - Playback progress
 *
 * REFERENCES:
 *     - react-native Animated API - Smooth animations
 *
 * PROPS:
 *     progress: number - Progress value (0-1 or 0-100 based on mode)
 *     mode?: 'percentage' | 'fraction' - Display mode (default: percentage)
 *     label?: string - Custom label (overrides auto-generated)
 *     showLabel?: boolean - Whether to show label (default: true)
 *     color?: string - Bar color (default: theme primary)
 *     backgroundColor?: string - Track color
 *     height?: number - Bar height (default: 8)
 *     animated?: boolean - Enable smooth animation (default: true)
 *     style?: ViewStyle - Container style override
 *
 * VARIANTS:
 *     Recording: Shows elapsed time (MM:SS)
 *     Processing: Shows percentage (45%)
 *     Playback: Shows position/duration (0:03 / 0:05)
 *
 * ANIMATION:
 *     Uses Animated.timing for smooth progress updates
 *     Duration: 300ms
 *     Easing: ease-out
 */
