# 🔑 Credentials Checklist - What You Need

**Quick reference for Supabase credentials needed to complete setup**

---

## 📋 Credentials You Need to Get

### For Database Migration (Choose One Method)

#### ✅ EASY: SQL Editor Method
- **Required:** Just login to Supabase dashboard
- **URL:** https://app.supabase.com/project/tamrgxhjyabdvtubseyu

#### Advanced: Direct psql Method
- **Required:** Database password
- **Where:** Project Settings → Database → "Database password"

---

## 🔑 Required API Keys & Secrets

### 1. Supabase Anon Key (Public)
**Needed for:** Mobile app authentication  
**File:** `mobile/.env`  
**Variable:** `EXPO_PUBLIC_SUPABASE_ANON_KEY`

**Where to find:**
1. Go to: https://app.supabase.com/project/tamrgxhjyabdvtubseyu/settings/api
2. Look for **"Project API keys"** section
3. Copy the **"anon" "public"** key
4. It starts with `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

**Safety:** ✅ Safe to use in mobile app (it's public)

---

### 2. Supabase JWT Secret
**Needed for:** Backend to validate JWT tokens  
**File:** `backend/.env`  
**Variable:** `SUPABASE_JWT_SECRET`

**Where to find:**
1. Go to: https://app.supabase.com/project/tamrgxhjyabdvtubseyu/settings/api
2. Scroll down to **"JWT Settings"** section
3. Copy **"JWT Secret"**
4. It's a long alphanumeric string

**Safety:** ⚠️ KEEP SECRET - Don't commit to git

---

### 3. Supabase Service Role Key
**Needed for:** Backend admin operations (bypass RLS)  
**File:** `backend/.env`  
**Variable:** `SUPABASE_SERVICE_ROLE_KEY`

**Where to find:**
1. Go to: https://app.supabase.com/project/tamrgxhjyabdvtubseyu/settings/api
2. Look for **"Project API keys"** section
3. Copy the **"service_role" "secret"** key
4. It starts with `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

**Safety:** 🚨 EXTREMELY SECRET - Full database access! Never expose!

---

## 📝 Quick Copy-Paste Template

### Mobile `.env` File
```env
# /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/mobile/.env

# Supabase Configuration
EXPO_PUBLIC_SUPABASE_URL=https://tamrgxhjyabdvtubseyu.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=PASTE_ANON_KEY_HERE

# Backend API Configuration
EXPO_PUBLIC_API_URL=http://localhost:8000
```

### Backend `.env` File
```env
# /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/backend/.env

# Connect to Supabase via connection pooling (already set)
DATABASE_URL="postgresql://postgres.tamrgxhjyabdvtubseyu:Fuckcitadelsecurities@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?pgbouncer=true"

# Direct connection to the database (already set)
DIRECT_URL="postgresql://postgres.tamrgxhjyabdvtubseyu:Fuckcitadelsecurities@aws-1-ap-south-1.pooler.supabase.com:5432/postgres"

# ADD THESE:
SUPABASE_URL=https://tamrgxhjyabdvtubseyu.supabase.co
SUPABASE_JWT_SECRET=PASTE_JWT_SECRET_HERE
SUPABASE_SERVICE_ROLE_KEY=PASTE_SERVICE_ROLE_KEY_HERE
```

---

## 🎯 Step-by-Step: Getting All Credentials

### Step 1: Open Supabase API Settings
```
https://app.supabase.com/project/tamrgxhjyabdvtubseyu/settings/api
```

### Step 2: Screenshot or Copy These Sections

**Section 1: "Project API keys"**
- [ ] Copy **anon public** key → Save for mobile
- [ ] Copy **service_role secret** key → Save for backend

**Section 2: "JWT Settings"** (scroll down)
- [ ] Copy **JWT Secret** → Save for backend

### Step 3: Update Your Files

**Mobile:**
```bash
# Edit this file:
nano /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/mobile/.env

# Update line 3 with the anon key
```

**Backend:**
```bash
# Edit this file:
nano /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/backend/.env

# Add the three new lines at the bottom
```

### Step 4: Restart Your Apps

```bash
# Restart mobile app
cd mobile
npm start

# Restart backend (when implemented)
cd backend
uvicorn main:app --reload
```

---

## ✅ Verification

After adding credentials, verify they work:

### Test Mobile Auth
```bash
# Start mobile app
cd mobile && npm run web

# Try to sign up with test email
# Check browser console - should NOT see:
# "Supabase credentials not found"
```

### Test Backend JWT Validation (when backend is ready)
```bash
# Get a JWT token from mobile app
# Make a test request:
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" http://localhost:8000/auth/me
```

---

## 🔒 Security Reminders

### ✅ Safe to Commit (Public)
- `EXPO_PUBLIC_SUPABASE_URL`
- `EXPO_PUBLIC_SUPABASE_ANON_KEY`

### 🚨 NEVER Commit (Secret)
- `SUPABASE_JWT_SECRET`
- `SUPABASE_SERVICE_ROLE_KEY`
- `DATABASE_URL` with password

### Check Your `.gitignore`
```bash
# Verify .env files are ignored:
cat .gitignore | grep "\.env"

# Should see:
# .env
# .env.local
# *.env
```

---

## 📌 Quick Links

| Resource | URL |
|----------|-----|
| **API Settings** | https://app.supabase.com/project/tamrgxhjyabdvtubseyu/settings/api |
| **Database Settings** | https://app.supabase.com/project/tamrgxhjyabdvtubseyu/settings/database |
| **SQL Editor** | https://app.supabase.com/project/tamrgxhjyabdvtubseyu/sql |
| **Table Editor** | https://app.supabase.com/project/tamrgxhjyabdvtubseyu/editor |
| **Auth Dashboard** | https://app.supabase.com/project/tamrgxhjyabdvtubseyu/auth/users |

---

## 🆘 Common Issues

### "Invalid API key" error
- Double-check you copied the full key (they're very long!)
- Make sure no extra spaces at beginning/end
- Verify you copied anon key for mobile, not service_role

### "JWT validation failed"
- Check JWT_SECRET is copied correctly
- Make sure it matches what's in Supabase dashboard
- Restart backend after updating .env

### "Connection refused" error
- Check DATABASE_URL is correct
- Verify your IP is allowed (Supabase has allowlists)
- Try pinging the database host

---

**Ready?** Follow the steps above to gather your credentials, then move on to `DATABASE_SETUP_GUIDE.md` to apply the schema!
