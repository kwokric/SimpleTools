# Quick Guide for Team Member - Updating JIRA Dashboard Data

**Welcome! This guide will help you update the JIRA dashboard while the main admin is away.**

---

## ⚠️ Important: Localhost Upload Only

**🔒 Security Notice:** For data integrity and security:
- ✅ File uploads work **ONLY when running locally** (localhost)
- ❌ File uploads are **disabled** on the cloud version (https://jiramanagement.streamlit.app)
- 📊 The cloud dashboard is **read-only** - everyone can view but not upload

**This means you MUST:**
1. Run the app on your local machine using `streamlit run src/app.py`
2. Upload files through your local browser (http://localhost:8501)
3. Push changes to GitHub using `./push_data.sh`
4. The cloud will automatically update within 1-2 minutes

---

## 🎯 What You'll Do

1. Upload new JIRA data to the local app
2. Push the data to the cloud
3. Everyone sees the updated dashboard

**Time needed:** 5-10 minutes per update

---

## 📋 Prerequisites

Make sure you have:
- [ ] Access to this project folder
- [ ] Git installed on your computer
- [ ] GitHub access to repository: `kwokric/SimpleTools`
- [ ] Python 3.9+ installed
- [ ] The latest JIRA CSV export file

---

## 🚀 Step-by-Step Instructions

### Step 1: Open Terminal/Command Prompt

**Mac:**
- Open Spotlight (Cmd + Space)
- Type "Terminal" and press Enter

**Windows:**
- Press Windows Key + R
- Type "cmd" and press Enter

---

### Step 2: Navigate to Project Folder

```bash
cd "/Users/kwokric/JIRA management"
```

**Note:** If the path is different on your machine, replace it with the correct path.

---

### Step 3: Run the Dashboard Locally

```bash
# Activate Python environment (if using virtual environment)
source .venv/bin/activate

# Or on Windows:
# .venv\Scripts\activate

# Run the app
streamlit run src/app.py
```

A browser window will open automatically at `http://localhost:8501`

---

### Step 4: Export and Upload Your Data

**4a. Export JIRA Data:**

1. Go to: https://manulife-gwam.atlassian.net/issues/?filter=37000
2. Click "Export" button (top right)
3. Select "Excel CSV (Current fields)"
4. Save the CSV file to your computer

**4b. Upload in Browser:**

1. **Log in as Admin:**
   - Look for "🔐 Admin Access" in the left sidebar
   - Enter password: `admin123` (or the password you were given)
   - You should see "Admin Unlocked" ✅

2. **Upload Sprint Data:**
   - Find "📤 Upload Sprint Data" section
   - Click "Browse files" or "Sprint JIRA Export (CSV)"
   - Select the CSV file you just exported
   - **Set Data Snapshot Date:** (Today's date)
   - Click "Process & Update" button
   - Wait for "✅ Sprint Data Saved" message

3. **Upload Plan Data (if you have it):**
   - Find "📤 Upload Plan Data" section
   - Click "Browse files" or "Plan Excel/CSV"
   - Select your plan file
   - Set Plan Snapshot Date
   - Click "Process & Update"

---

### Step 5: Push Data to Cloud

**Close the browser and go back to Terminal.**

Run this single command:

```bash
./push_data.sh
```

**What this does:**
- Commits your data changes to Git
- Pushes to GitHub
- Triggers automatic deployment to the cloud
- Everyone sees your updates in ~30 seconds

**You'll see:**
```
🔄 Syncing data to cloud...
📦 Adding data files...
🚀 Pushing to GitHub...
✅ Done! Data synced to cloud.
⏱️  Streamlit Cloud will refresh in ~30 seconds.
```

---

### Step 6: Verify Update

1. Go to: https://jiramanagement.streamlit.app
2. Wait ~30 seconds for deployment
3. Refresh the page
4. Your new data should be visible!

---

## 🔧 Troubleshooting

### Problem: "Permission denied" when pushing

**Solution:** You need GitHub authentication

```bash
# Option 1: Set up Personal Access Token (PAT)
# 1. Go to: https://github.com/settings/tokens
# 2. Generate new token (classic)
# 3. Select scope: "repo"
# 4. Copy the token
# 5. When Git asks for password, paste the token

# Option 2: Ask the admin to add you as collaborator
```

---

### Problem: "streamlit: command not found"

**Solution:** Install Streamlit

```bash
pip install streamlit
# Or
pip install -r requirements.txt
```

---

### Problem: "ModuleNotFoundError"

**Solution:** Install dependencies

```bash
pip install -r requirements.txt
```

---

### Problem: Wrong dates or validation errors

**Solution:**
- Sprint End Date must be a **Friday**
- Sprint Start Date must be a **Monday**
- Start Date should be ~2 weeks before End Date

---

### Problem: App won't start

**Solution:**

```bash
# Check if another instance is running
# Press Ctrl+C to stop any running processes

# Try running again
streamlit run src/app.py
```

---

## 📝 Quick Reference Commands

```bash
# Navigate to project
cd "/Users/kwokric/JIRA management"

# Run app locally
streamlit run src/app.py

# Push data to cloud (AFTER uploading in browser)
./push_data.sh

# Check Git status (what will be uploaded)
git status

# View recent pushes
git log --oneline -5
```

---

## ⚠️ Important Notes

### DO:
✅ Upload data through the local app first  
✅ Run `./push_data.sh` after uploading  
✅ Verify dates are correct (Friday end, Monday start)  
✅ Check the cloud app after pushing  

### DON'T:
❌ Edit CSV files directly in `data/` folder  
❌ Delete files from `data/sprints/` or `data/plans/`  
❌ Push without uploading through the app first  
❌ Forget to run `./push_data.sh`  

---

## 📅 Step by Step Example

**Every morning (or as needed):**

```bash
# 1. Export JIRA data
# Go to: https://manulife-gwam.atlassian.net/issues/?filter=37000
# Click "Export" → "Excel CSV (Current fields)"

# 2. Navigate to project
cd "/Users/kwokric/JIRA management"

# 3. Start local app
streamlit run src/app.py

# 4. In browser: 
#    - Login as admin
#    - Upload the exported CSV
#    - Set "Data Snapshot Date" to today
#    - Click "Process & Update"

# 5. Close browser, push to cloud
./push_data.sh

# 6. Verify at https://jiramanagement.streamlit.app

# Done! Takes 5-10 minutes total.
```

---

## 🎓 Understanding the System

**How it works:**

```
You upload CSV locally
        ↓
Saved to data/sprints/ folder
        ↓
./push_data.sh runs
        ↓
Git commits changes
        ↓
Pushes to GitHub
        ↓
Streamlit Cloud detects push
        ↓
Auto-deploys new version
        ↓
Everyone sees updated data!
```

**Key folders:**
- `data/sprints/` - Sprint data files (sprint_2026-02-06.csv)
- `data/plans/` - Plan data files (plan_2026-01-27.csv)
- `data/cache/` - Temporary (don't worry about this)

---

## ✅ Success Checklist

After each upload, verify:

- [ ] Local app showed "✅ Sprint Data Saved"
- [ ] `./push_data.sh` ran successfully
- [ ] Saw "✅ Done! Data synced to cloud."
- [ ] Cloud app updated (https://jiramanagement.streamlit.app)
- [ ] New data is visible in dashboard
- [ ] No error messages

---

## 🔐 Admin Password

**Default:** `admin123`

**If it doesn't work:** Contact the admin for the updated password.

---

## Self Support

**Repository:** https://github.com/kwokric/SimpleTools  
**Cloud App:** https://jiramanagement.streamlit.app  

**Documentation in project:**
- `README.md` - Project overview
- `USER_GUIDE.md` - Full user guide
- `QUICK_START_DEPLOYMENT.md` - Deployment guide

---

## 🎉 You're Ready!

**Remember:**
1. Run app locally → Upload data → Close app → Run `./push_data.sh`
2. That's it! Simple as that.

**Don't worry if you make a mistake** - everything is version controlled in Git, so we can always restore previous data if needed.

**Good luck! You've got this! 🚀**

---

## 📸 Visual Workflow

```
┌─────────────────────────────────┐
│ 1. Open Terminal                │
└─────────────────┬───────────────┘
                  │
┌─────────────────▼───────────────┐
│ 2. cd to project folder         │
└─────────────────┬───────────────┘
                  │
┌─────────────────▼───────────────┐
│ 3. streamlit run src/app.py    │
└─────────────────┬───────────────┘
                  │
┌─────────────────▼───────────────┐
│ 4. Browser opens automatically  │
│    - Login as admin             │
│    - Upload CSV                 │
│    - Click "Process & Update"   │
└─────────────────┬───────────────┘
                  │
┌─────────────────▼───────────────┐
│ 5. Close browser                │
│    Back to Terminal             │
└─────────────────┬───────────────┘
                  │
┌─────────────────▼───────────────┐
│ 6. ./push_data.sh               │
└─────────────────┬───────────────┘
                  │
┌─────────────────▼───────────────┐
│ 7. Wait 30 seconds              │
│    Check cloud app              │
└─────────────────────────────────┘
```

**That's the entire process! Easy! 😊**
