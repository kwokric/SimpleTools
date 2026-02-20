# Auto-Persistence Strategy - How It Works

## The Challenge

You want:
1. ✅ Upload data once
2. ✅ Refresh page → data still there
3. ✅ Deploy app → data still there
4. ✅ Everyone sees the same data

## The Solution: Hybrid Approach

### 📊 How Data Flows

```
User uploads CSV locally
        ↓
Saved to TWO places:
├── data/cache/          (Fast, temporary)
└── data/sprints/        (Permanent, in Git)
        ↓
You run: ./push_data.sh
        ↓
Git commit + push to GitHub
        ↓
Streamlit Cloud auto-deploys
        ↓
Everyone sees updated data!
```

---

## 🎯 Three-Tier Storage System

### Tier 1: Session State (Immediate)
- **Location:** Memory
- **Lifetime:** Current page session
- **Speed:** Instant
- **Purpose:** While user is actively using app

### Tier 2: Cache (Fast Reload)
- **Location:** `data/cache/` 
- **Lifetime:** Until app restart
- **Speed:** Very fast
- **Purpose:** Survive page refreshes

### Tier 3: Permanent (Git-tracked)
- **Location:** `data/sprints/` and `data/plans/`
- **Lifetime:** Forever (in Git)
- **Speed:** Fast
- **Purpose:** Survive deployments, shared across all users

---

## 📁 File Structure

```
data/
├── cache/                              # Temporary (NOT in Git)
│   ├── last_sprint_data.csv           # Latest upload (temp)
│   ├── last_plan_data.csv             # Latest plan (temp)
│   └── metadata.json                  # Upload info
│
├── sprints/                            # Permanent (IN Git)
│   ├── sprint_2026-01-23.csv          # Historical sprint
│   ├── sprint_2026-02-06.csv          # Another sprint
│   └── sprint_2026-02-20.csv          # Latest sprint ← Auto-loads this
│
└── plans/                              # Permanent (IN Git)
    ├── plan_2026-01-26.csv
    └── plan_2026-01-27.csv             # Latest plan ← Auto-loads this
```

---

## 🔄 Complete Workflow

### For You (Data Uploader):

**Step 1: Upload Locally**
```bash
# Run your local app
streamlit run src/app.py

# Upload CSV in browser
# ✅ Data saved to data/cache/ (immediate)
# ✅ Data also saved to data/sprints/ (permanent)
```

**Step 2: Push to Cloud**
```bash
# Sync to GitHub
./push_data.sh

# This does:
# - git add data/
# - git commit
# - git push origin main
```

**Step 3: Streamlit Cloud Auto-Deploys**
- Detects push
- Rebuilds app
- New data is live!

### For Cloud Users (Viewers):

**First Visit:**
1. Open app URL
2. App auto-loads from `data/sprints/sprint_*.csv` (most recent)
3. See latest data immediately!

**After Refresh:**
1. Refresh page
2. App loads from cache (faster!)
3. Data still there

**After You Push Updates:**
1. App restarts automatically
2. Loads new data from Git
3. Everyone sees updates

---

## 🚀 Auto-Load Logic

### On App Start:

```python
def auto_save_and_load_wrapper():
    # 1. Check cache first (fastest)
    if cache_exists:
        load_from_cache()
    
    # 2. Otherwise, load from Git-tracked files
    else:
        latest_sprint = get_latest_sprint_file()  # Most recent sprint_*.csv
        latest_plan = get_latest_plan_file()      # Most recent plan_*.csv
        load_and_cache(latest_sprint, latest_plan)
    
    # 3. Show user what was loaded
    display_load_message()
```

### Priority:
1. **Cache** (if exists, use it - fastest)
2. **Git files** (if cache empty, load most recent file)
3. **Nothing** (fresh start, wait for upload)

---

## ✅ Benefits

### For Local Development:
- ✅ Fast reloads (cache)
- ✅ Data persists in files
- ✅ Easy to inspect/edit

### For Cloud Deployment:
- ✅ Data survives app restarts
- ✅ All users see same data
- ✅ Version controlled (Git)
- ✅ No database setup needed

### For Users:
- ✅ No re-uploading after refresh
- ✅ Always see latest data
- ✅ Fast page loads

---

## 🔒 What Gets Committed to Git?

### ✅ Tracked (Committed):
- `data/sprints/sprint_*.csv` 
- `data/plans/plan_*.csv`
- `data/upload_history.csv`
- `data/rules.json`
- All source code

### ❌ NOT Tracked (Excluded):
- `data/cache/*` (temporary)
- `logs/*` (temporary)
- `.venv/` (local Python environment)

---

## 📝 Your Workflow Summary

### Daily Use:

```bash
# Morning: Start local app
streamlit run src/app.py

# Upload new data via browser
# ✅ Auto-saved to cache + permanent storage

# Sync to cloud (when ready)
./push_data.sh

# Done! Cloud users see updates in ~30 seconds
```

### One-Time Setup (Already Done):
- ✅ Git repository initialized
- ✅ Auto-save/load code added
- ✅ Directory structure created
- ✅ .gitignore configured

---

## 🎯 Key Points

1. **You upload locally** (has file access, network access if needed)
2. **Data saved to Git-tracked files** (permanent)
3. **You manually push** when ready (control timing)
4. **Cloud auto-deploys** (users see updates)
5. **Everyone auto-loads** latest data (no manual uploads)

---

## 💡 Why This Approach?

### Why Not Auto-Commit from Cloud?
- ❌ Streamlit Cloud is read-only
- ❌ Would need GitHub auth tokens (security risk)
- ❌ Complex setup

### Why Not Database?
- ❌ Costs money
- ❌ More complex
- ❌ CSV files work perfectly fine

### Why Git-Based?
- ✅ Free
- ✅ Version control built-in
- ✅ You already use Git
- ✅ Simple file system
- ✅ Easy to backup/restore

---

## 🔧 Commands Reference

### Push Data to Cloud:
```bash
./push_data.sh
```

### Manual Push:
```bash
git add data/
git commit -m "Update data"
git push origin main
```

### Check What Changed:
```bash
git status
git diff data/
```

### View Cloud Logs:
- Go to Streamlit Cloud dashboard
- Click your app
- View logs tab

---

## 🎉 Result

**Perfect balance of:**
- ✅ Ease of use
- ✅ Data persistence
- ✅ Cost ($0)
- ✅ Your control
- ✅ Auto-loading for everyone

**No complex setup needed - just works!** 🚀

---

## Next Steps

1. Test locally (already works!)
2. Push to GitHub: `./push_data.sh`
3. Verify on Streamlit Cloud
4. Users can now refresh without losing data!

Done! The system is ready. 🎊
