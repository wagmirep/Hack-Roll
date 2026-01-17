# Codebase Concerns

**Analysis Date:** 2026-01-18

## Tech Debt

**PyTorch 2.6 Compatibility Workaround:**
- Issue: Monkey-patching `torch.load` to set `weights_only=False` for pyannote compatibility
- File: `backend/services/diarization.py` (lines 52-71)
- Why: PyTorch 2.6 changed default behavior, breaking pyannote model loading
- Impact: Reduces security benefits of new PyTorch defaults
- Fix approach: Wait for pyannote to update, then remove patch

**Test Files in Backend Root:**
- Issue: Multiple test scripts in `backend/` root instead of `backend/tests/`
- Files: `backend/test_api.py`, `backend/test_ml_pipeline.py`, `backend/test_claiming_flow.py`, `backend/test_history_endpoints.py`, `backend/quick_test.py`, etc.
- Why: Quick development testing during hackathon
- Impact: Cluttered directory, inconsistent test organization
- Fix approach: Move relevant tests to `backend/tests/`, delete ad-hoc scripts

**Hardcoded Database URL Construction:**
- Issue: DATABASE_URL constructed from SUPABASE_URL with hardcoded pattern
- File: `backend/config.py` (lines 66-74)
- Why: Quick setup during hackathon
- Impact: May break with different Supabase configurations
- Fix approach: Require explicit DATABASE_URL or validate construction

## Known Bugs

**No Critical Bugs Detected**

The codebase appears stable based on analysis. Known limitations are documented in `CLAUDE.md`:
- Speaker diarization ~85% accuracy
- No voice enrollment (manual claiming required)
- 30s chunk upload (not true real-time)
- Requires quiet environment

## Security Considerations

**CORS Wildcard in Development:**
- Risk: `"*"` allows all origins in CORS config
- File: `backend/config.py` (line 39)
- Current mitigation: Listed as development setting
- Recommendations: Remove `"*"` before production, explicit origin list only

**JWT Secret Validation:**
- Risk: Server starts even if JWT secret is weak/empty (only checks if set)
- File: `backend/config.py` (lines 81-84)
- Current mitigation: Validation raises ValueError if missing
- Recommendations: Add minimum length/entropy check for production

**HuggingFace Token Exposure:**
- Risk: Token stored in .env could be committed accidentally
- File: Environment variable `HUGGINGFACE_TOKEN`
- Current mitigation: `.gitignore` includes `.env`
- Recommendations: Add pre-commit hook to check for secrets

## Performance Bottlenecks

**ML Model Loading Time:**
- Problem: First transcription/diarization request loads large models
- Files: `backend/services/transcription.py`, `backend/services/diarization.py`
- Measurement: ~30-60 seconds to load models on CPU
- Cause: Singleton pattern loads on first use, not at startup
- Improvement path: Pre-load models on startup (add to `startup_event` in `main.py`)

**CPU Transcription Speed:**
- Problem: MERaLiON inference slow on CPU
- File: `backend/services/transcription.py`
- Measurement: ~10x real-time (10 minutes to transcribe 1 minute)
- Cause: Large transformer model on CPU
- Improvement path: Use GPU, or use external API (`TRANSCRIPTION_API_URL`)

**Sequential Chunk Download:**
- Problem: Audio chunks downloaded and processed sequentially
- File: `backend/processor.py` (lines 243-283)
- Measurement: Linear with chunk count
- Cause: Loop with await for each chunk
- Improvement path: Parallel download with `asyncio.gather()`

## Fragile Areas

**Diarization Service Patching:**
- File: `backend/services/diarization.py`
- Why fragile: Multiple monkey patches for PyTorch compatibility
- Common failures: New PyTorch versions may break patches
- Safe modification: Test with multiple torch versions before changing
- Test coverage: Limited (model loading not easily testable)

**Audio Processing Pipeline:**
- File: `backend/processor.py`
- Why fragile: Long orchestration function with multiple stages
- Common failures: Any stage failure requires understanding full pipeline
- Safe modification: Ensure tests mock each stage independently
- Test coverage: Integration tests exist but depend on many mocks

## Scaling Limits

**Memory Usage:**
- Current capacity: ~8-16GB RAM for both models loaded
- Limit: OOM if running transcription and diarization concurrently
- Symptoms at limit: Process killed, no graceful degradation
- Scaling path: Use external API for transcription, or dedicated GPU server

**Concurrent Transcriptions:**
- Current capacity: 3 concurrent (semaphore in `processor.py` line 430)
- Limit: OOM with more parallel transcriptions
- Symptoms at limit: Memory exhaustion
- Scaling path: Queue with worker pool, external transcription service

## Dependencies at Risk

**pyannote.audio:**
- Risk: Requires PyTorch compatibility patches, may break with updates
- Impact: Speaker diarization completely fails
- Migration plan: Monitor pyannote releases, test PyTorch updates carefully

**MERaLiON Model:**
- Risk: HuggingFace model availability depends on maintainer
- Impact: Transcription fails if model removed
- Migration plan: Keep local model cache, consider model backup

## Missing Critical Features

**No Automated Testing for Mobile:**
- Problem: React Native app has no test files
- Current workaround: Manual testing
- Blocks: Can't safely refactor mobile code
- Implementation complexity: Medium (Jest + Testing Library setup)

**No Error Recovery for Processing:**
- Problem: Failed processing sessions stay in "failed" state
- Current workaround: Manual database updates
- Blocks: Users can't retry failed sessions
- Implementation complexity: Low (add retry endpoint)

**No Rate Limiting:**
- Problem: No protection against API abuse
- Current workaround: None
- Blocks: Production deployment without protection
- Implementation complexity: Low (add FastAPI middleware)

## Test Coverage Gaps

**Mobile App (No Tests):**
- What's not tested: All React Native screens and hooks
- Risk: Regressions undetected during changes
- Priority: Medium
- Difficulty to test: Medium (requires Jest + RNTL setup)

**Audio Processing E2E:**
- What's not tested: Full pipeline with real audio
- Risk: Integration issues between diarization and transcription
- Priority: High
- Difficulty to test: High (requires audio fixtures, slow tests)

**Supabase Integration:**
- What's not tested: Actual Supabase storage/auth
- Risk: Configuration issues in production
- Priority: Medium
- Difficulty to test: Medium (requires test Supabase project)

## Documentation Gaps

**API Documentation:**
- What's missing: No OpenAPI descriptions on endpoints
- File: `backend/routers/*.py`
- Impact: Auto-generated docs less useful
- Fix: Add docstrings to route functions

**Environment Setup:**
- What's missing: No `.env.example` file
- Impact: New developers must discover required vars
- Fix: Create `.env.example` with dummy values

---

*Concerns audit: 2026-01-18*
*Update as issues are fixed or new ones discovered*
