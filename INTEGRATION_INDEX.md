# Integration Documentation Index

**Quick navigation to all integration guides and documentation.**

---

## 🚀 START HERE

If you're new to the latest changes, read these documents **in order**:

1. **[WHATS_NEW.md](./WHATS_NEW.md)** ⭐ START HERE
   - Overview of what's been added
   - Quick summary of all new features
   - Integration checklist
   - Recommended priorities

2. **[QUICK_INTEGRATION_GUIDE.md](./QUICK_INTEGRATION_GUIDE.md)** 
   - Code examples for each feature
   - Step-by-step integration instructions
   - Estimated time for each task
   - Quick start guide (1 hour total)

3. **[INTEGRATION_MAP.md](./INTEGRATION_MAP.md)**
   - Visual architecture diagrams
   - Data flow illustrations
   - Before/after comparisons
   - Integration points explained

4. **[INTEGRATION_OPPORTUNITIES.md](./INTEGRATION_OPPORTUNITIES.md)**
   - Full technical details
   - Complete API documentation
   - Integration examples
   - Testing strategies

---

## 📚 BY FEATURE

### Transcription Service
- **Main Guide:** [QUICK_INTEGRATION_GUIDE.md#1-transcription-service](./QUICK_INTEGRATION_GUIDE.md#1-transcription-service-ready-now)
- **Code:** `backend/services/transcription.py`
- **Test:** `scripts/test_meralion.py`
- **Status:** ✅ Production ready
- **Time:** 30 minutes to integrate

### Session History API
- **Main Guide:** [QUICK_INTEGRATION_GUIDE.md#2-session-history-api](./QUICK_INTEGRATION_GUIDE.md#2-session-history-api-ready-now)
- **API Docs:** `backend/SESSION_HISTORY_API.md`
- **Code:** `backend/routers/sessions.py`
- **Test:** `backend/test_history_endpoints.py`
- **Status:** ✅ Backend complete
- **Time:** 15 minutes to integrate

### Global Leaderboard API
- **Main Guide:** [QUICK_INTEGRATION_GUIDE.md#3-global-leaderboard-api](./QUICK_INTEGRATION_GUIDE.md#3-global-leaderboard-api-ready-now)
- **Feature Guide:** `GLOBAL_LEADERBOARD_FEATURE.md`
- **Test Guide:** `TESTING_GLOBAL_LEADERBOARD.md`
- **Code:** `backend/routers/stats.py`
- **Status:** ✅ Backend complete
- **Time:** 15 minutes to integrate

### Three-Way Claiming System
- **Main Guide:** [QUICK_INTEGRATION_GUIDE.md#6-three-way-claiming](./QUICK_INTEGRATION_GUIDE.md#6-three-way-claiming-backend-ready)
- **Feature Guide:** `CLAIMING_FEATURE_GUIDE.md`
- **Code:** `backend/routers/sessions.py`, `backend/routers/auth.py`
- **Test:** `backend/test_claiming_flow.py`
- **Status:** ✅ Backend complete
- **Time:** 1 hour to integrate

### Team Recording Pipeline
- **Main Guide:** [QUICK_INTEGRATION_GUIDE.md#5-team-recording-pipeline](./QUICK_INTEGRATION_GUIDE.md#5-team-recording-pipeline-ready-to-start)
- **ML Guide:** `ml/README.md`
- **Workflow:** `ml/data/team_recordings/README.md`
- **Sentences:** `ml/data/sentence_templates.txt`
- **Script:** `ml/scripts/prepare_team_recordings.py`
- **Status:** ✅ Ready to use
- **Time:** 20 min/person + 30 min processing

---

## 📂 BY FILE TYPE

### Documentation Files

**Overview & Guides:**
- `WHATS_NEW.md` - Summary of latest changes ⭐
- `QUICK_INTEGRATION_GUIDE.md` - Quick start with code examples
- `INTEGRATION_MAP.md` - Visual architecture and data flow
- `INTEGRATION_OPPORTUNITIES.md` - Full integration details
- `INTEGRATION_INDEX.md` - This file

**Feature Guides:**
- `backend/SESSION_HISTORY_API.md` - Session history API documentation
- `GLOBAL_LEADERBOARD_FEATURE.md` - Global leaderboard feature guide
- `CLAIMING_FEATURE_GUIDE.md` - Three-way claiming system guide
- `TESTING_GLOBAL_LEADERBOARD.md` - Leaderboard testing guide

**ML Guides:**
- `ml/README.md` - ML pipeline overview and setup
- `ml/data/team_recordings/README.md` - Recording workflow
- `ml/data/sentence_templates.txt` - 90 sentences to record

**Project Docs:**
- `TASKS.md` - Task tracker and project status
- `CHANGELOG.md` - Detailed changelog
- `README.md` - Project overview

### Backend Files

**Services (Production Ready):**
- `backend/services/transcription.py` - MERaLiON transcription service ✅
- `backend/services/diarization.py` - Pyannote diarization service ✅

**Routers (Enhanced):**
- `backend/routers/sessions.py` - Session endpoints + history ✅
- `backend/routers/stats.py` - Stats endpoints + global leaderboard ✅
- `backend/routers/auth.py` - Auth endpoints + user search ✅

**Core (Needs Integration):**
- `backend/processor.py` - Audio processing pipeline ⏳

**Tests:**
- `backend/test_claiming_flow.py` - Claiming system tests
- `backend/test_history_endpoints.py` - History endpoint tests
- `scripts/test_meralion.py` - Transcription service test
- `scripts/test_pyannote.py` - Diarization service test

### Mobile Files (Need Updates)

**API Client:**
- `mobile/src/api/client.ts` - Add new API methods ⏳

**Screens:**
- `mobile/src/screens/StatsScreen.tsx` - Add history & global tabs ⏳
- `mobile/src/screens/ClaimingScreen.tsx` - Add 3-mode claiming ⏳
- `mobile/src/screens/ResultsScreen.tsx` - Display guests ⏳

### ML Files

**Scripts:**
- `ml/scripts/prepare_team_recordings.py` - Recording workflow ✅
- `ml/scripts/filter_imda.py` - Filter IMDA corpus ✅
- `ml/scripts/prepare_singlish_data.py` - Prepare training data ✅
- `ml/scripts/train_lora.py` - LoRA training (stub) ⏳

**Data:**
- `ml/data/sentence_templates.txt` - 90 Singlish sentences ✅
- `ml/data/team_recordings/` - Recording directory ✅

**Config:**
- `ml/configs/lora_config.yaml` - LoRA hyperparameters ✅
- `ml/configs/training_config.yaml` - Training settings ✅

---

## 🎯 BY PRIORITY

### Priority 1: Core ML (Blocking for MVP)

**Must integrate for app to work:**

1. **Connect Transcription Service** (30 min)
   - Guide: [QUICK_INTEGRATION_GUIDE.md](./QUICK_INTEGRATION_GUIDE.md)
   - File: `backend/processor.py`
   - Status: ⏳ Needs integration

2. **Test End-to-End** (1 hour)
   - Record → Upload → Process → Claim → Results
   - Verify transcription works
   - Check word counting

3. **Deploy Backend** (2 hours)
   - Set up GPU server
   - Deploy FastAPI
   - Configure environment

### Priority 2: Enhanced UX (High value, low effort)

**Easy wins that improve user experience:**

1. **Session History** (15 min)
   - Guide: [QUICK_INTEGRATION_GUIDE.md#2](./QUICK_INTEGRATION_GUIDE.md#2-session-history-api-ready-now)
   - Files: `mobile/src/api/client.ts`, `mobile/src/screens/StatsScreen.tsx`
   - Status: ⏳ Needs mobile UI

2. **Global Leaderboard** (15 min)
   - Guide: [QUICK_INTEGRATION_GUIDE.md#3](./QUICK_INTEGRATION_GUIDE.md#3-global-leaderboard-api-ready-now)
   - Files: `mobile/src/api/client.ts`, `mobile/src/screens/StatsScreen.tsx`
   - Status: ⏳ Needs mobile UI

3. **Enhanced Claiming** (1 hour)
   - Guide: [QUICK_INTEGRATION_GUIDE.md#6](./QUICK_INTEGRATION_GUIDE.md#6-three-way-claiming-backend-ready)
   - File: `mobile/src/screens/ClaimingScreen.tsx`
   - Status: ⏳ Needs mobile UI

### Priority 3: Model Improvement (Long-term quality)

**Optional but improves ASR accuracy:**

1. **Record Training Data** (20 min/person)
   - Guide: [ml/data/team_recordings/README.md](./ml/data/team_recordings/README.md)
   - Sentences: [ml/data/sentence_templates.txt](./ml/data/sentence_templates.txt)
   - Status: ✅ Ready to start

2. **Process Recordings** (30 min)
   - Script: `ml/scripts/prepare_team_recordings.py`
   - Status: ✅ Ready to use

3. **Implement Training** (1-2 days)
   - Script: `ml/scripts/train_lora.py`
   - Status: ⏳ Needs implementation

---

## 🔍 QUICK REFERENCE

### API Endpoints (New/Enhanced)

```
GET  /sessions/history                    # Session history
GET  /stats/global/leaderboard            # Global leaderboard
GET  /auth/search                         # User search
POST /sessions/{id}/claim                 # Enhanced claiming
```

### Key Functions (Backend)

```python
# Transcription
from services.transcription import process_transcription
result = process_transcription("audio.wav")

# Diarization
from services.diarization import diarize_audio
segments = diarize_audio("audio.wav")
```

### Key Components (Mobile)

```typescript
// API Client
getSessionHistory(period, limit)
getGlobalLeaderboard(period, limit)
searchUsers(query, groupId, limit)

// Screens
StatsScreen.tsx    // Add history & global tabs
ClaimingScreen.tsx // Add 3-mode claiming
```

### Key Scripts (ML)

```bash
# Test transcription
python scripts/test_meralion.py

# Record training data
python ml/scripts/prepare_team_recordings.py --auto-transcribe
python ml/scripts/prepare_team_recordings.py --process
```

---

## 📊 STATUS OVERVIEW

### ✅ Complete (Ready to Use)
- Transcription service
- Session history API
- Global leaderboard API
- User search API
- Enhanced claiming API
- Team recording pipeline
- GPU compatibility fixes

### ⏳ In Progress (Needs Work)
- Backend processor integration
- Mobile UI updates
- LoRA training script
- End-to-end testing

### ❌ Not Started
- Model fine-tuning
- Production deployment
- Performance optimization

---

## 💡 TIPS

### For Backend Developers
1. Start with transcription integration in `processor.py`
2. Test with `scripts/test_meralion.py`
3. Check GPU memory with `nvidia-smi`
4. Review test files for API usage examples

### For Mobile Developers
1. Start with session history (easiest)
2. Then add global leaderboard
3. Finally enhance claiming screen
4. Test with Postman/curl first

### For ML Engineers
1. Record team training data first
2. Process while building other features
3. Implement training script when data is ready
4. Fine-tune on GPU server

---

## 🆘 TROUBLESHOOTING

### Can't find a file?
- Check the file paths in this index
- Use `find` command: `find . -name "filename.py"`
- Check `.gitignore` for excluded files

### API not working?
- Check `backend/.env` for credentials
- Verify backend is running: `curl http://localhost:8000/health`
- Check logs: `tail -f backend/logs/app.log`

### GPU issues?
- Check CUDA: `nvidia-smi`
- Check PyTorch: `python -c "import torch; print(torch.cuda.is_available())"`
- See `ml/README.md` for GPU setup

### Mobile errors?
- Check `mobile/.env` for API URL
- Verify network connectivity
- Check browser console for errors

---

## 📞 NEED HELP?

1. **Check the guides** - Start with `WHATS_NEW.md`
2. **Review the code** - Services have detailed docstrings
3. **Run the tests** - See `backend/test_*.py` for examples
4. **Check commit history** - `git log --oneline -20`

---

## 🔗 EXTERNAL RESOURCES

### Models
- [MERaLiON-2-10B-ASR](https://huggingface.co/MERaLiON/MERaLiON-2-10B-ASR) - Singlish ASR model
- [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1) - Speaker diarization

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Native Docs](https://reactnative.dev/)
- [Supabase Docs](https://supabase.com/docs)
- [LoRA Paper](https://arxiv.org/abs/2106.09685)

---

**Last Updated:** January 17, 2026  
**Version:** 1.0  
**Commits:** 26050a0 → 271c620

---

*This index is your central hub for all integration documentation. Bookmark it!*
