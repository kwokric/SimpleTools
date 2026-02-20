"""
SharePoint File Loader for Streamlit
Allows users to browse and load files from SharePoint
"""

import streamlit as st
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File
import io
import pandas as pd


class SharePointLoader:
    """Load files from SharePoint"""
    
    def __init__(self, site_url, username=None, password=None):
        """
        Initialize SharePoint connection
        
        Args:
            site_url: SharePoint site URL (e.g., "https://company.sharepoint.com/sites/YourSite")
            username: SharePoint username (optional, can use secrets)
            password: SharePoint password (optional, can use secrets)
        """
        self.site_url = site_url
        self.username = username or st.secrets.get("sharepoint", {}).get("username")
        self.password = password or st.secrets.get("sharepoint", {}).get("password")
        self.ctx = None
        
    def authenticate(self):
        """Authenticate with SharePoint"""
        try:
            auth_ctx = AuthenticationContext(self.site_url)
            if auth_ctx.acquire_token_for_user(self.username, self.password):
                self.ctx = ClientContext(self.site_url, auth_ctx)
                return True
            return False
        except Exception as e:
            st.error(f"Authentication failed: {e}")
            return False
    
    def list_files(self, folder_path="Shared Documents"):
        """
        List files in a SharePoint folder
        
        Args:
            folder_path: Path to folder (e.g., "Shared Documents/JIRA Data")
            
        Returns:
            List of file names
        """
        if not self.ctx:
            if not self.authenticate():
                return []
        
        try:
            folder = self.ctx.web.get_folder_by_server_relative_url(folder_path)
            files = folder.files
            self.ctx.load(files)
            self.ctx.execute_query()
            
            return [f.properties["Name"] for f in files]
        except Exception as e:
            st.error(f"Error listing files: {e}")
            return []
    
    def download_file(self, file_path):
        """
        Download file from SharePoint
        
        Args:
            file_path: Full path to file (e.g., "Shared Documents/data.csv")
            
        Returns:
            File content as bytes
        """
        if not self.ctx:
            if not self.authenticate():
                return None
        
        try:
            response = File.open_binary(self.ctx, file_path)
            return response.content
        except Exception as e:
            st.error(f"Error downloading file: {e}")
            return None
    
    def load_csv_from_sharepoint(self, file_path):
        """
        Load CSV file from SharePoint directly into pandas DataFrame
        
        Args:
            file_path: Full path to CSV file
            
        Returns:
            pandas DataFrame
        """
        content = self.download_file(file_path)
        if content:
            return pd.read_csv(io.BytesIO(content))
        return None


def create_sharepoint_file_browser(site_url, folder_path="Shared Documents"):
    """
    Create a Streamlit file browser for SharePoint
    
    Usage in app.py:
        df = create_sharepoint_file_browser(
            "https://company.sharepoint.com/sites/YourSite",
            "Shared Documents/JIRA Data"
        )
    """
    st.subheader("📁 Browse SharePoint Files")
    
    # Initialize loader
    loader = SharePointLoader(site_url)
    
    # Authentication
    with st.expander("🔐 SharePoint Login", expanded=True):
        use_secrets = st.checkbox("Use saved credentials", value=True)
        
        if not use_secrets:
            username = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if username and password:
                loader.username = username
                loader.password = password
        
        if st.button("Connect to SharePoint"):
            with st.spinner("Connecting..."):
                if loader.authenticate():
                    st.success("✅ Connected!")
                    st.session_state['sharepoint_connected'] = True
                else:
                    st.error("❌ Connection failed")
    
    # File browser
    if st.session_state.get('sharepoint_connected'):
        st.write(f"**Folder:** `{folder_path}`")
        
        with st.spinner("Loading files..."):
            files = loader.list_files(folder_path)
        
        if files:
            # Filter for CSV files
            csv_files = [f for f in files if f.endswith('.csv')]
            
            if csv_files:
                selected_file = st.selectbox(
                    "Select file to load:",
                    csv_files,
                    index=0
                )
                
                if st.button("📥 Load File"):
                    with st.spinner(f"Loading {selected_file}..."):
                        file_path = f"{folder_path}/{selected_file}"
                        df = loader.load_csv_from_sharepoint(file_path)
                        
                        if df is not None:
                            st.success(f"✅ Loaded {len(df)} rows from {selected_file}")
                            return df
            else:
                st.warning("No CSV files found in this folder")
        else:
            st.warning("No files found or unable to access folder")
    
    return None
