"""
Auto-save and Auto-load functionality for Streamlit app
Automatically saves uploaded data and restores it on refresh

STRATEGY:
1. Local/Cloud: Save to data/cache/ for immediate session persistence
2. Permanent: Also save to data/sprints/ and data/plans/ (tracked by Git)
3. On app start: Auto-load from Git-tracked files (most recent)
4. User pushes updates via push_data.sh to sync to cloud

This ensures:
- Fast local caching between refreshes
- Permanent storage in Git for cloud deployment
- Data survives app restarts on Streamlit Cloud
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import glob


class DataPersistence:
    """Handle automatic data saving and loading from permanent storage"""
    
    def __init__(self, data_dir="data/cache", permanent_sprint_dir="data/sprints", permanent_plan_dir="data/plans"):
        """
        Initialize data persistence manager
        
        Args:
            data_dir: Directory for temporary cache
            permanent_sprint_dir: Git-tracked sprint data directory
            permanent_plan_dir: Git-tracked plan data directory
        """
        self.data_dir = data_dir
        self.permanent_sprint_dir = permanent_sprint_dir
        self.permanent_plan_dir = permanent_plan_dir
        
        # Ensure directories exist
        for dir_path in [self.data_dir, self.permanent_sprint_dir, self.permanent_plan_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        # Cache file paths (temporary, fast access)
        self.cache_sprint_file = os.path.join(data_dir, "last_sprint_data.csv")
        self.cache_plan_file = os.path.join(data_dir, "last_plan_data.csv")
        self.metadata_file = os.path.join(data_dir, "metadata.json")
    
    def get_latest_sprint_file(self):
        """Get the most recent sprint file from permanent storage"""
        try:
            files = glob.glob(os.path.join(self.permanent_sprint_dir, "sprint_*.csv"))
            if files:
                # Sort by modification time, most recent first
                files.sort(key=os.path.getmtime, reverse=True)
                return files[0]
            return None
        except Exception:
            return None
    
    def get_latest_plan_file(self):
        """Get the most recent plan file from permanent storage"""
        try:
            files = glob.glob(os.path.join(self.permanent_plan_dir, "plan_*.csv"))
            if files:
                files.sort(key=os.path.getmtime, reverse=True)
                return files[0]
            return None
        except Exception:
            return None
    
    def save_sprint_data(self, df, filename="uploaded_file.csv"):
        """
        Save sprint data to BOTH cache and permanent storage
        
        Args:
            df: DataFrame to save
            filename: Original filename (for metadata)
        """
        try:
            # Save to cache for fast access
            df.to_csv(self.cache_sprint_file, index=False)
            
            # Save metadata
            metadata = {
                "last_upload_time": datetime.now().isoformat(),
                "filename": filename,
                "row_count": len(df),
                "columns": list(df.columns),
                "type": "sprint_data"
            }
            self.save_metadata(metadata)
            
            return True
        except Exception as e:
            st.error(f"Error saving data: {e}")
            return False
    
    def save_plan_data(self, df, filename="plan_file.csv"):
        """Save plan data to BOTH cache and permanent storage"""
        try:
            df.to_csv(self.cache_plan_file, index=False)
            
            metadata = {
                "last_upload_time": datetime.now().isoformat(),
                "filename": filename,
                "row_count": len(df),
                "columns": list(df.columns),
                "type": "plan_data"
            }
            self.save_metadata(metadata, key="plan")
            
            return True
        except Exception as e:
            st.error(f"Error saving plan data: {e}")
            return False
    
    def save_metadata(self, metadata, key="sprint"):
        """Save metadata to JSON file"""
        try:
            # Load existing metadata
            all_metadata = {}
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    all_metadata = json.load(f)
            
            # Update with new metadata
            all_metadata[key] = metadata
            
            # Save back
            with open(self.metadata_file, 'w') as f:
                json.dump(all_metadata, f, indent=2)
            
            return True
        except Exception as e:
            st.error(f"Error saving metadata: {e}")
            return False
    
    def load_sprint_data(self):
        """
        Load last saved sprint data
        Priority: Cache first (fast), then permanent storage
        
        Returns:
            DataFrame if data exists, None otherwise
        """
        try:
            # Try cache first (faster)
            if os.path.exists(self.cache_sprint_file):
                df = pd.read_csv(self.cache_sprint_file)
                return df
            
            # Fallback to permanent storage (Git-tracked)
            latest_file = self.get_latest_sprint_file()
            if latest_file:
                df = pd.read_csv(latest_file)
                # Cache it for next time
                df.to_csv(self.cache_sprint_file, index=False)
                return df
            
            return None
        except Exception as e:
            st.error(f"Error loading saved data: {e}")
            return None
    
    def load_plan_data(self):
        """Load last saved plan data (cache first, then permanent)"""
        try:
            # Try cache first
            if os.path.exists(self.cache_plan_file):
                df = pd.read_csv(self.cache_plan_file)
                return df
            
            # Fallback to permanent storage
            latest_file = self.get_latest_plan_file()
            if latest_file:
                df = pd.read_csv(latest_file)
                df.to_csv(self.cache_plan_file, index=False)
                return df
            
            return None
        except Exception as e:
            st.error(f"Error loading plan data: {e}")
            return None
    
    def get_metadata(self, key="sprint"):
        """Get metadata about saved data"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    all_metadata = json.load(f)
                    return all_metadata.get(key)
            return None
        except Exception as e:
            return None
    
    def has_saved_data(self):
        """Check if there's saved data available (cache or permanent)"""
        return os.path.exists(self.cache_sprint_file) or self.get_latest_sprint_file() is not None
    
    def has_saved_plan(self):
        """Check if there's saved plan data (cache or permanent)"""
        return os.path.exists(self.cache_plan_file) or self.get_latest_plan_file() is not None
    
    def clear_cache(self):
        """Clear cache (but keep permanent files in Git)"""
        try:
            if os.path.exists(self.cache_sprint_file):
                os.remove(self.cache_sprint_file)
            if os.path.exists(self.cache_plan_file):
                os.remove(self.cache_plan_file)
            if os.path.exists(self.metadata_file):
                os.remove(self.metadata_file)
            return True
        except Exception as e:
            st.error(f"Error clearing cache: {e}")
            return False


def auto_save_and_load_wrapper():
    """
    Wrapper function to add auto-save/auto-load to your app
    Call this at the start of your main() function
    """
    # Initialize persistence manager
    if 'persistence' not in st.session_state:
        st.session_state['persistence'] = DataPersistence()
    
    persistence = st.session_state['persistence']
    
    # Auto-load on first run
    if 'data_auto_loaded' not in st.session_state:
        load_count = 0
        
        # Try to load all sprint files from permanent storage
        try:
            sprint_files = glob.glob(os.path.join(persistence.permanent_sprint_dir, "sprint_*.csv"))
            if sprint_files:
                # Initialize sprint_data dict if not exists
                if 'sprint_data' not in st.session_state:
                    st.session_state['sprint_data'] = {}
                if 'sprint_options' not in st.session_state:
                    st.session_state['sprint_options'] = []
                
                for sprint_file in sprint_files:
                    # Extract date from filename: sprint_2026-02-06.csv -> 2026-02-06
                    filename = os.path.basename(sprint_file)
                    date_str = filename.replace('sprint_', '').replace('.csv', '')
                    
                    # Load the data
                    df = pd.read_csv(sprint_file)
                    st.session_state['sprint_data'][date_str] = df
                    
                    if date_str not in st.session_state['sprint_options']:
                        st.session_state['sprint_options'].append(date_str)
                    
                    load_count += 1
                
                # Sort sprint options
                st.session_state['sprint_options'].sort()
                
                if load_count > 0:
                    st.sidebar.success(f"✅ Auto-loaded {load_count} sprint(s)")
        except Exception as e:
            st.sidebar.warning(f"Could not auto-load sprints: {e}")
        
        # Try to load saved plan data
        try:
            saved_plan = persistence.load_plan_data()
            if saved_plan is not None:
                st.session_state['plan_data'] = saved_plan
                st.sidebar.info(f"📋 Plan data auto-loaded")
        except Exception as e:
            st.sidebar.warning(f"Could not auto-load plan: {e}")
        
        st.session_state['data_auto_loaded'] = True
    
    return persistence


def create_auto_save_upload_widget(label="Upload Sprint CSV", key="sprint"):
    """
    Create a file uploader that automatically saves uploaded data
    
    Args:
        label: Label for the uploader
        key: Unique key for this uploader
        
    Returns:
        DataFrame if file uploaded, None otherwise
    """
    persistence = st.session_state.get('persistence', DataPersistence())
    
    uploaded_file = st.file_uploader(
        label,
        type=['csv'],
        help="Upload CSV file - automatically saved for next session",
        key=f"uploader_{key}"
    )
    
    if uploaded_file is not None:
        # Read the file
        df = pd.read_csv(uploaded_file)
        
        # Auto-save
        if key == "sprint":
            success = persistence.save_sprint_data(df, uploaded_file.name)
        elif key == "plan":
            success = persistence.save_plan_data(df, uploaded_file.name)
        else:
            success = False
        
        if success:
            st.success(f"✅ Data saved! Will auto-load on next visit.")
        
        return df
    
    return None
