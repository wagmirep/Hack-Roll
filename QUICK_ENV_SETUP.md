# 🚀 Quick Environment Setup

## What You Need

All credentials come from your Supabase dashboard:
👉 **https://app.supabase.com/project/tamrgxhjyabdvtubseyu/settings/api**

---

## Setup Instructions

### 1️⃣ Backend Setup

```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/backend

# Copy the example file
cp env.example .env

# Edit it with your credentials
nano .env  # or code .env, or vim .env
```

**Fill in these 4 values:**

| Variable | Where to Find It |
|----------|------------------|
| `SUPABASE_URL` | ✅ Already filled: `https://tamrgxhjyabdvtubseyu.supabase.co` |
| `SUPABASE_JWT_SECRET` | Settings → API → JWT Settings → **JWT Secret** |
| `SUPABASE_SERVICE_ROLE_KEY` | Settings → API → Project API keys → **service_role (secret)** |
| `DATABASE_URL` | Settings → Database → Get your password, then fill in the URL |

---

### 2️⃣ Mobile Setup

```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/mobile

# Copy the example file
cp env.example .env

# Edit it with your credentials
nano .env  # or code .env, or vim .env
```

**Fill in these 3 values:**

| Variable | Where to Find It |
|----------|------------------|
| `EXPO_PUBLIC_SUPABASE_URL` | ✅ Already filled: `https://tamrgxhjyabdvtubseyu.supabase.co` |
| `EXPO_PUBLIC_SUPABASE_ANON_KEY` | Settings → API → Project API keys → **anon (public)** ⚠️ NOT service_role! |
| `EXPO_PUBLIC_API_URL` | ✅ Already filled: `http://localhost:8000` (for local dev) |

---

## 3️⃣ Start Everything

### Terminal 1 - Backend:
```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Expected output:**
```
✅ Configuration loaded successfully
✅ Database connection successful
✅ Application startup complete
```

### Terminal 2 - Mobile:
```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/mobile
npm start
```

---

## 🔑 Credentials Cheat Sheet

Go to: **https://app.supabase.com/project/tamrgxhjyabdvtubseyu/settings/api**

You'll need to copy **3 different keys**:

### For Backend (.env):
1. **JWT Secret** (in "JWT Settings" section)
   - Used to decode JWT tokens
   - Example: `super-secret-jwt-token-with-at-least-32-characters-long`

2. **Service Role Key** (in "Project API keys" section)
   - Starts with: `eyJhbGci...`
   - This is the **secret** one, not public!
   - Used for admin operations

3. **Database Password** (Settings → Database)
   - Your PostgreSQL password
   - Set during Supabase project creation

### For Mobile (.env):
1. **Anon Key** (in "Project API keys" section)
   - Starts with: `eyJhbGci...`
   - This is the **public** one!
   - Different from service_role key

---

## ✅ Verify Setup

### Test Backend:
```bash
curl http://localhost:8000/docs
```
Should open FastAPI documentation in your browser.

### Test Mobile:
Open the app and try to:
1. Sign up with a new account
2. Sign in
3. Check that you don't see any "401 Unauthorized" errors

---

## 🆘 Troubleshooting

**Backend won't start?**
- Check `.env` file exists in backend directory: `ls -la backend/.env`
- Check no typos in variable names
- Make sure no extra spaces around the `=` signs

**Mobile can't connect?**
- Restart the Expo dev server after editing `.env`
- Try `npm start --clear` to clear cache
- Check backend is running on port 8000

**Still getting 401 errors?**
- Double-check you copied the **anon** key for mobile (not service_role)
- Double-check you copied the **JWT secret** correctly for backend
- Make sure both use the same Supabase project URL

---

## 📁 Files Created

- ✅ `backend/env.example` - Backend environment template
- ✅ `mobile/env.example` - Mobile environment template
- ✅ `backend/ENV_SETUP_GUIDE.md` - Detailed setup guide
- ✅ `AUTHENTICATION_DEBUG_SUMMARY.md` - Complete auth troubleshooting

**Note:** The actual `.env` files are in `.gitignore` and won't be committed to git (they contain secrets!).
