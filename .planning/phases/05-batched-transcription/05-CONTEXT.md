# Phase 5: Batched Transcription - Context

**Gathered:** 2026-01-18
**Status:** Ready for research

<vision>
## How This Should Work

During recording, transcription happens invisibly in the background — the user doesn't see anything different. Every few seconds, audio chunks are sent off for transcription while recording continues.

When the user stops recording, most of the audio has already been transcribed. They only wait for the final chunk to process, plus diarization. Instead of waiting 60-120 seconds after a 1-2 minute recording, they wait maybe 5-10 seconds.

The recording UI stays exactly the same. No live captions, no progress indicators during recording. The magic happens behind the scenes. When they stop, there's a brief "finalizing" moment, then results are ready.

</vision>

<essential>
## What Must Be Nailed

- **Seamless feel** — Stopping the recording should feel responsive, not like starting a long processing job
- **No accuracy degradation** — Batching shouldn't noticeably hurt transcription quality compared to processing the full audio
- **Demo polish** — For the hackathon demo, avoid the awkward 60+ second wait that kills momentum

</essential>

<boundaries>
## What's Out of Scope

- **No live captions** — Not showing real-time text during recording
- **No diarization changes** — Diarization still runs on full audio after recording ends, same as before
- **Not optimizing for very long recordings** — Focus is on 1-2 minute demo scenarios

</boundaries>

<specifics>
## Specific Ideas

- Chunk boundaries should be smart (detect natural pauses) rather than cutting at arbitrary time marks — avoids splitting words
- Alternative: slightly longer chunks (8-10s) if that reduces boundary issues
- Post-processing corrections might catch some boundary artifacts anyway

</specifics>

<notes>
## Additional Context

Primary motivation is **hackathon demo polish**. The current 1:1 ratio (60s audio = 60s wait) creates an awkward pause during demos. With batched transcription, a 1-2 minute conversation should feel nearly instant to process.

User is concerned about accuracy degradation from batching. Research should investigate:
- Voice Activity Detection (VAD) for smarter chunk boundaries
- Optimal chunk size tradeoffs
- Whether post-processing can mitigate boundary artifacts

</notes>

---

*Phase: 05-batched-transcription*
*Context gathered: 2026-01-18*
