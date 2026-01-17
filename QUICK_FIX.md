# QUICK FIX: HuggingFace Token Required

## TL;DR

✅ **FFmpeg issue FIXED** - Audio chunks are concatenating successfully!

❌ **NEW issue**: Missing HuggingFace token for speaker diarization

## What's Working Now

Looking at your worker logs:
- ✅ Redis connection: Working
- ✅ Database connection: Working  
- ✅ FFmpeg: **NOW WORKING!** (audio chunks downloading and concatenating)
- ✅ Audio concatenation: **65.4 seconds of audio successfully processed**
- ❌ Speaker diarization: Blocked by missing token

## The Problem

The pyannote speaker diarization model requires a HuggingFace token to access the model. This is a required authentication step.

**Error in your logs (line 190):**
```
HUGGINGFACE_TOKEN environment variable is required. 
Get your token from https://huggingface.co/settings/tokens 
and accept the pyannote model terms.
```

## The Solution (5 minutes)

### Step 1: Get HuggingFace Token

1. Go to: **https://huggingface.co/settings/tokens**
2. Click **"New token"**
3. Name: `hacknroll` (or whatever)
4. Type: **Read** access
5. Click **"Generate token"**
6. **Copy the token** (starts with `hf_...`)

### Step 2: Accept Model Terms

1. Go to: **https://huggingface.co/pyannote/speaker-diarization-3.1**
2. Click **"Agree and access repository"**
   - You must be logged into HuggingFace
   - This gives you permission to use the model

### Step 3: Add Token to `.env`

1. Open: `/Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/backend/.env`
2. Find line 30:
   ```bash
   # HUGGINGFACE_TOKEN=your-huggingface-token-here
   ```
3. Change to (with YOUR token):
   ```bash
   HUGGINGFACE_TOKEN=hf_your_actual_token_here
   ```
4. Save the file

### Step 4: Restart Worker

In **Terminal 11** (where worker is running):
1. Press `Ctrl+C` to stop the worker
2. Run: `python worker.py`

## What Will Happen Next

When you restart the worker:
1. It will detect the token
2. On **first run**, it will **download the pyannote model** (~500MB)
   - This will take **2-5 minutes** depending on your internet
   - You'll see download progress in the logs
3. After download, it will start processing the queued audio
4. Speaker diarization will run successfully

## Summary of Issues & Status

| Issue | Status | Solution |
|-------|--------|----------|
| FFmpeg missing | ✅ FIXED | Installed FFmpeg 8.0.1 |
| Audio chunks failing | ✅ FIXED | FFmpeg now converts WebM to WAV |
| Audio concatenation | ✅ WORKING | Successfully concatenated 65.4s |
| HuggingFace token | ❌ MISSING | **YOU NEED TO ADD THIS NOW** |
| Speaker diarization | ⏸️ BLOCKED | Waiting for token |

## After You Fix This

Once the token is added and the model downloads, the full pipeline will work:
1. ✅ Audio chunks upload to Supabase
2. ✅ Worker downloads chunks
3. ✅ FFmpeg converts WebM → WAV
4. ✅ Chunks concatenate into single audio file
5. ✅ Speaker diarization identifies speakers
6. ✅ MERaLiON transcribes speech
7. ✅ Singlish words counted per speaker
8. ✅ Results saved to database
9. ✅ Frontend displays wrapped screen

---

**Go get that token and restart the worker!** 🚀
