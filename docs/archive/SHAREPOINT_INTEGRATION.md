# SharePoint Integration Guide

## Setup Instructions

### 1. Install Required Package

Add to `requirements.txt`:
```
Office365-REST-Python-Client>=2.5.0
```

### 2. Configure SharePoint Settings

#### Option A: Use Streamlit Secrets (Recommended for deployment)

Create/update `.streamlit/secrets.toml`:
```toml
[sharepoint]
site_url = "https://yourcompany.sharepoint.com/sites/YourSite"
username = "your.email@company.com"
password = "your_password"
folder_path = "Shared Documents/JIRA Data"
```

#### Option B: Let users enter credentials (More flexible)
Users enter credentials in the app interface each time.

---

## Integration into app.py

### Option 1: Add as Alternative Upload Method

Add this to your sidebar in `src/app.py`:

```python
# Add import at top of file
from sharepoint_loader import create_sharepoint_file_browser

# In your sidebar, add SharePoint option
st.sidebar.markdown("---")
st.sidebar.header("📁 Data Source")

data_source = st.sidebar.radio(
    "Choose data source:",
    ["Upload File", "Browse SharePoint"]
)

if data_source == "Upload File":
    # Your existing file uploader code
    uploaded_file = st.sidebar.file_uploader(
        "Upload Sprint CSV",
        type=['csv'],
        help="Upload your Jira export CSV file"
    )
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        # ... rest of your code
        
elif data_source == "Browse SharePoint":
    # SharePoint browser
    site_url = st.secrets.get("sharepoint", {}).get(
        "site_url", 
        "https://yourcompany.sharepoint.com/sites/YourSite"
    )
    folder_path = st.secrets.get("sharepoint", {}).get(
        "folder_path",
        "Shared Documents"
    )
    
    df = create_sharepoint_file_browser(site_url, folder_path)
    
    if df is not None:
        # Process the DataFrame same as uploaded file
        st.session_state['sprint_data'] = df
```

---

## Option 2: Simpler - Direct File Path Input

If users know the exact file path in SharePoint:

```python
from sharepoint_loader import SharePointLoader

st.sidebar.markdown("---")
st.sidebar.header("📁 Load from SharePoint")

with st.sidebar.expander("SharePoint File", expanded=False):
    file_path = st.text_input(
        "SharePoint file path",
        placeholder="Shared Documents/JIRA Data/sprint.csv"
    )
    
    if st.button("Load from SharePoint"):
        site_url = "https://yourcompany.sharepoint.com/sites/YourSite"
        loader = SharePointLoader(site_url)
        
        if loader.authenticate():
            df = loader.load_csv_from_sharepoint(file_path)
            if df is not None:
                st.success(f"Loaded {len(df)} rows")
                st.session_state['sprint_data'] = df
```

---

## Option 3: Auto-load from SharePoint (Most Automated)

For users who always load the same file:

```python
from sharepoint_loader import SharePointLoader

# Auto-load on app start
if 'data_loaded' not in st.session_state:
    with st.spinner("Loading data from SharePoint..."):
        site_url = st.secrets["sharepoint"]["site_url"]
        file_path = st.secrets["sharepoint"]["default_file"]
        
        loader = SharePointLoader(site_url)
        if loader.authenticate():
            df = loader.load_csv_from_sharepoint(file_path)
            if df is not None:
                st.session_state['sprint_data'] = df
                st.session_state['data_loaded'] = True
                st.success("✅ Data loaded from SharePoint")
```

---

## Security Considerations

### For Company Use (Network-based):

**Best Practice: Use Azure AD Authentication**

```python
# More secure - uses Azure AD
from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext

def authenticate_with_azure_ad(site_url, client_id, client_secret):
    """
    Authenticate using Azure AD App Registration
    More secure than username/password
    """
    credentials = ClientCredential(client_id, client_secret)
    ctx = ClientContext(site_url).with_credentials(credentials)
    return ctx

# Usage
ctx = authenticate_with_azure_ad(
    st.secrets["sharepoint"]["site_url"],
    st.secrets["azure"]["client_id"],
    st.secrets["azure"]["client_secret"]
)
```

**Setup Azure AD App:**
1. Go to Azure Portal → App Registrations
2. Create new registration
3. API Permissions → SharePoint → Application → Sites.Read.All
4. Certificates & secrets → New client secret
5. Copy Client ID and Secret to secrets.toml

---

## Alternative: Microsoft Graph API

For more modern approach:

```bash
pip install msal requests
```

```python
import msal
import requests

def get_sharepoint_file_graph_api(site_id, file_path, access_token):
    """Use Microsoft Graph API to access SharePoint"""
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root:/{file_path}:/content"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    return response.content
```

---

## Testing Locally

1. **Update requirements.txt:**
   ```bash
   pip install Office365-REST-Python-Client
   ```

2. **Create test secrets file:**
   `.streamlit/secrets.toml`:
   ```toml
   [sharepoint]
   site_url = "https://yourcompany.sharepoint.com/sites/YourSite"
   username = "test@company.com"
   password = "test_password"
   folder_path = "Shared Documents/JIRA Data"
   ```

3. **Test locally first:**
   ```bash
   streamlit run src/app.py
   ```

---

## Deployment Considerations

### On Streamlit Cloud:

1. **Add secrets in Streamlit Cloud dashboard**
2. **Network Access**: Streamlit Cloud servers must be able to reach your SharePoint
   - ✅ Works with: SharePoint Online (public internet)
   - ❌ May not work with: On-premises SharePoint behind firewall
   
### For Internal SharePoint (Behind Firewall):

**Option A: VPN/Network Access**
- Deploy on internal server instead of Streamlit Cloud
- Use company network that can access SharePoint

**Option B: Hybrid Approach**
- You upload locally (has SharePoint access)
- Push to GitHub using `push_data.sh`
- Cloud app reads from GitHub

---

## Which Approach Should You Use?

| Scenario | Best Option |
|----------|-------------|
| **SharePoint Online, public access** | Option 1 or 3 (Direct SharePoint) |
| **Internal SharePoint, on VPN** | Keep current approach (local upload + push_data.sh) |
| **Multiple users need access** | Azure AD + SharePoint integration |
| **Single user (you)** | Local upload + GitHub sync (current) |

---

## Recommendation for Your Case:

Since you mentioned users will be "in company office", I recommend:

**Hybrid Solution:**
1. **For you (local)**: Keep current workflow - upload locally, use `push_data.sh`
2. **For others (view-only)**: Access deployed Streamlit app with your uploaded data
3. **If they need to upload**: Add SharePoint browser (Option 1 above)

This way:
- ✅ You control data uploads
- ✅ Others can view latest data
- ✅ Optional: Others can also upload if needed
- ✅ Works with internal SharePoint

---

**Want me to implement the SharePoint integration into your app?** 

Just let me know:
- A) Add SharePoint browser option
- B) Keep current approach (simpler, you have full control)
- C) Show me how to test SharePoint connection first
