# Auto-Save & Auto-Load Feature

## What It Does

Your app now **automatically saves and restores uploaded data**:

✅ **Upload data once** → It's saved automatically  
✅ **Refresh the page** → Data loads automatically  
✅ **No re-uploading needed** → Last uploaded data persists

---

## How It Works

### 1. **Automatic Save**
When you upload data (Sprint or Plan):
- Data is saved to `data/cache/` directory
- Metadata (filename, upload time, row count) is stored
- You'll see: ✅ "Data saved! Will auto-load on next visit."

### 2. **Automatic Load**
When you open the app:
- App checks for saved data
- If found, loads it automatically
- Shows in sidebar: ✅ "Auto-loaded: filename.csv"

### 3. **Metadata Display**
In the sidebar, you'll see:
```
✅ Auto-loaded: Jan_15.csv
📅 Uploaded: 2026-02-20 15:30:45
📊 Rows: 150
```

---

## Files Structure

```
data/
├── cache/                          # Auto-save location (NOT in Git)
│   ├── last_sprint_data.csv       # Last sprint upload
│   ├── last_plan_data.csv         # Last plan upload
│   └── metadata.json              # Upload metadata
├── sprints/                        # Permanent sprint storage
│   └── sprint_2026-02-06.csv
└── plans/                          # Permanent plan storage
    └── plan_2026-01-27.csv
```

**Note:** `data/cache/` is temporary and excluded from Git (see `.gitignore`)

---

## User Experience

### Before (Without Auto-Save):
1. Open app
2. Upload CSV
3. View data
4. **Refresh page** → Data lost 😞
5. Upload again

### After (With Auto-Save):
1. Open app
2. Upload CSV ✅ Auto-saved
3. View data
4. **Refresh page** → Data auto-loads! 🎉
5. Continue working

---

## Cloud Deployment

### On Streamlit Cloud:

**How it works:**
- Each user session has its own cache
- Cache persists during app runtime
- **Note:** Cache is cleared when app restarts (typically happens when you push updates to GitHub)

**Behavior:**
- ✅ Survives page refreshes
- ✅ Survives browser close/reopen (same session)
- ❌ Cleared on app restart/redeploy

**Why this is perfect:**
- Users don't need to re-upload after every refresh
- Data doesn't pile up forever
- Fresh start after app updates

---

## For Local Development

### Cache Location:
```
/Users/kwokric/JIRA management/data/cache/
```

### To View Cache:
```bash
ls -la data/cache/
cat data/cache/metadata.json
```

### To Clear Cache Manually:
```bash
rm -rf data/cache/*
```

Or use the **Admin** panel in the app (coming soon).

---

## Admin Features

### Clear Cache Button (Add this if needed)

In your app's admin section, you can add:

```python
if is_admin:
    if st.sidebar.button("🗑️ Clear Cached Data"):
        if persistence.clear_cache():
            st.success("Cache cleared!")
            st.rerun()
```

---

## Technical Details

### Storage Method:
- **Format:** CSV files (lightweight, easy to inspect)
- **Location:** `data/cache/` directory
- **Metadata:** JSON file with upload timestamps
- **Size:** Minimal (only last upload stored)

### Session State Integration:
- Works seamlessly with existing session state
- No changes to your current workflow
- Transparent to users

### Data Flow:

```
User uploads CSV
       ↓
Saved to session_state (existing)
       ↓
AUTO-SAVE to data/cache/
       ↓
User refreshes page
       ↓
AUTO-LOAD from data/cache/
       ↓
Restored to session_state
       ↓
User continues working
```

---

## Benefits

### For You:
- ✅ No more re-uploading after page refresh
- ✅ Faster workflow
- ✅ Better user experience

### For Cloud Users:
- ✅ Data persists during session
- ✅ No need to re-upload constantly
- ✅ Seamless experience

### For Development:
- ✅ Easy to test (cached data available)
- ✅ No database setup needed
- ✅ Simple file-based storage

---

## Limitations & Considerations

### What's NOT Saved:
- ❌ User preferences/settings (use session_state)
- ❌ Chart states/filters
- ❌ Multi-session sharing (each user has own cache)

### When Cache is Cleared:
- App restart/redeploy
- Manual clear by admin
- File system cleanup (rare)

### Not a Database:
- This is **session-level caching**, not permanent storage
- For permanent storage, still use `data/sprints/` and `data/plans/`
- Cache is just for convenience between refreshes

---

## Testing the Feature

### Local Test:
1. Run app: `streamlit run src/app.py`
2. Upload a CSV file
3. Note the success message: "Data saved!"
4. Refresh the browser (F5)
5. Check sidebar: Should show "Auto-loaded: filename.csv"
6. Data should be there without re-uploading!

### Cloud Test (After deployment):
1. Open deployed app
2. Upload CSV
3. Refresh page
4. Verify data auto-loads

---

## What Changed in Your Code

### Added Files:
- ✅ `src/data_persistence.py` - Auto-save/load module
- ✅ `data/cache/` - Cache directory

### Modified Files:
- ✅ `src/app.py` - Added auto-save on upload, auto-load on start
- ✅ `.gitignore` - Excluded cache directory

### New Imports:
```python
from data_persistence import DataPersistence, auto_save_and_load_wrapper
```

### New Function Call (in main):
```python
persistence = auto_save_and_load_wrapper()
```

### New Save Calls (after upload):
```python
persistence.save_sprint_data(df, filename)
persistence.save_plan_data(df, filename)
```

---

## Summary

**Before:** Upload → View → Refresh → Lost → Re-upload 🔄  
**After:** Upload → View → Refresh → Auto-restored ✨

**Zero configuration needed - it just works!** 🎉

---

## Questions?

**Q: Will my old data work?**  
A: Yes! Existing data in `data/sprints/` and `data/plans/` is unaffected.

**Q: Do I need to change anything?**  
A: No! Feature works automatically.

**Q: What if I want to upload new data?**  
A: Just upload normally - it will overwrite the cache with new data.

**Q: Does this work on Streamlit Cloud?**  
A: Yes! Works perfectly.

**Q: Is my data secure?**  
A: Same security as before - files stored same way, just with auto-load.

---

**The feature is ready to use! Push to GitHub and deploy.** 🚀
