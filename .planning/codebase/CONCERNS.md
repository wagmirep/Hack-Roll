# Codebase Concerns

**Analysis Date:** 2026-01-17

## Tech Debt

**Placeholder File Structure:**
- Issue: Most source files contain only header docstrings with no implementation
- Files: All files in `backend/`, `mobile/src/`, `ml/scripts/`
- Why: Scaffolded structure for hackathon, implementation pending
- Impact: No working application yet - all features need to be built
- Fix approach: Implement each file according to its documented PURPOSE and RESPONSIBILITIES

**Requirements.txt Commented Out:**
- Issue: All dependencies in `backend/requirements.txt` and `ml/requirements.txt` are commented out
- Files: `backend/requirements.txt`, `ml/requirements.txt`
- Why: Placeholder structure
- Impact: `pip install -r requirements.txt` installs nothing
- Fix approach: Uncomment dependencies when implementing

**package.json Structure:**
- Issue: `mobile/package.json` contains only comments and structure hints, not valid JSON
- File: `mobile/package.json`
- Why: Placeholder for documentation
- Impact: `bun install` or `npm install` will fail
- Fix approach: Replace with actual package.json during mobile implementation

## Known Bugs

**None documented** - Codebase is in placeholder state with no implementation to have bugs yet.

## Security Considerations

**No Authentication Implementation:**
- Risk: User IDs passed as parameters without verification
- Files: `backend/routers/sessions.py` (all endpoints accept user_id without auth)
- Current mitigation: None
- Recommendations: Add Firebase Auth verification or JWT tokens before production

**HuggingFace Token Exposure:**
- Risk: Token could be exposed if committed
- File: `backend/.env.example` (template only)
- Current mitigation: .env is gitignored
- Recommendations: Ensure `.env` never committed, use secrets management in production

**S3 Credentials:**
- Risk: AWS credentials could be exposed
- File: `backend/.env.example`
- Current mitigation: .env is gitignored
- Recommendations: Use IAM roles in production, not static credentials

## Performance Bottlenecks

**ML Model Loading:**
- Problem: MERaLiON and pyannote models are large, slow to load
- Files: `backend/services/transcription.py`, `backend/services/diarization.py`
- Cause: Models loaded on first request
- Improvement path: Pre-load models on worker startup, cache instances

**Processing Pipeline Sequential:**
- Problem: Audio processing is sequential (diarize → transcribe each segment)
- File: `backend/processor.py`
- Cause: Design choice for simplicity
- Improvement path: Parallelize segment transcription after diarization

## Fragile Areas

**Post-Processing Corrections:**
- Files: `backend/processor.py`, `backend/services/transcription.py`
- Why fragile: Corrections dictionary requires manual maintenance, edge cases easy to miss
- Common failures: New Singlish words not recognized, false positives
- Safe modification: Add comprehensive tests before changing corrections
- Test coverage: `backend/tests/test_word_counting.py` (placeholder)

**Chunk Upload/Concatenation:**
- Files: `backend/storage.py`, `backend/processor.py`
- Why fragile: Depends on consistent chunk ordering and format
- Common failures: Missing chunks, incorrect ordering, format mismatches
- Safe modification: Add validation, checksum verification
- Test coverage: Needs integration tests

## Scaling Limits

**Single Worker Processing:**
- Current capacity: One session processed at a time per worker
- Limit: Queue backup during high usage
- Symptoms at limit: Long processing wait times
- Scaling path: Multiple workers, horizontal scaling

**In-Memory Model Loading:**
- Current capacity: GPU memory limits concurrent model use
- Limit: OOM errors with multiple large models
- Scaling path: Model quantization, separate model servers

## Dependencies at Risk

**pyannote.audio:**
- Risk: Requires HuggingFace agreement acceptance, license restrictions
- Impact: Cannot use without accepting terms
- Mitigation: Document agreement requirement in setup instructions

**MERaLiON Model:**
- Risk: Large model (~10B parameters), requires significant resources
- Impact: May need GPU with significant VRAM
- Mitigation: Document hardware requirements, consider smaller model for development

## Missing Critical Features

**Authentication:**
- Problem: No user authentication implemented
- Current workaround: User IDs passed as parameters
- Blocks: Production deployment, security
- Implementation complexity: Medium (add Firebase Auth verification)

**Group Management:**
- Problem: No group creation/management endpoints
- Current workaround: Group IDs assumed to exist
- Blocks: Full user flow
- Implementation complexity: Low (add group CRUD endpoints)

**Error Recovery:**
- Problem: No retry mechanism for failed processing
- Current workaround: Manual re-trigger
- Blocks: Reliable production operation
- Implementation complexity: Medium (add job retry logic)

## Test Coverage Gaps

**All Files Need Implementation:**
- What's not tested: Everything - files are placeholders
- Risk: No verification that code works
- Priority: High - implement tests alongside features
- Difficulty: Tests can be written as features are built

**Integration Testing:**
- What's not tested: Full flow from recording to claiming
- Risk: Components may not work together
- Priority: High
- Difficulty: Need mock services and test fixtures

## Documentation Gaps

**Setup Instructions Incomplete:**
- Problem: No step-by-step setup guide
- Files: `README.md` is brief
- Impact: Onboarding difficulty
- Fix: Add detailed setup instructions

---

*Concerns audit: 2026-01-17*
*Update as issues are fixed or new ones discovered*

## Notes

This is a **scaffolded hackathon project** - the codebase contains well-documented placeholder files awaiting implementation. The concerns above reflect both the placeholder state and anticipated issues once implementation begins.

**Priority for Hackathon:**
1. Implement core backend files (main.py, processor.py, services/*)
2. Implement mobile recording and claiming flow
3. Add basic tests for critical paths
4. Defer authentication and scaling concerns
