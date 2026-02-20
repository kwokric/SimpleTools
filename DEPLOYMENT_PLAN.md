# Deployment Plan for JIRA Management Tool

## Overview
This plan outlines how to:
1. Host the Streamlit app online for free
2. Push code to GitHub repository
3. Store data in an online Excel/cloud storage solution

---

## 1. FREE HOSTING OPTIONS

### Option A: Streamlit Community Cloud (RECOMMENDED ✅)
**Best for Streamlit apps - 100% Free**

**Features:**
- Free hosting for public apps
- Automatic deployment from GitHub
- Supports private GitHub repos (with authentication)
- Built-in secrets management
- Auto-restarts on code changes
- 1 GB storage, shared CPU/RAM

**Steps:**
1. Push code to GitHub (see Section 2)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub account
4. Click "New app"
5. Select repository: `kwokric/SimpleTools`
6. Set main file path: `src/app.py`
7. Deploy!

**Limitations:**
- Apps sleep after inactivity (wake up when accessed)
- Public URL (anyone with link can access)
- Limited resources for heavy computation

---

### Option B: Render.com
**Free tier with 750 hours/month**

**Features:**
- Free tier includes 750 hours/month
- Supports Docker deployments
- Persistent storage with paid plans

**Setup:**
1. Create `render.yaml` (see Section 3)
2. Connect GitHub repo
3. Automatic deployment

---

### Option C: Railway.app
**$5 free credit monthly**

**Features:**
- Easy deployment from GitHub
- Good performance
- $5 free credit/month (then pay-as-you-go)

---

### Option D: Hugging Face Spaces
**Free for public spaces**

**Features:**
- Free for ML/AI apps
- Supports Streamlit
- Good community

---

## 2. GITHUB REPOSITORY SETUP

### Current Status
- Target repository: https://github.com/kwokric/SimpleTools
- Project folder: "JIRA management"

### Preparation Steps

#### A. Create Required Files

**1. `.gitignore` file** (exclude sensitive/unnecessary files)
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/

# Data files (exclude local data)
data/*.csv
data/*.json
data/plans/*.csv
data/sprints/*.csv
logs/*.log

# Keep example files
!data/Sample Input.csv

# IDE
.vscode/
.DS_Store

# Secrets
.env
secrets.toml
```

**2. `requirements.txt`** (rename from install_requirements.txt)
```
pandas==2.0.3
openpyxl==3.1.2
matplotlib==3.7.2
scikit-learn==1.3.0
streamlit==1.28.0
fpdf==1.7.2
plotly==5.17.0
```

**3. `.streamlit/config.toml`** (Streamlit configuration)
```toml
[theme]
primaryColor = "#4CAF50"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
headless = true
port = 8501
enableCORS = false
```

**4. `README.md` (Update for GitHub)**
- Add deployment instructions
- Add live demo link (after deployment)
- Add badges

#### B. Security Fixes

**CRITICAL: Remove hardcoded password**
Current line in `src/app.py`:
```python
if admin_password == "admin123":
```

**Replace with environment variable:**
```python
import os
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change_me_in_production")
if admin_password == ADMIN_PASSWORD:
```

#### C. Initialize Git & Push

```bash
cd "/Users/kwokric/JIRA management"

# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: JIRA Sprint Management Tool"

# Add remote repository
git remote add origin https://github.com/kwokric/SimpleTools.git

# Push to main branch
git push -u origin main
```

---

## 3. ONLINE DATA STORAGE SOLUTIONS

### Option A: Google Sheets (RECOMMENDED ✅)
**Best for Excel-like interface + API access**

**Advantages:**
- Free unlimited storage
- Excel-like interface
- API access via `gspread` library
- Real-time collaboration
- Version history

**Implementation:**
1. Create Google Sheet for data storage
2. Enable Google Sheets API
3. Install `gspread` and `oauth2client`:
   ```bash
   pip install gspread oauth2client
   ```
4. Store credentials in Streamlit secrets
5. Modify code to read/write from Google Sheets

**Code Changes Needed:**
```python
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Load from Google Sheets
def load_data_from_sheets():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    sheet = client.open("JIRA_Data").sheet1
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Save to Google Sheets
def save_data_to_sheets(df, sheet_name="plan_data"):
    # Similar implementation
    pass
```

---

### Option B: GitHub Repository (Data Branch)
**Store data in separate branch**

**Advantages:**
- Free
- Version control
- No external dependencies

**Disadvantages:**
- Not ideal for frequent updates
- Manual merge conflicts
- Rate limits on API

---

### Option C: Dropbox
**Cloud storage with API**

**Advantages:**
- 2GB free storage
- Simple API
- File versioning

**Implementation:**
```bash
pip install dropbox
```

---

### Option D: AWS S3 Free Tier
**12 months free with limits**

**Advantages:**
- Professional solution
- 5GB storage
- Good performance

**Disadvantages:**
- Requires AWS account
- More complex setup
- Costs after free tier

---

## 4. RECOMMENDED ARCHITECTURE

```
┌─────────────────────────────────────────┐
│  Streamlit Cloud (Free Hosting)         │
│  - Hosts web application                │
│  - Auto-deploys from GitHub             │
│  - Public URL access                    │
└─────────────────┬───────────────────────┘
                  │
                  │ Pulls code
                  ▼
┌─────────────────────────────────────────┐
│  GitHub Repository                       │
│  https://github.com/kwokric/SimpleTools │
│  - Source code                          │
│  - Version control                      │
│  - Automated deployments                │
└─────────────────┬───────────────────────┘
                  │
                  │ API calls
                  ▼
┌─────────────────────────────────────────┐
│  Google Sheets (Data Storage)           │
│  - Sprint data                          │
│  - Plan data                            │
│  - Upload history                       │
│  - Alert dismissals                     │
└─────────────────────────────────────────┘
```

---

## 5. IMPLEMENTATION CHECKLIST

### Phase 1: Prepare Code for GitHub ✓
- [ ] Create `.gitignore` file
- [ ] Rename `install_requirements.txt` to `requirements.txt`
- [ ] Create `.streamlit/config.toml`
- [ ] Fix hardcoded password (use environment variable)
- [ ] Update README.md with deployment info
- [ ] Test locally to ensure everything works

### Phase 2: Push to GitHub ✓
- [ ] Initialize git repository
- [ ] Commit all files
- [ ] Push to https://github.com/kwokric/SimpleTools
- [ ] Verify files on GitHub

### Phase 3: Setup Online Data Storage ✓
- [ ] Create Google Sheet for data
- [ ] Enable Google Sheets API
- [ ] Generate service account credentials
- [ ] Install `gspread` library
- [ ] Modify data loading/saving functions
- [ ] Test read/write operations

### Phase 4: Deploy to Streamlit Cloud ✓
- [ ] Sign up at share.streamlit.io
- [ ] Create new app from GitHub repo
- [ ] Add secrets (Google credentials, admin password)
- [ ] Configure app settings
- [ ] Deploy and test
- [ ] Share public URL

### Phase 5: Migration ✓
- [ ] Migrate existing data to Google Sheets
- [ ] Test full workflow with online storage
- [ ] Update documentation with new URLs
- [ ] Announce to users

---

## 6. ESTIMATED COSTS

| Service | Cost | Notes |
|---------|------|-------|
| Streamlit Cloud | **FREE** | Public apps, limited resources |
| GitHub | **FREE** | Public repositories |
| Google Sheets | **FREE** | API included |
| **Total Monthly** | **$0** | Fully free solution! |

---

## 7. NEXT STEPS

1. **Review this plan** - Confirm approach
2. **Backup current data** - Export all CSV files
3. **Execute Phase 1** - Prepare code
4. **Execute Phases 2-4** - Deploy
5. **Test thoroughly** - Verify all features work online
6. **Monitor** - Check app performance and errors

---

## 8. SUPPORT & RESOURCES

- **Streamlit Docs**: https://docs.streamlit.io/streamlit-community-cloud
- **Google Sheets API**: https://developers.google.com/sheets/api
- **GitHub Guides**: https://guides.github.com/

---

## Notes & Considerations

### Data Privacy
- Streamlit Cloud apps are PUBLIC by default
- Consider authentication if handling sensitive data
- Google Sheets can have restricted access

### Performance
- Free hosting has resource limits
- Large datasets may be slow
- Consider data optimization

### Maintenance
- Auto-deploys on GitHub push (can disable)
- Monitor app logs in Streamlit Cloud dashboard
- Keep dependencies updated

### Alternative: Self-Hosting
If free options don't meet needs:
- DigitalOcean Droplet ($5/month)
- AWS EC2 t2.micro (free tier 12 months)
- Your own VPS/server

---

**Ready to proceed? Let me know which option you prefer, and I'll help implement it!**
