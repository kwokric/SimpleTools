# Localhost Upload Security Feature

## Overview

File uploads have been restricted to **localhost only** for security and data integrity purposes.

## How It Works

### Detection Mechanism
The app detects whether it's running on Streamlit Cloud using environment variables:
- `STREAMLIT_SHARING_MODE`
- `STREAMLIT_RUNTIME_ENVIRONMENT`

### Behavior

**🟢 Running Locally (http://localhost:8501):**
- ✅ File uploads are **enabled**
- ✅ Admin can upload Sprint Data
- ✅ Admin can upload Plan Data
- ✅ All upload features work normally

**🔴 Running on Cloud (https://jiramanagement.streamlit.app):**
- ❌ File uploads are **disabled**
- 📊 Dashboard is **read-only** (view only)
- ℹ️ Users see a message with instructions to upload locally
- 🔒 Prevents accidental data uploads to cloud

## Why This Matters

1. **Data Integrity:** Ensures all data goes through proper validation workflow
2. **Version Control:** Forces data to be committed to Git before appearing on cloud
3. **Audit Trail:** Every data change is tracked in Git history
4. **Team Workflow:** Clear separation between data management (local) and viewing (cloud)

## User Experience

### On Cloud (Read-Only)
When users visit https://jiramanagement.streamlit.app, they see:

```
⚠️ File uploads are disabled on the cloud version.

📌 To upload data:
1. Run the app locally
2. Upload your files
3. Run `./push_data.sh`
4. Changes will appear here automatically!
```

### On Localhost (Upload Enabled)
When running locally, all upload features work as normal.

## Implementation Details

### Code Location
`src/app.py` - Lines ~240-280

```python
# Detect if running on Streamlit Cloud
is_local = not os.getenv("STREAMLIT_SHARING_MODE") and not os.getenv("STREAMLIT_RUNTIME_ENVIRONMENT")

if not is_local:
    # Running on Streamlit Cloud - disable uploads
    st.sidebar.warning("⚠️ File uploads are disabled on the cloud version.")
    st.sidebar.info("📌 To upload data:\n1. Run the app locally\n2. Upload your files\n3. Run `./push_data.sh`\n4. Changes will appear here automatically!")
    uploaded_file = None
    upload_target_str = None
    snapshot_date = None
else:
    # Running locally - allow uploads
    uploaded_file = st.sidebar.file_uploader("Sprint JIRA Export (CSV)", type=['csv'])
    # ... rest of upload UI
```

## Testing

### Test Locally
1. Run: `streamlit run src/app.py`
2. Open: http://localhost:8501
3. Verify: File upload widgets are visible in sidebar
4. Result: ✅ Uploads work

### Test on Cloud
1. Open: https://jiramanagement.streamlit.app
2. Check sidebar for upload section
3. Verify: Warning message shown instead of file uploaders
4. Result: ✅ Uploads disabled

## Documentation Updates

- ✅ `TEAM_MEMBER_GUIDE.md` - Added security notice at top
- ✅ `src/app.py` - Added detection logic and conditional UI
- ✅ `LOCALHOST_UPLOAD_SECURITY.md` - This document

## Deployment

Deployed on: 2026-02-20
Commit: `92128c4` - "Security: Restrict file uploads to localhost only"
Status: ✅ Live on https://jiramanagement.streamlit.app

---

**Note:** This feature ensures that only authorized team members with local access can upload data, while everyone can view the dashboard online.
