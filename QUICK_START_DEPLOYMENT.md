# 🚀 Quick Start Guide - GitHub & Deployment

## Step-by-Step Instructions

### Prerequisites
- GitHub account
- Git installed on your machine
- Streamlit Community Cloud account (free, sign up with GitHub)

---

## Phase 1: Push to GitHub (15 minutes)

### 1. Check Repository Access
Verify you have access to: https://github.com/kwokric/SimpleTools

### 2. Initialize Git (if needed)
```bash
cd "/Users/kwokric/JIRA management"

# Check if git is already initialized
git status

# If not initialized, run:
git init
```

### 3. Stage and Commit Files
```bash
# Add all files (respecting .gitignore)
git add .

# Review what will be committed
git status

# Commit with message
git commit -m "Initial commit: JIRA Sprint Management Tool

- Streamlit dashboard for sprint management
- Burndown chart tracking
- Resource allocation analysis
- AI-powered agents for insights
- Alert system for blockers and risks"
```

### 4. Connect to GitHub Repository
```bash
# Add remote (replace with your actual repo URL if different)
git remote add origin https://github.com/kwokric/SimpleTools.git

# Verify remote
git remote -v

# Push to GitHub
git push -u origin main

# If main branch doesn't exist, try:
git push -u origin master
```

**Note:** You may need to authenticate with GitHub. Use a Personal Access Token (PAT) if prompted.

**Creating a PAT:**
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` scope
3. Use token as password when pushing

---

## Phase 2: Deploy to Streamlit Cloud (10 minutes)

### 1. Sign Up for Streamlit Cloud
- Go to: https://share.streamlit.io
- Click "Sign up" and use your GitHub account

### 2. Create New App
1. Click "New app" button
2. Fill in details:
   - **Repository:** `kwokric/SimpleTools`
   - **Branch:** `main` (or `master`)
   - **Main file path:** `src/app.py`
   - **App URL:** Choose a custom name (e.g., `jira-sprint-tool`)

3. Click "Advanced settings" (optional but recommended):
   - **Python version:** 3.9 or higher
   - **Secrets:** Add admin password (see below)

### 3. Add Secrets (Optional)
Click "Advanced settings" → "Secrets" and add:
```toml
[general]
ADMIN_PASSWORD = "your_secure_password_here"
```

### 4. Deploy!
- Click "Deploy"
- Wait 2-5 minutes for initial deployment
- Your app will be live at: `https://[your-app-name].streamlit.app`

---

## Phase 3: Setup Data Storage (Optional - 30 minutes)

### Option: Google Sheets Integration

**Why Google Sheets?**
- Free unlimited storage
- Excel-like interface
- Easy collaboration
- API access for automated sync

### Steps:

#### 1. Create Google Sheet
1. Go to Google Sheets
2. Create new spreadsheet named "JIRA_Sprint_Data"
3. Create sheets for:
   - `sprint_data` (main sprint CSV)
   - `plan_data` (plan CSV)
   - `upload_history` (tracking)
   - `alert_dismissals` (user preferences)

#### 2. Enable Google Sheets API
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project (e.g., "JIRA-Sprint-Tool")
3. Enable "Google Sheets API"
4. Enable "Google Drive API"

#### 3. Create Service Account
1. Go to IAM & Admin → Service Accounts
2. Create service account (e.g., "streamlit-app")
3. Create key (JSON format)
4. Download credentials JSON file

#### 4. Share Sheet with Service Account
1. Open your Google Sheet
2. Click "Share"
3. Add service account email (from JSON file: `client_email`)
4. Give "Editor" permissions

#### 5. Add Credentials to Streamlit Secrets
In Streamlit Cloud app settings, add to secrets:
```toml
[general]
ADMIN_PASSWORD = "your_password"

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs/your-service-account"
```

#### 6. Update requirements.txt
Add these lines to `requirements.txt`:
```
gspread==5.12.0
oauth2client==4.1.3
```

#### 7. Modify Code for Google Sheets
(I can help implement this if you choose this option)

---

## Troubleshooting

### Push to GitHub Issues

**Error: "Permission denied"**
- Use Personal Access Token instead of password
- Ensure you have write access to repository

**Error: "Repository not found"**
- Check repository URL
- Verify repository exists and you have access

**Error: "Branch main does not exist"**
- Try pushing to `master` branch instead
- Or create `main` branch: `git branch -M main`

### Streamlit Deployment Issues

**Error: "Module not found"**
- Ensure `requirements.txt` is in repository root
- Check all imports are listed

**Error: "Port already in use"**
- This shouldn't happen on Streamlit Cloud
- For local testing, change port in config

**App crashes on startup**
- Check logs in Streamlit Cloud dashboard
- Ensure all data files have fallback logic

---

## Testing Your Deployed App

### 1. Basic Functionality
- [ ] App loads without errors
- [ ] Can upload CSV file
- [ ] Burndown chart displays
- [ ] Resource allocation shows

### 2. Data Persistence
- [ ] Upload history saves between sessions
- [ ] Alert dismissals persist
- [ ] Plans save correctly

### 3. Performance
- [ ] App responds within 5 seconds
- [ ] Large files process successfully
- [ ] Charts render smoothly

---

## Updating Your App

### After Making Code Changes:
```bash
# Make changes to your code
# Then commit and push:

git add .
git commit -m "Description of changes"
git push origin main
```

**Streamlit Cloud auto-deploys** when you push to GitHub! 🎉

---

## Next Steps After Deployment

1. **Share URL** with your team
2. **Monitor usage** via Streamlit Cloud dashboard
3. **Set up alerts** for app downtime (optional)
4. **Create documentation** for users
5. **Collect feedback** and iterate

---

## Support

- **Streamlit Docs:** https://docs.streamlit.io
- **GitHub Help:** https://docs.github.com
- **Google Sheets API:** https://developers.google.com/sheets

---

**Ready to deploy? Start with Phase 1! 🚀**
