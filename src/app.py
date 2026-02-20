import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import sys
import os
import plotly.express as px
import datetime
import webbrowser

# --- Import Adaptation for src/ location ---
# When running from src/, we don't need to append 'src' to path, 
# but if we run from root, we do. 
# Also, 'agents' and 'jira_analyzer' are siblings of app.py in src/.
try:
    from jira_analyzer import JiraAnalyzer
    from alert_logger import AlertLogger
    from agents import BusinessAnalystAgent, ScrumMasterAgent, ProjectManagerAgent
    from data_persistence import DataPersistence, auto_save_and_load_wrapper
except ImportError:
    # If standard import fails, try adding current dir to path (though highly unlikely if running directly)
    sys.path.append(os.path.dirname(__file__))
    try:
        from jira_analyzer import JiraAnalyzer
        from alert_logger import AlertLogger
        from agents import BusinessAnalystAgent, ScrumMasterAgent, ProjectManagerAgent
        from data_persistence import DataPersistence, auto_save_and_load_wrapper
    except ImportError as e:
        st.error(f"Error importing modules: {e}")
        st.stop()

# Hardcoded valid sprints 
FIXED_SPRINTS = []

def main():
    # 1. Critical: This must be the first Streamlit command
    st.set_page_config(page_title="JIRA Sprint Analyzer", layout="wide", page_icon="📊")
    
    # 2. Initialize auto-save/auto-load (loads saved data if available)
    persistence = auto_save_and_load_wrapper()
    
    # --- Custom CSS / HTML Styling ---
    st.markdown("""
        <style>
        /* Global Typography */
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Roboto', sans-serif;
            color: #333333;
            background-color: #ffffff;
        }

        /* Header Styling */
        .main-header {
            padding: 20px 0;
            border-bottom: 1px solid #e0e0e0;
            margin-bottom: 30px;
        }
        .main-header h1 {
            font-family: 'Roboto', sans-serif;
            font-weight: 300;
            color: #1a4d2e; /* Deep Professional Green */
            font-size: 2.5rem;
            margin: 0;
        }
        .sub-header {
            font-size: 1rem;
            color: #666;
            margin-top: 5px;
            font-weight: 300;
        }

        /* KPI Cards */
        .kpi-card {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 0px; /* Sharp edges for professional look */
            padding: 20px;
            border-left: 4px solid #1a4d2e;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .kpi-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #1a4d2e;
            margin-bottom: 5px;
        }
        .kpi-label {
            font-size: 0.85rem;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 500;
        }
        
        /* Metric container styling adjustments */
        [data-testid="stMetricValue"] {
            font-family: 'Roboto', sans-serif;
            color: #1a4d2e;
        }

        /* Custom Button Styling for Drill Down Metrics */
        /* Target buttons that are likely our metric buttons based on context or just style all secondary buttons slightly nicer */
        div.stButton > button {
            border-radius: 4px;
            font-weight: 500;
        }

        /* Specifically target Buttons inside the metrics columns if possible? 
           Streamlit doesn't give easy ID. We will use a specific targeting for the metric Drill Down buttons.
           We can look for buttons that have newlines in them? No. 
           Let's style ALL buttons to be more substantial, or try to be specific.
           Since the user complained about "too small font" and "button too large", 
           let's make the buttons compact but text large.
        */
        
        div[data-testid="column"] div.stButton > button p {
             font-size: 1.2rem !important;
             line-height: 1.4 !important;
        }
        
        div.stButton > button {
            height: auto !important;
            padding-top: 15px !important;
            padding-bottom: 15px !important;
            min-height: 100px; /* Make them square-ish */
            border: 1px solid #d1d5db;
            background-color: #ffffff;
            color: #1a4d2e;
            transition: all 0.2s;
        }
        
        div.stButton > button:hover {
            border-color: #1a4d2e;
            background-color: #f0fdf4;
            color: #14532d;
        }

        /* Reset/Compact style for buttons inside Expanders (like 'Close Details') */
        div[data-testid="stExpander"] div.stButton > button {
            min-height: 0px !important;
            padding-top: 5px !important;
            padding-bottom: 5px !important;
            font-weight: 400 !important;
        }
        div[data-testid="stExpander"] div.stButton > button p {
            font-size: 1rem !important;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #f8f9fa;
            border-right: 1px solid #e0e0e0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # --- Custom Header ---
    st.markdown("""
        <div class="main-header">
            <h1>JIRA Sprint Management & Analysis</h1>
            <div class="sub-header">Strategic Insights & Executive Dashboard</div>
        </div>
    """, unsafe_allow_html=True)


    # --- Session State Initialization ---
    
    # Initialize sprint options if not present
    if 'sprint_options' not in st.session_state:
        st.session_state['sprint_options'] = list(FIXED_SPRINTS)
    
    # FORCE CLEANUP: Remove deprecated or missing sprints
    # Also explicitly remove 2026-01-13 if it lingers in session from previous runs
    for deprecated in ["2026-02-02", "2025-12-30", "2026-01-13"]:
        if deprecated in st.session_state['sprint_options']:
            st.session_state['sprint_options'].remove(deprecated)
    
    # Ensure valid fixed sprints are always present
    for s in FIXED_SPRINTS:
        if s not in st.session_state['sprint_options']:
            st.session_state['sprint_options'].append(s)
            
    # Auto-Cleaning: Remove options that have no corresponding file in data/sprints
    # This prevents "Ghost Sprints" from appearing
    sprint_dirs_check = ["data/sprints", "../data/sprints"]
    existing_sprints_on_disk = []
    
    for d in sprint_dirs_check:
        if os.path.exists(d):
            for f in os.listdir(d):
                if f.startswith("sprint_") and f.endswith(".csv"):
                    s_date = f.replace("sprint_", "").replace(".csv", "")
                    existing_sprints_on_disk.append(s_date)
                    
                    # Missing Step: Ensure discovered on-disk sprints are IN the options list
                    if s_date not in st.session_state['sprint_options']:
                        st.session_state['sprint_options'].append(s_date)
    
    # Filter session options
    # We keep those that are in FIXED_SPRINTS OR exist on disk OR are temporarily in memory (just uploaded)
    st.session_state['sprint_options'] = [
        opt for opt in st.session_state['sprint_options'] 
        if opt in FIXED_SPRINTS or opt in existing_sprints_on_disk or opt in st.session_state.get('sprint_data', {})
    ]

    st.session_state['sprint_options'].sort()

    # Initialize storage for dataframes
    if 'sprint_data' not in st.session_state:
        st.session_state['sprint_data'] = {}

    # --- Sidebar Controls ---
    st.sidebar.header("Configuration")

    # --- ADMIN ACCESS ---
    is_admin = False
    # Use environment variable or Streamlit secrets for password (with fallback)
    try:
        ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD") or st.secrets.get("general", {}).get("ADMIN_PASSWORD", "admin123")
    except:
        # Fallback if secrets.toml doesn't exist (local development)
        ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    
    with st.sidebar.expander("🔐 Admin Access", expanded=False):
        admin_password = st.text_input("Enter Admin Password", type="password")
        if admin_password == ADMIN_PASSWORD:
            is_admin = True
            st.success("Admin Unlocked")
        else:
            if admin_password:
                st.error("Incorrect Password")

    # Reset Button (Admin)
    if is_admin:
        if st.sidebar.button("⚠️ Clear Cache & Restart"):
            st.session_state.clear()
            st.rerun()

    st.sidebar.markdown("---")

    # --- SPRINT DATA UPLOAD ---
    st.sidebar.subheader("📤 Upload Sprint Data")
    
    # 1. File
    uploaded_file = st.sidebar.file_uploader("Sprint JIRA Export (CSV)", type=['csv'])
    
    # 2. Target Sprint Definition (For Upload)
    # Default to a sane value, but allow user to pick a new date to create a new sprint
    default_upload_target = datetime.date.today()
    # Try to grab the latest sprint from valid options as default
    if st.session_state['sprint_options']:
        try:
             latest = st.session_state['sprint_options'][-1]
             default_upload_target = pd.to_datetime(latest).date()
        except: pass
        
    upload_target_date = st.sidebar.date_input("Target Sprint End Date", value=default_upload_target, key="upload_target_date_input", help="The End Date of the Sprint you are uploading data for.")
    upload_target_str = upload_target_date.strftime('%Y-%m-%d')
    
    # 3. Snapshot Date (highlighted in red)
    st.sidebar.markdown("<p style='color: red; font-weight: bold; margin-bottom: 0;'>📅 Data Snapshot Date *</p>", unsafe_allow_html=True)
    snapshot_date = st.sidebar.date_input("Date", value=datetime.date.today(), help="When was this data exported?", label_visibility="collapsed", key="snapshot_date_input")
    
    # 4. Optional: Start Date Override (Stored in session / metadata if possible)
    # We can infer it (End - 14 days) or let user set it. 
    # Calculation: If End is Friday (4), Start should be Monday (0) -> End - 11.
    # If End is Monday (0), Start should be Monday (0) -> End - 14.
    # General formula for "Monday Start ~2 weeks ago":
    # delta = (upload_target_date.weekday() - 0) % 7 + 7  -> This gives 1 week back. Add 7 for 2 weeks?
    # Actually simple logic:
    if upload_target_date.weekday() == 4: # Friday
        def_start_delta = 11
    else:
        def_start_delta = 14 # Fallback
        
    upload_start_date = st.sidebar.date_input("Sprint Start Date", value=upload_target_date - datetime.timedelta(days=def_start_delta), key="upload_start_date_input")

    # --- VALIDATION LOGIC ---
    validation_errors = []
    
    # Check 1: Friday
    if upload_target_date.weekday() != 4: # 0=Mon, 4=Fri
        validation_errors.append(f"❌ Target End Date ({upload_target_str}) is {upload_target_date.strftime('%A')}, should be Friday.")
        
    # Check 2: Monday
    if upload_start_date.weekday() != 0:
        validation_errors.append(f"❌ Sprint Start Date ({upload_start_date.strftime('%Y-%m-%d')}) is {upload_start_date.strftime('%A')}, should be Monday.")
    
    # Check 3: New Sprint Detection
    is_new_sprint = upload_target_str not in st.session_state['sprint_options']
    confirm_new = True
    
    if is_new_sprint:
        st.sidebar.warning(f"🆕 New Sprint: {upload_target_str}")
        confirm_new = st.sidebar.checkbox("✅ Confirm creating new sprint?", value=False)
        if not confirm_new:
             st.sidebar.caption("Please check the box to proceed.")
             # We make this one blocking because it's a specific confirm action
             # can_upload = False # Actually, let's just warn to avoid getting stuck
            
    # Display Validation Blocking Errors -> Changed to WARNINGS (User Override)
    can_upload = True
    if validation_errors:
        for err in validation_errors:
            st.sidebar.warning(err)
            # st.sidebar.caption("⚠️ Proceed only if you are sure.")
        # can_upload = False # Disabled blocking
        
    if is_new_sprint and not confirm_new:
        can_upload = False

    # --- PLAN DATA UPLOAD (Collapsible) ---
    with st.sidebar.expander("📤 Upload Plan Data", expanded=False):
        uploaded_plan_file = st.file_uploader("Plan Excel/CSV", type=['xlsx', 'xls', 'csv'], key="plan_file_uploader")
        st.markdown("<p style='color: red; font-weight: bold; margin-bottom: 0;'>📅 Plan Snapshot Date *</p>", unsafe_allow_html=True)
        plan_snapshot_date = st.date_input("Date", value=datetime.date.today(), key="plan_snapshot", label_visibility="collapsed")
    
    # Initialize Alert Logger
    alert_logger = AlertLogger()

    # --- PROCESS BUTTON (Now accessible to everyone or keep Admin?) ---
    # User requested: "Allow user to add new sprints"
    # Previously restricted to Admin. I will keep it restricted as per existing logic unless asked to open it.
    # But wait, user said "It should allow user to add new sprints". 
    # If I am not Admin, I can't upload. This is a blocker if User isn't logged in.
    # I will assume User is logged in or I should make it open. 
    # Given the instructions, I'll keep Admin check for safety but emphasize it.
    
    if is_admin:
        if st.sidebar.button("Process & Update", type="primary", disabled=not can_upload):
            # 1. Process Sprint Data
            if uploaded_file is not None:
                st.session_state['just_uploaded'] = True
                try:
                    df = pd.read_csv(uploaded_file)
                    # Store data in session state using UPLOAD TARGET
                    st.session_state['sprint_data'][upload_target_str] = df
                    
                    # Store Start Date in Session for immediate view
                    st.session_state[f"start_date_{upload_target_str}"] = upload_start_date
                    
                    # Update options list
                    if upload_target_str not in st.session_state['sprint_options']:
                        st.session_state['sprint_options'].append(upload_target_str)
                        st.session_state['sprint_options'].sort()
                    
                    # FORCE VIEW SWITCH to the new/updated sprint
                    st.session_state['main_sprint_selection'] = upload_target_str
                    
                    # --- NEW: Process Data & Update History ---
                    temp_analyzer = JiraAnalyzer(df, sprint_end_date=upload_target_str)
                    temp_analyzer.append_to_history(snapshot_date, upload_target_str)
                    st.session_state['sprint_data'][upload_target_str] = temp_analyzer.df

                    # --- STANDARDIZED STORAGE ---
                    base_data_dir = "data/sprints"
                    if not os.path.exists("data") and os.path.exists("../data"): base_data_dir = "../data/sprints"
                    if not os.path.exists(base_data_dir):
                        try: os.makedirs(base_data_dir)
                        except: pass
                        
                    save_path = os.path.join(base_data_dir, f"sprint_{upload_target_str}.csv")
                    temp_analyzer.df.to_csv(save_path, index=False)
                    st.success(f"Sprint Data Saved: {save_path}")
                    
                    # AUTO-SAVE: Save to cache for auto-load on refresh
                    persistence.save_sprint_data(temp_analyzer.df, uploaded_file.name)

                except Exception as e:
                    st.error(f"Error: {e}")

            # 2. Process Plan Data
            if uploaded_plan_file is not None:
                try:
                    if uploaded_plan_file.name.endswith('.csv'):
                        new_plan_df = pd.read_csv(uploaded_plan_file)
                    else:
                        new_plan_df = pd.read_excel(uploaded_plan_file)
                    
                    # --- INTELLIGENT MERGE LOGIC ---
                    # 1. Load Existing Data
                    existing_plan_df = None
                    plan_data_dir = "data/plans"
                    if not os.path.exists("data") and os.path.exists("../data"): plan_data_dir = "../data/plans"
                    
                    if os.path.exists(plan_data_dir):
                        files = [f for f in os.listdir(plan_data_dir) if f.startswith('plan_') and (f.endswith('.csv') or f.endswith('.xlsx'))]
                        if files:
                            files.sort(reverse=True)
                            latest = os.path.join(plan_data_dir, files[0])
                            try:
                                if latest.endswith('.csv'): existing_plan_df = pd.read_csv(latest)
                                else: existing_plan_df = pd.read_excel(latest)
                            except: pass

                    # 2. Key Normalization helper
                    def get_key_col(df):
                        for k in ['Epic Key', 'Issue key', 'Key', 'Epic']:
                            if k in df.columns: return k
                        return None
                    
                    if existing_plan_df is not None:
                         new_key = get_key_col(new_plan_df)
                         old_key = get_key_col(existing_plan_df)
                         
                         if new_key and old_key:
                             # Columns to preserve from OLD data if they exist
                             # These are fields users manually edit in the tool
                             preserve_cols = ['Business Purpose', 'Start Date', 'Estimated Start Date', 'Planned End Date', 'Business Value', 'Purpose']
                             
                             # Convert to dictionaries for fast lookup
                             # { 'KEY-123': { 'Business Purpose': 'XYZ', ... } }
                             old_data_map = existing_plan_df.set_index(old_key).to_dict('index')
                             
                             # Iterate new data and inject old values
                             for idx, row in new_plan_df.iterrows():
                                 key_val = row[new_key]
                                 if key_val in old_data_map:
                                     old_row = old_data_map[key_val]
                                     for col in preserve_cols:
                                         if col in old_row and col in new_plan_df.columns:
                                             # Logic: If New is Empty/NaN and Old has Value, user logic implies we Keep Old
                                             # OR: Always prefer Old for these manual columns? 
                                             # "User does not need to enter values again" -> Keep old value
                                             val = old_row[col]
                                             if pd.notna(val) and str(val).strip() != "":
                                                 new_plan_df.at[idx, col] = val
                                         elif col in old_row and col not in new_plan_df.columns:
                                             # If column was missing in new upload but existed in old (e.g. purely manual column), add it
                                             new_plan_df.at[idx, col] = old_row[col]

                    st.session_state['plan_data'] = new_plan_df
                    st.session_state['plan_snapshot_date'] = plan_snapshot_date
                    
                    if not os.path.exists(plan_data_dir):
                        try: os.makedirs(plan_data_dir, exist_ok=True)
                        except: pass
                    
                    plan_save_path = os.path.join(plan_data_dir, f"plan_{plan_snapshot_date}.csv")
                    new_plan_df.to_csv(plan_save_path, index=False)
                    st.success(f"Plan Saved (Merged with previous data): {plan_save_path}")
                    
                    # AUTO-SAVE: Save to cache for auto-load on refresh
                    persistence.save_plan_data(new_plan_df, uploaded_plan_file.name)
                    
                except Exception as e:
                    st.error(f"Error: {e}")
            
            if uploaded_file or uploaded_plan_file:
                 st.rerun()

    else:
        st.sidebar.info("🔒 Admin Access required to upload/process data.")
        
    # Compat: Define target_date_str for downstream logic using Main Selection
    # If 'main_sprint_selection' is set (which is the View Selector), use that.
    # Otherwise fallback to latest.
    
    if st.session_state['sprint_options']:
        fallback = st.session_state['sprint_options'][-1]
    else:
        fallback = datetime.date.today().strftime('%Y-%m-%d')
        
    # Get value, handle case where key exists but value is None (empty selectbox)
    target_date_str = st.session_state.get('main_sprint_selection')
    if not target_date_str:
        target_date_str = fallback
    
    # Backport "Sprint Start Date" logic for the View
    # If we stored it during upload, retrieve it. Else calculate default.
    # Default logic: If End Date is Friday, Start is usually Monday 11 days prior (2 weeks).
    # If End Date is not Friday, fallback to 14 days.
    
    default_start_date = datetime.date.today() - datetime.timedelta(days=14)
    if target_date_str:
        try:
             t_dt = pd.to_datetime(target_date_str)
             if t_dt.weekday() == 4: # Friday
                 delta = 11
             else:
                 delta = 14
             default_start_date = t_dt - datetime.timedelta(days=delta)
        except:
             pass

    sprint_start_date = st.session_state.get(f"start_date_{target_date_str}", default_start_date)

    
    # Main Logic for Alerts Display (moved logic here)
    if 'sprint_data' not in st.session_state:
        st.session_state['sprint_data'] = {}
        
    sprint_opts = st.session_state['sprint_options']
    # If session state has no default, set it
    if 'main_sprint_selection' not in st.session_state:
        # Default to whatever matches target_date_str if possible
        if target_date_str in sprint_opts:
             st.session_state['main_sprint_selection'] = target_date_str
        elif sprint_opts:
             st.session_state['main_sprint_selection'] = sprint_opts[-1]

    # --- Auto-load Logic (New & Legacy) ---
    # Load logic depends on what is selected.
    # Effectively override target_date_str with the selection from main area if it exists
    # But wait, sidebar input drives target_date_str. 
    # Let's make main_sprint_selection DRIVE target_date_str visually? 
    # Streamlit limitation: Can't easily update sidebar widget from main widget without rerun loop.
    # Approach: Use main selection as the SOURCE OF TRUTH for data display.
    
    selected_sprint = st.session_state.get('main_sprint_selection', target_date_str)
    
    # Ensure data is loaded for selected sprint
    if selected_sprint not in st.session_state['sprint_data']:
        # 1. Try New Managed Path First
        base_data_dir = "data/sprints"
        if not os.path.exists("data") and os.path.exists("../data"):
             base_data_dir = "../data/sprints"
        
        managed_path = os.path.join(base_data_dir, f"sprint_{selected_sprint}.csv")
        
        # 2. Legacy Fallback
        legacy_path = None
        auto_load_map = {
            "2026-01-13": "data/Jan12.csv"
        }
        if selected_sprint in auto_load_map:
            l_name = auto_load_map[selected_sprint]
            legacy_path = f"../{l_name}" if not os.path.exists(l_name) else l_name
        
        # Load logic
        target_path = None
        if os.path.exists(managed_path):
             target_path = managed_path
        elif legacy_path and os.path.exists(legacy_path):
             target_path = legacy_path
             
        if target_path:
            try:
                df_local = pd.read_csv(target_path)
                # Clean again just to be safe (though stored files should be ok)
                temp_analyzer = JiraAnalyzer(df_local, sprint_end_date=selected_sprint)
                st.session_state['sprint_data'][selected_sprint] = temp_analyzer.df
                st.rerun()
            except Exception as e:
                pass


    # --- Main Content ---
    
    # Retrieve data for current view
    current_df = st.session_state['sprint_data'].get(selected_sprint)
    
    # Initialize Analyzer
    analyzer = None
    if current_df is not None:
        if current_df.empty:
            st.error("⚠️ Data Loaded but DataFrame is Empty. Check file format.")
        analyzer = JiraAnalyzer(current_df, sprint_end_date=selected_sprint)

    if analyzer:
        # Use custom HTML success message or keep standard st.success
        st.success(f"Viewing Sprint Data: {selected_sprint}")
        
        tab1, tab3, tab4, tab5 = st.tabs(["Sprint Dashboard", "Detail Data", "Plan Management", "Plan Management (New)"])

        with tab1:
            # Layout: Header + Sprint Selector
            c_head, c_sel = st.columns([3, 1])
            with c_head:
                st.markdown("### Sprint Overview")
            with c_sel:
                # MAIN SPRINT SELECTOR
                # Updates 'main_sprint_selection' in session state, triggering re-run with new data
                st.selectbox(
                    "Sprint", 
                    options=st.session_state['sprint_options'], 
                    key="main_sprint_selection"
                )

            metrics = analyzer.calculate_metrics()
            
            # --- Layout Change: Metrics + Pie Chart on same row ---
            # Columns: 2/3 for Metrics, 1/3 for Pie Chart
            col_metrics, col_pie = st.columns([2, 1])

            with col_metrics:
                # Interactive Metrics Drill-down
                # Replaced st.metric with st.button to allow "click to see details"
                m1, m2 = st.columns(2)
                m3, m4 = st.columns(2)
                
                v_stories = metrics.get('total_stories', 0)
                v_points = metrics.get('total_points', 0)
                v_complete = metrics.get('completed_points', 0)
                v_carry = metrics.get('carry_over_points', 0)
                
                # Use double newlines for spacing between Label and Value
                if m1.button(f"Total Stories\n\n{v_stories}", key="btn_drill_stories", use_container_width=True):
                    st.session_state['metric_drill_active'] = 'stories'
                
                if m2.button(f"Total Points\n\n{v_points}", key="btn_drill_points", use_container_width=True):
                    st.session_state['metric_drill_active'] = 'points'

                if m3.button(f"Completed Points\n\n{v_complete}", key="btn_drill_complete", use_container_width=True):
                    st.session_state['metric_drill_active'] = 'completed'

                if m4.button(f"Remaining Points\n\n{v_carry}", key="btn_drill_carry", use_container_width=True):
                    st.session_state['metric_drill_active'] = 'carryover'
            
            with col_pie:
                if 'Status' in current_df.columns:
                    fig_pie = px.pie(current_df, names='Status', title=f'Status Distribution', height=300)
                    fig_pie.update_layout(margin=dict(t=30, b=0, l=0, r=0))
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("No Status column.")

            # --- Drill Down Details Section ---
            if st.session_state.get('metric_drill_active'):
                view_key = st.session_state['metric_drill_active']
                
                with st.expander(f"🔍 Drill Down: {view_key.replace('_',' ').title()}", expanded=True):
                    # Filter Logic
                    drill_df = current_df.copy()
                    
                    # 1. Base Filter (Work Items)
                    if 'Issue Type' in drill_df.columns:
                        drill_df = drill_df[~drill_df['Issue Type'].isin(['Epic', 'Sub-task'])]

                    # 2. Specific Filters
                    done_set = ['Done', 'Resolved', 'Closed']
                    if view_key == 'completed':
                        if 'Status' in drill_df.columns:
                            drill_df = drill_df[drill_df['Status'].isin(done_set)]
                    elif view_key == 'carryover':
                        if 'Status' in drill_df.columns:
                            drill_df = drill_df[~drill_df['Status'].isin(done_set)]
                    elif view_key == 'stories':
                        pass # All work items
                    elif view_key == 'points':
                        # All work items (points are summed from them)
                        pass

                    # --- FILTER LOGIC (Replicated from Detail Data) ---
                    st.markdown("##### Filter Results")
                    cols_to_filter = st.multiselect(
                        "Add Filters", 
                        [c for c in drill_df.columns if c not in ['Issue id', 'Parent', 'Assignee Id']], # Exclude IDs
                        key=f"drill_cols_filter_{view_key}"
                    )
                    
                    if cols_to_filter:
                        cols_ui = st.columns(3)
                        for i, col in enumerate(cols_to_filter):
                            col_ui = cols_ui[i % 3]
                            with col_ui:
                                # 1. Numeric Filtering
                                if pd.api.types.is_numeric_dtype(drill_df[col]):
                                    # Handle NaN or empty series
                                    if drill_df[col].dropna().empty:
                                         st.caption(f"**{col}**: No valid data")
                                         continue

                                    min_v = float(drill_df[col].min())
                                    max_v = float(drill_df[col].max())
                                    
                                    if min_v == max_v:
                                        st.caption(f"**{col}**: Constant ({min_v})")
                                    else:
                                        st.markdown(f"**{col}**")
                                        rng = st.slider(
                                            f"Range", 
                                            min_v, max_v, (min_v, max_v), 
                                            key=f"drill_filter_num_{view_key}_{col}",
                                            label_visibility="collapsed"
                                        )
                                        drill_df = drill_df[drill_df[col].between(rng[0], rng[1])]
                                
                                # 2. Categorical Filtering
                                else:
                                    unique_vals = sorted(drill_df[col].astype(str).unique())
                                    st.markdown(f"**{col}**")
                                    
                                    if len(unique_vals) > 50: # Simpler threshold
                                         search_txt = st.text_input(
                                             f"Search", 
                                             key=f"drill_filter_txt_{view_key}_{col}",
                                             label_visibility="collapsed"
                                         )
                                         if search_txt:
                                             drill_df = drill_df[
                                                 drill_df[col].astype(str).str.contains(search_txt, case=False, na=False)
                                             ]
                                    else:
                                        sel_vals = st.multiselect(
                                            f"Values", 
                                            unique_vals, 
                                            placeholder="All", 
                                            key=f"drill_filter_cat_{view_key}_{col}",
                                            label_visibility="collapsed"
                                        )
                                        if sel_vals:
                                            drill_df = drill_df[drill_df[col].astype(str).isin(sel_vals)]
                                            
                    # Display
                    d_cols = ['Issue key', 'Summary', 'Status', 'Custom field (Story Points)', 'Assignee', 'Priority']
                    
                    # Add any columns currently being filtered to the view so user can see what they are doing
                    if cols_to_filter:
                         for c in cols_to_filter:
                             if c not in d_cols:
                                 d_cols.append(c)

                    d_cols = [c for c in d_cols if c in drill_df.columns]
                    
                    st.dataframe(drill_df[d_cols], use_container_width=True, hide_index=True)
                    
                    if st.button("Close Details", key="btn_close_drill"):
                        del st.session_state['metric_drill_active']
                        st.rerun()

            st.markdown("---")

            # --- Visualizations Section ---
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown("### Sprint Burndown")
                # Try to load history for Burndown
                history_path = "data/burndown_history.csv"
                # Adjustment for running from src/
                if not os.path.exists(history_path):
                     history_path = "../data/burndown_history.csv"
                
                has_history = False
                if os.path.exists(history_path):
                    try:
                        hist_df = pd.read_csv(history_path)
                        hist_df['Date'] = pd.to_datetime(hist_df['Date'])
                        
                        # Filter for current selected sprint
                        sprint_data = hist_df[hist_df['Sprint End Date'] == target_date_str].sort_values('Date')
                        
                        if not sprint_data.empty:
                            has_history = True
                            
                            # Convert to Days directly for plotting
                            sprint_data['Remaining Estimate (Days)'] = sprint_data['Remaining Estimate'] / 28800

                            # Create Ideal Line
                            # Start: Users Sprint Start Date OR Earliest data point
                            # End: Sprint End Date -> 0
                            
                            start_date = pd.to_datetime(sprint_start_date)
                            # Fallback if start date is after first data point? 
                            # Usually Ideal Line starts at Sprint Start.
                            
                            end_date = pd.to_datetime(target_date_str)
                            
                            # If user set a weird start date (e.g. after end date), fallback to auto
                            if start_date >= end_date:
                                start_date = sprint_data['Date'].min()
                                if (end_date - start_date).days < 1:
                                     start_date = end_date - pd.Timedelta(days=14)

                            # Determine max y value (Estimate)
                            max_est = sprint_data['Remaining Estimate (Days)'].max()
                            
                            fig_burn = px.line(sprint_data, x='Date', y='Remaining Estimate (Days)', title="Burndown Velocity (Days)", markers=True)
                            
                            # Add ideal line
                            fig_burn.add_scatter(x=[start_date, end_date], y=[max_est, 0], mode='lines', name='Ideal Guideline', line=dict(dash='dash', color='gray'))
                            
                            st.plotly_chart(fig_burn, use_container_width=True)
                        else:
                            st.info("No historical data points yet for this sprint.")
                    except Exception as e:
                        st.error(f"Could not load burndown history: {e}")
                
                if not has_history:
                     st.caption("Burndown chart requires historical data points in 'data/burndown_history.csv'.")

            with c2:
                st.markdown("### Resource Utilization")
                workload_data = analyzer.generate_workload_chart_data()
                
                if workload_data is not None and not workload_data.empty:
                    # --- Graph 1: Remaining Estimate ---
                    # Filter for items with remaining work
                    # Debug: Check if we have data
                    # st.write(f"DEBUG: Loaded {len(workload_data)} rows. Max Rem: {workload_data['Remaining (Days)'].max()}")

                    df_rem = workload_data[workload_data['Remaining (Days)'] > 0.01].copy() # Filter small float noise
                    
                    if not df_rem.empty:
                        fig_rem = px.bar(df_rem, x='Assignee', y='Remaining (Days)', color='Issue key',
                                        title="1. Future Workload: Remaining Estimate (Days)",
                                        text='Remaining (Days)')
                        
                        # FORCE alphabetic order on X axis
                        fig_rem.update_layout(xaxis={'categoryorder':'category ascending'}, showlegend=True, legend_title_text='Ticket', height=400, clickmode='event+select')
                        
                        fig_rem.update_traces(textposition='inside', texttemplate='%{text:.1f}')
                        
                        # Enable Selection
                        # Dynamic key based on sprint to ensure refresh on switch
                        sel_rem = st.plotly_chart(fig_rem, use_container_width=True, on_select="rerun", key=f"chart_rem_select_{selected_sprint}")
                        
                        # Handle Click with JS redirection
                        if sel_rem and "selection" in sel_rem and "rows" in sel_rem["selection"]:
                            rows = sel_rem["selection"]["rows"]
                            if rows:
                                try:
                                    # Get first selected item's index
                                    row_idx = rows[0]
                                    selected_row = df_rem.iloc[row_idx]
                                    issue_key_sel = selected_row['Issue key']
                                    
                                    last_key = st.session_state.get('last_opened_rem', None)
                                    
                                    if issue_key_sel != last_key:
                                        st.session_state['last_opened_rem'] = issue_key_sel
                                        jira_url = f"https://manulife-gwam.atlassian.net/browse/{issue_key_sel}"
                                        
                                        # Visual Feedback & Backup Link
                                        st.toast(f"Opening {issue_key_sel}...", icon="🔗")
                                        st.markdown(f"**🔗 Opening {issue_key_sel}...** [Click here if not redirected]({jira_url})")

                                        # Method 1: Python Webbrowser (Best for Localhost)
                                        try:
                                            webbrowser.open_new_tab(jira_url)
                                        except:
                                            pass
                                            
                                        # Method 2: JS Fallback (Best for Cloud)
                                        js = f"window.open('{jira_url}', '_blank').focus();"
                                        components.html(f"<script>{js}</script>", height=0)
                                    else:
                                        # Persistent link if already selected
                                        jira_url = f"https://manulife-gwam.atlassian.net/browse/{issue_key_sel}"
                                        st.markdown(f"Selected: [{issue_key_sel}]({jira_url})")

                                except:
                                    pass # Ignore indexing errors
                            else:
                                # Deselection occurred
                                st.session_state['last_opened_rem'] = None
                    else:
                        st.info("No remaining work to display.")

                    # --- Graph 2: Time Spent ---
                    # Filter for items with time spent
                    df_spent = workload_data[workload_data['Spent (Days)'] > 0.01].copy()
                    
                    if not df_spent.empty:
                        fig_spent = px.bar(df_spent, x='Assignee', y='Spent (Days)', color='Issue key',
                                        title="2. Completed Work: Time Spent (Days)",
                                        text='Spent (Days)')
                        
                        # FORCE alphabetic order on X axis
                        fig_spent.update_layout(xaxis={'categoryorder':'category ascending'}, showlegend=True, legend_title_text='Ticket', height=400, clickmode='event+select')
                        
                        fig_spent.update_traces(textposition='inside', texttemplate='%{text:.1f}')
                        
                        # Enable Selection
                        # Dynamic key based on sprint to ensure refresh on switch
                        sel_spent = st.plotly_chart(fig_spent, use_container_width=True, on_select="rerun", key=f"chart_spent_select_{selected_sprint}")
                        
                        # Handle Click with JS redirection
                        if sel_spent and "selection" in sel_spent and "rows" in sel_spent["selection"]:
                            rows = sel_spent["selection"]["rows"]
                            if rows:
                                try:
                                    row_idx = rows[0]
                                    selected_row = df_spent.iloc[row_idx]
                                    issue_key_sel = selected_row['Issue key']
                                    
                                    last_key = st.session_state.get('last_opened_spent', None)
                                    
                                    if issue_key_sel != last_key:
                                        st.session_state['last_opened_spent'] = issue_key_sel
                                        jira_url = f"https://manulife-gwam.atlassian.net/browse/{issue_key_sel}"
                                        
                                        # Visual Feedback & Backup Link
                                        st.toast(f"Opening {issue_key_sel}...", icon="🔗")
                                        st.markdown(f"**🔗 Opening {issue_key_sel}...** [Click here if not redirected]({jira_url})")

                                        # Method 1: Python Webbrowser
                                        try:
                                            webbrowser.open_new_tab(jira_url)
                                        except:
                                            pass
                                            
                                        # Method 2: JS Fallback
                                        js = f"window.open('{jira_url}', '_blank').focus();"
                                        components.html(f"<script>{js}</script>", height=0)
                                    else:
                                        jira_url = f"https://manulife-gwam.atlassian.net/browse/{issue_key_sel}"
                                        st.markdown(f"Selected: [{issue_key_sel}]({jira_url})")
                                except:
                                    pass
                            else:
                                st.session_state['last_opened_spent'] = None
                    else:
                        st.info("No time spent recorded yet.")
                
                elif 'Assignee' in current_df.columns:
                    # Fallback to simple bar if detailed data gen fails
                    # Group by Assignee
                    # Check for Story Points col
                    sp_col = 'Custom field (Story Points)'
                    if sp_col not in current_df.columns:
                         # Fallback
                         cols = [c for c in current_df.columns if 'Story Points' in c]
                         if cols: sp_col = cols[0]
                    
                    if sp_col in current_df.columns:
                        # Ensure numeric
                        current_df[sp_col] = pd.to_numeric(current_df[sp_col], errors='coerce').fillna(0)
                        
                        resource_df = current_df.groupby('Assignee')[sp_col].sum().reset_index()
                        resource_df = resource_df.sort_values(sp_col, ascending=True)
                        
                        fig_res = px.bar(resource_df, x=sp_col, y='Assignee', orientation='h', 
                                         title="Workload by Assignee (Story Points)",
                                         text=sp_col)
                        fig_res.update_traces(marker_color='#1a4d2e') # Professional green
                        st.plotly_chart(fig_res, use_container_width=True)
                    else:
                        st.info("Story Points column not found for resource chart.")
                else:
                    st.info("Assignee column not found.")

            st.markdown("---")
            
            # --- Workload Alerts & Risk Section (Restored) ---
            
            # Header with Help Button using Columns
            # Tighter columns to place button next to title
            c_head, c_btn, c_rest = st.columns([3, 1.5, 7])
            with c_head:
                st.subheader("Workload Alerts")
                # Removed caption "Estimate Exceed" to move it to logic area for alignment
            with c_btn:
                st.write("") # Vertical spacer for alignment
                if st.button("❓ Rules", key="btn_wa_rules"):
                    st.session_state['show_wa_rules'] = not st.session_state.get('show_wa_rules', False)
            
            # Show Help Text if toggled
            if st.session_state.get('show_wa_rules', False):
                st.info("""
                **⚠️ Workload Alerts (Potential Underestimated Tickets):**
                *   **Metric**: Ticket Estimates vs Story Points.
                *   **Alerts**: 
                    1. **Remaining > SP**: If Remaining Estimate > Story Points.
                    2. **Spent > SP**: If Time Spent > Story Points.
                
                **🔥 At Risk Items Logic:**
                *   **Criteria**:
                    1.  **Priority**: 'Critical' or 'Blocker' (and not Done).
                    2.  **Estimate Blowout**: Status Not Done AND (Time Spent + Remaining) > Story Points.
                """)
            
            # Risk Count KPI in a box
            col_alerts, col_risk_list = st.columns([1, 1])
            
            with col_alerts:
                 # Check Ticket Alerts
                 alerts_df = analyzer.check_ticket_alerts()
                 alert_logger = AlertLogger()
                 
                 # Logic for counts
                 active_count = 0
                 active_alerts_list = []
                 dismissed_recurring_list = []
                 
                 if alerts_df is not None and not alerts_df.empty:
                     alerts_df = alerts_df.sort_values(by=['Assignee', 'Issue key'])
                     alert_logger.log_alerts_to_file(alerts_df)
                     
                     for idx, row in alerts_df.iterrows():
                         key = row['Issue key']
                         a_type = row['Alert Type']
                         if alert_logger.is_dismissed(key, a_type):
                             dismissed_recurring_list.append(row)
                         else:
                             active_alerts_list.append(row)
                     
                     active_count = len(active_alerts_list)

                 # --- Display Alignment: Metric Header ---
                 st.metric("ESTIMATE EXCEED", active_count)
                 
                 if alerts_df is not None and not alerts_df.empty:
                     # Check visibility context
                     show_all = st.session_state.get('just_uploaded', False)
                     
                     # 1. Show Active Alerts (Dismissable with Remarks)
                     if active_alerts_list:
                         st.error(f"⚠️ Action Required: {active_count} Alerts")
                         for row in active_alerts_list:
                             c1, c2 = st.columns([4, 1])
                             c1.markdown(f"**{row['Assignee']}** | {row['Issue key']} | {row['Alert Type']} | {row['Details']}")
                             
                             # Dismissal with Remarks Popup
                             with c2.popover("Dismiss", use_container_width=True):
                                 st.write("Confirm Dismissal")
                                 remarks_input = st.text_input("Remarks / Reason:", key=f"dsm_rem_{row['Issue key']}_{row['Alert Type']}")
                                 if st.button("Confirm", key=f"dsm_conf_{row['Issue key']}_{row['Alert Type']}"):
                                     alert_logger.dismiss_alert(row['Issue key'], row['Alert Type'], remarks=remarks_input)
                                     st.rerun()
                     
                     # 2. Show Recurring/Dismissed if "Repopup" mode (New Upload)
                     if show_all and dismissed_recurring_list:
                         st.warning(f"Previously Closed Alerts (Recurring): {len(dismissed_recurring_list)}")
                         st.caption("These alerts were previously dismissed but are still present in the new data.")
                         if st.button("Ignore All Recurring", key="ign_all"):
                             st.session_state['just_uploaded'] = False
                             st.rerun()
                             
                         df_rec = pd.DataFrame(dismissed_recurring_list)
                         st.dataframe(df_rec[['Assignee', 'Issue key', 'Alert Type', 'Details']], hide_index=True)
                     
                     if not active_alerts_list and not (show_all and dismissed_recurring_list):
                         st.success("No active alerts.")
                 else:
                     st.success("No workload alerts detected.")
                 
                 # 3. Reference: Historical Closed Alerts (Always Visible if any exist)
                 all_dism = alert_logger.get_all_dismissed_alerts()
                 if all_dism:
                     with st.expander("Historical Closed Alerts"):
                         d_df = pd.DataFrame(all_dism)
                         # Reformat for display
                         if not d_df.empty:
                             # Display nicer column names
                             d_df_disp = d_df.rename(columns={
                                 "issue_key": "Issue Key",
                                 "alert_type": "Alert Type",
                                 "remarks": "Remarks",
                                 "dismissed_at": "Dismissed Date",
                                 "dismissed_by": "User"
                             })
                             # Select columns to show
                             cols_show = ["Issue Key", "Alert Type", "Remarks", "Dismissed Date"]
                             # Safe select
                             cols_show = [c for c in cols_show if c in d_df_disp.columns]
                             st.dataframe(d_df_disp[cols_show], hide_index=True, use_container_width=True)

            with col_risk_list:
                # At Risk Count
                risk_count = analyzer.get_at_risk_count()
                st.metric("AT RISK ITEMS", risk_count)
                
                # Table of risks
                risk_items = analyzer.get_at_risk_items()
                if not risk_items.empty:
                    st.dataframe(risk_items, hide_index=True)

            st.markdown("---")

            # --- Data Management Section ---
            with st.expander("Manage Data Sources & History"):
                tab_src, tab_hist, tab_plans = st.tabs(["Sprint Data Files", "Burndown History", "Plan Data Files"])
                
                # Tab 1: Sprint Data Files (data/sprints/ and root data/)
                with tab_src:
                    st.write("Manage stored CSV files for individual sprints.")
                    
                    # Directories to check
                    dirs_to_check = []
                    
                    # 1. New Sprints Directory
                    base_data_dir = "data/sprints"
                    base_root_dir = "data"
                    if not os.path.exists("data") and os.path.exists("../data"):
                         base_data_dir = "../data/sprints"
                         base_root_dir = "../data"
                    
                    # Create if not exists (for new folder)
                    if not os.path.exists(base_data_dir):
                        try:
                            os.makedirs(base_data_dir)
                        except: pass
                    
                    all_files = []
                    
                    # Gather from New Folder
                    if os.path.exists(base_data_dir):
                        for f in os.listdir(base_data_dir):
                            if f.endswith('.csv'):
                                all_files.append({'File': f, 'Location': 'Sprints Folder', 'Path': os.path.join(base_data_dir, f)})

                    # Gather from Root Folder (Legacy) - Excluding history/configs
                    exclude = ['burndown_history.csv', 'upload_history.csv', 'Sample Input.csv']
                    if os.path.exists(base_root_dir):
                        for f in os.listdir(base_root_dir):
                            if f.endswith('.csv') and f not in exclude:
                                all_files.append({'File': f, 'Location': 'Legacy/Root', 'Path': os.path.join(base_root_dir, f)})
                    
                    if all_files:
                         files_df = pd.DataFrame(all_files)[['File', 'Location']]
                         st.dataframe(files_df, use_container_width=True)
                         
                         # Delete Interface (Admin Only)
                         if is_admin:
                             file_options = {f"{f['File']} ({f['Location']})": f['Path'] for f in all_files}
                             to_delete_key = st.selectbox("Select file to delete:", ["Select..."] + list(file_options.keys()))
                             
                             if st.button("Delete File"):
                                 if to_delete_key != "Select..." and to_delete_key in file_options:
                                     path_to_del = file_options[to_delete_key]
                                     try:
                                        os.remove(path_to_del)
                                        st.success(f"Deleted {path_to_del}")
                                        st.rerun()
                                     except Exception as e:
                                         st.error(f"Error deleting file: {e}")
                         else:
                             st.caption("🔒 File deletion restricted to Admin.")
                    else:
                        st.info("No stored sprint files found.")

                # Tab 2: Burndown History
                with tab_hist:
                    st.write("Historical data used for the Burndown chart.")
                    history_path = "data/burndown_history.csv"
                    if not os.path.exists(history_path):
                         history_path = "../data/burndown_history.csv" # Fallback
                    
                    if os.path.exists(history_path):
                        hist_df = pd.read_csv(history_path)
                        
                        # Add delete buttons
                        # To effectively manage, user selects rows to delete
                        st.dataframe(hist_df)
                        
                        # Delete UI (Admin Only)
                        if is_admin:
                            with st.form("delete_history_form"):
                                st.write("Select snapshot date to remove:")
                                dates_to_remove = st.multiselect("Select Dates", hist_df['Date'].unique())
                                if st.form_submit_button("Delete Selected Records"):
                                    if dates_to_remove:
                                        new_hist_df = hist_df[~hist_df['Date'].isin(dates_to_remove)]
                                        new_hist_df.to_csv(history_path, index=False)
                                        st.success(f"Deleted records for: {', '.join(dates_to_remove)}")
                                        st.rerun()
                        else:
                            st.caption("🔒 History modification restricted to Admin.")
                    else:
                        st.info("No history file found.")

                # Tab 3: Plan Files
                with tab_plans:
                     st.write("Manage stored Plan Data files.")
                     plan_data_dir = "data/plans"
                     if not os.path.exists("data") and os.path.exists("../data"):
                        plan_data_dir = "../data/plans"
                     
                     if os.path.exists(plan_data_dir):
                         plan_files = [f for f in os.listdir(plan_data_dir) if f.endswith('.csv') or f.endswith('.xlsx')]
                         if plan_files:
                             p_df = pd.DataFrame(plan_files, columns=["Filename"])
                             st.dataframe(p_df, use_container_width=True)
                             
                             if is_admin:
                                 to_del_plan = st.selectbox("Delete Plan File:", ["Select..."] + plan_files)
                                 if st.button("Delete Plan"):
                                     if to_del_plan != "Select...":
                                         try:
                                             os.remove(os.path.join(plan_data_dir, to_del_plan))
                                             st.success(f"Deleted {to_del_plan}")
                                             st.rerun()
                                         except Exception as e:
                                             st.error(f"Error: {e}")
                             else:
                                 st.caption("🔒 Admin only.")
                         else:
                             st.info("No plan files found.")
                     else:
                         st.info("Plan directory not found (no files uploaded yet).")

        with tab3:
            st.markdown("### Detailed Data View")
            
            # --- Dynamic Filtering ---
            # Initialize filtered_df with the full dataset
            df_filtered = current_df.copy()

            # --- Column Cleanup for Display ---
            # Remove requested columns if they exist
            cols_to_remove = [
                'Issue id', 'Parent', 'Assignee Id', 
                'Remaining Estimate', 'Time Spent'
            ]
            # Case-insensitive removal
            existing_cols = df_filtered.columns
            drop_cols = []
            for col in existing_cols:
                if col in cols_to_remove: # Exact match
                    drop_cols.append(col)
                # Or specific partial matches if needed, but User gave specific names.
                # Let's try to match exact names User provided, assuming standard Jira CSV.
            
            if drop_cols:
                df_filtered = df_filtered.drop(columns=drop_cols)

            # Filter Expander
            with st.expander("🔍 Filter Data", expanded=False):
                st.caption("Select columns to add filters:")
                cols_to_filter = st.multiselect(
                    "Select Columns to Filter", 
                    df_filtered.columns, 
                    key="filter_cols_multiselect"
                )
                
                if cols_to_filter:
                    st.divider()
                    # Use 3 columns for layout
                    cols_ui = st.columns(3)
                    
                    for i, col in enumerate(cols_to_filter):
                        col_ui = cols_ui[i % 3]
                        with col_ui:
                            # 1. Numeric Filtering
                            if pd.api.types.is_numeric_dtype(df_filtered[col]):
                                min_v = float(df_filtered[col].min())
                                max_v = float(df_filtered[col].max())
                                
                                if min_v == max_v:
                                    st.caption(f"**{col}**: Constant ({min_v})")
                                else:
                                    st.markdown(f"**{col}**")
                                    rng = st.slider(
                                        f"Range", 
                                        min_v, max_v, (min_v, max_v), 
                                        key=f"filter_{col}",
                                        label_visibility="collapsed"
                                    )
                                    df_filtered = df_filtered[df_filtered[col].between(rng[0], rng[1])]
                            
                            # 2. Categorical Filtering
                            else:
                                unique_vals = sorted(df_filtered[col].astype(str).unique())
                                st.markdown(f"**{col}**")
                                
                                # Use Text Search if cardinality is high (> 200)
                                if len(unique_vals) > 200:
                                     search_txt = st.text_input(
                                         f"Search...", 
                                         key=f"filter_{col}",
                                         label_visibility="collapsed"
                                     )
                                     if search_txt:
                                         df_filtered = df_filtered[
                                             df_filtered[col].astype(str).str.contains(search_txt, case=False, na=False)
                                         ]
                                else:
                                    sel_vals = st.multiselect(
                                        f"Values", 
                                        unique_vals, 
                                        placeholder="All", 
                                        key=f"filter_{col}",
                                        label_visibility="collapsed"
                                    )
                                    if sel_vals:
                                        df_filtered = df_filtered[df_filtered[col].astype(str).isin(sel_vals)]

            # Show Data with Row Count
            st.dataframe(df_filtered, use_container_width=True)
            st.info(f"**Total Rows:** {len(df_filtered)}")

        with tab4:
             # --- AUTO-LOAD LOGIC FOR PLAN DATA ---
             # If no plan data in session, try to load the most recent file from data/plans
             if st.session_state.get('plan_data') is None:
                 plan_dirs = ["data/plans", "../data/plans"]
                 plan_dir = next((d for d in plan_dirs if os.path.exists(d)), None)
                 
                 if plan_dir:
                     files = [f for f in os.listdir(plan_dir) if f.startswith('plan_') and (f.endswith('.csv') or f.endswith('.xlsx'))]
                     if files:
                         files.sort(reverse=True) # Sort desc to get latest date (assuming YYYY-MM-DD in name)
                         latest_file = files[0]
                         latest_path = os.path.join(plan_dir, latest_file)
                         try:
                             if latest_path.endswith('.csv'):
                                st.session_state['plan_data'] = pd.read_csv(latest_path)
                             else:
                                st.session_state['plan_data'] = pd.read_excel(latest_path)
                             
                             # Extract date from filename if possible plan_2026-01-26.csv
                             try:
                                p_date = latest_file.replace("plan_", "").split(".")[0]
                                st.session_state['plan_snapshot_date'] = p_date
                             except:
                                pass
                         except: 
                             pass

             # IMPORTANT: Work on a COPY for display to avoid forcing implicit updates 
             # on the persistent session object every render interactively
             plan_df_session = st.session_state.get('plan_data')
             plan_df = plan_df_session.copy() if plan_df_session is not None else None

             if plan_df is not None:
                st.subheader("Plan Management (Epics)")
                
                # --- 1. DATA PREPARATION & NORMALIZATION ---
                # Map potential upload columns to our internal standard
                # Standard: 'Epic Key', 'Epic Name', 'Start Date', 'Estimated Start Date', 'Planned End Date', 'Business Purpose'
                
                col_map = {
                    'Issue key': 'Epic Key',
                    'Key': 'Epic Key',
                    'Parent key': 'Epic Key', # Only if it's the direct list of Epics
                    'Summary': 'Epic Name',
                    'Epic': 'Epic Name',
                    'Feature': 'Epic Name',
                    'Start Date': 'Start Date',
                    'Estimated Start Date': 'Estimated Start Date',
                    'Delivery Date': 'Planned End Date',
                    'Planned End Date': 'Planned End Date',
                    'Planned End': 'Planned End Date',
                    'Business Purpose': 'Business Purpose',
                    'Purpose': 'Business Purpose',
                    'Business Value': 'Business Purpose',
                    'Custom field (Story Points)': 'Story Points',
                    'Story Points': 'Story Points',
                    'Status': 'Status',
                    'Priority': 'Priority'
                }
                
                # Normalize columns with Duplicate Prevention
                # We do a two-pass approach:
                # 1. Map columns if target doesn't exist
                # 2. If target exists, merge/drop source
                
                for src, dest in col_map.items():
                    if src in plan_df.columns:
                        if src == dest:
                            continue
                            
                        if dest in plan_df.columns:
                            # Target already exists. 
                            # Fill NaNs in Target with Source data
                            plan_df[dest] = plan_df[dest].fillna(plan_df[src])
                            # Drop source to avoid duplication
                            plan_df.drop(columns=[src], inplace=True)
                        else:
                            # Safe rename
                            plan_df.rename(columns={src: dest}, inplace=True)
                
                # Check for any remaining duplicates (just in case)
                plan_df = plan_df.loc[:, ~plan_df.columns.duplicated()]

                # Identify Sprint Columns (Column P onwards, usually 'Custom field (Quarter Plan)')
                sprint_cols = [c for c in plan_df.columns if 'Quarter Plan' in str(c)]
                assignee_cols = ['Assignee'] if 'Assignee' in plan_df.columns else []
                
                # Define Display Order: Sprints -> Assignee -> Status -> Dates -> Purpose
                # Epic Key and Epic Name will be moved to INDEX to freeze them.
                # Define Display Order: Epic Name + Sprints -> Assignee -> Status -> Dates -> Purpose
                # Epic Key will be moved to INDEX to freeze it (or prepended if not frozen)
                # Added 'Delete' mainly for manual removal
                display_cols = ['Epic Name', 'Delete', 'Priority', 'Story Points'] + sprint_cols + assignee_cols + ['Status', 'Start Date', 'Estimated Start Date', 'Planned End Date', 'Business Purpose']
                
                # Ensure all required columns exist
                required_cols = ['Epic Key', 'Epic Name', 'Story Points', 'Status', 'Start Date', 'Estimated Start Date', 'Planned End Date', 'Business Purpose', 'Priority']
                for c in required_cols:
                    if c not in plan_df.columns:
                        if c == 'Priority':
                            plan_df[c] = 'Medium'
                        else:
                            plan_df[c] = None 
                
                # Force Date Types for standardization
                date_cols = ['Start Date', 'Estimated Start Date', 'Planned End Date']
                # Add Milestone Date (Flag)
                if 'Milestone Date' not in plan_df.columns:
                    plan_df['Milestone Date'] = pd.NaT
                date_cols.append('Milestone Date')
                
                for dc in date_cols:
                    plan_df[dc] = pd.to_datetime(plan_df[dc], errors='coerce')
                
                # Force String Type for Text Editor Columns to prevent StreamlitAPIException
                # Especially for dynamic sprint columns which might contain NaNs (floats)
                for c in sprint_cols:
                    if c in plan_df.columns:
                        plan_df[c] = plan_df[c].astype(str).replace('nan', '')
                
                if assignee_cols and assignee_cols[0] in plan_df.columns:
                    plan_df[assignee_cols[0]] = plan_df[assignee_cols[0]].astype(str).replace('nan', '')
                
                plan_df['Business Purpose'] = plan_df['Business Purpose'].astype(str).replace('nan', '')
                plan_df['Status'] = plan_df['Status'].astype(str).replace('nan', '')
                plan_df['Epic Name'] = plan_df['Epic Name'].astype(str).replace('nan', '')
                
                # Add Delete Column (Checkbox)
                if 'Delete' not in plan_df.columns:
                    plan_df['Delete'] = False

                # Fill Epic Key/Name if missing (sanity check)
                if 'Epic Key' not in plan_df.columns:
                    # If completely missing, use index? 
                    plan_df['Epic Key'] = [f"EPIC-{i}" for i in range(len(plan_df))]
                
                # --- 2. EDITOR TABLE ---
                st.markdown("### 📝 Edit Plan")
                st.caption("'Epic Key' is frozen. Scroll right to edit other columns.")
                
                # Freeze Columns: Set Epic Key as Index
                # Streamlit data_editor does not support MultiIndex, so we can only freeze one column cleanly.
                if 'Epic Key' in plan_df.columns:
                     try:
                         # Check for duplicates because data_editor needs unique index for reliable editing
                         if plan_df['Epic Key'].duplicated().any():
                             # If duplicates exist, we can't use it as a safe index for editing without losing row tracking
                             # Fallback: Just display normally without freeze, or use internal index
                             st.warning("⚠️ Duplicate Epic Keys found. Freezing disabled to prevent data loss.")
                             plan_df_editor = plan_df
                             # Add Epic Key back to display cols if not frozen
                             if 'Epic Key' not in display_cols:
                                 display_cols = ['Epic Key'] + display_cols
                         else:
                             plan_df_editor = plan_df.set_index('Epic Key')
                     except:
                         plan_df_editor = plan_df
                         if 'Epic Key' not in display_cols:
                             display_cols = ['Epic Key'] + display_cols
                else:
                     plan_df_editor = plan_df
                     if 'Epic Key' not in display_cols:
                             display_cols = ['Epic Key'] + display_cols

                # Configure the editor
                editor_config = {
                        "Epic Key": st.column_config.TextColumn("Epic Key", width="medium", help="Unique ID (e.g., JIRA Key)", required=True),
                        "Epic Name": st.column_config.TextColumn("Epic Name", width=400, help="Description or Summary"),
                        "Delete": st.column_config.CheckboxColumn("🗑️", help="Select to remove this item", width="small", default=False),
                        "Story Points": st.column_config.NumberColumn("Story Points", width="small", help="Effort Estimate"),
                        "Status": st.column_config.TextColumn("Status", width="medium", help="Current Status"),
                        "Priority": st.column_config.SelectboxColumn(
                            "Priority", 
                            width="small", 
                            options=["Critical", "High", "Medium", "Low"],
                            required=True,
                            help="Strategic Priority Level"
                        ),
                        "Start Date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD"),
                        "Estimated Start Date": st.column_config.DateColumn("Est. Start Date", format="YYYY-MM-DD"),
                        "Planned End Date": st.column_config.DateColumn("Planned End Date", format="YYYY-MM-DD"),
                        "Milestone Date": st.column_config.DateColumn("🚩 Milestone", format="YYYY-MM-DD", help="Date for Red Flag indicator"),
                        "Business Purpose": st.column_config.TextColumn("Business Purpose", width="large", help="Strategic Value"),
                }
                
                # Dynamic sprint columns configuration
                # Sort sprint_cols to ensure order if pandas didn't preserve it (usually does)
                # Assuming standard naming: '...Plan)', '...Plan).1', '...Plan).2'
                
                # Counter for display labels: Quarter Plan 1, Quarter Plan 2...
                qp_counter = 1
                
                for c in sprint_cols:
                    # Logic: If it contains "Quarter Plan", we want sequential numbering "Quarter Plan 1", "Quarter Plan 2"...
                    if "Quarter Plan" in c:
                         final_label = f"Quarter Plan {qp_counter}"
                         qp_counter += 1
                    else:
                         # Fallback for other 'Custom fields'
                         final_label = c.replace("Custom field (", "").replace(")", "").strip()
                    
                    editor_config[c] = st.column_config.TextColumn(final_label, width="medium")

                if assignee_cols:
                    editor_config['Assignee'] = st.column_config.TextColumn("Assignee", width="medium", help="Owner")

                edited_df = st.data_editor(
                    plan_df_editor,
                    key="plan_editor_table",
                    num_rows="dynamic", # Allow adding rows manually
                    column_config=editor_config,
                    column_order=display_cols, # Show specific order with sprints and assignee
                    use_container_width=True
                )
                
                # SAVE BUTTON
                if st.button("💾 Save Changes", type="primary"):
                    # Update session state with edited data
                    # IMPORTANT: Reset index to get 'Epic Key' and 'Epic Name' back as columns before saving
                    final_df = edited_df.reset_index()
                    
                    # PROCESS DELETION
                    if 'Delete' in final_df.columns:
                        deleted_count = final_df['Delete'].sum()
                        if deleted_count > 0:
                            st.toast(f"🗑️ Deleting {deleted_count} items...")
                            final_df = final_df[~final_df['Delete']]
                        # Drop the helper column
                        final_df = final_df.drop(columns=['Delete'])

                    st.session_state['plan_data'] = final_df
                    
                    # Save to Disk
                    plan_dir = "data/plans"
                    if not os.path.exists("data") and os.path.exists("../data"): plan_dir = "../data/plans"
                    if not os.path.exists(plan_dir): 
                        try: os.makedirs(plan_dir)
                        except: pass
                    
                    # Construct filename
                    snap_date = st.session_state.get('plan_snapshot_date', str(datetime.date.today()))
                    # Sanitize if needed
                    save_path = os.path.join(plan_dir, f"plan_{snap_date}.csv")
                    
                    try:
                        final_df.to_csv(save_path, index=False)
                        st.success(f"✅ Plan successfully saved to `{save_path}`!")
                        # Rerun to refresh any dependent views
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save plan: {e}")

                st.markdown("---")

                # --- 3. GANTT CHART & BUSINESS PURPOSE ---
                st.markdown("### 📅 Roadmap Visualization")
                
                # Priority Definition Legend
                with st.expander("ℹ️ Priority Definitions & Criteria", expanded=False):
                    st.markdown("""
                    **Strategic Classification Rules:**
                    *   **🔴 Critical**: Urgent **BoW (Book of Work)** items, mandatory **Compliance/Regulatory** deadlines, or system stability blockers.
                    *   **🟠 High**: Top production issues, fixes involving significant manual effort reduction, or key deliverables approaching deadline.
                    *   **🔵 Medium**: Standard roadmap features, technical debt retirement, UX enhancements.
                    *   **🟢 Low**: Minor cosmetic changes, internal tools, or nice-to-have items.
                    """)

                c_gantt, c_side = st.columns([3, 1])
                
                with c_gantt:
                    # Prepare Gantt Data
                    # Logic: Plot_Start = Start Date -> Est Start -> (Planned End - 14)
                    # IMPORTANT: Reset index because 'Epic Key' might be frozen in the index, 
                    # but Plotly Express needs it as a column.
                    g_df = edited_df.reset_index().copy()
                    
                    # --- Data Preparation for Gantt ---
                    # 1. Determine Plot_Start based on Start Date or Estimated Start Date
                    g_df['Plot_Start'] = g_df['Start Date'].fillna(g_df['Estimated Start Date'])

                    # 2. Handle missing End Date: If Start exists but End is missing, assume 30 days duration
                    mask_no_end = g_df['Planned End Date'].isna() & g_df['Plot_Start'].notna()
                    if mask_no_end.any():
                        g_df.loc[mask_no_end, 'Planned End Date'] = g_df.loc[mask_no_end, 'Plot_Start'] + pd.Timedelta(days=30)
                    
                    # 3. Handle missing Start Date: If End exists but Start is missing, assume 14 days duration
                    g_df['Plot_Start'] = g_df['Plot_Start'].fillna(g_df['Planned End Date'] - pd.Timedelta(days=14))
                    
                    # 4. Filter out rows that still lack necessary date info
                    g_df = g_df.dropna(subset=['Plot_Start', 'Planned End Date'])
                    
                    if not g_df.empty:
                        
                        # Formatting for Tooltip
                        g_df['Business Purpose'] = g_df['Business Purpose'].fillna('N/A')
                        
                        # Determine Color based on Time Status
                        # Green: Still within time range (Today <= Planned End Date)
                        # Red: Past expected time (Today > Planned End Date)
                        
                        now = pd.Timestamp.now().normalize()
                        
                        def get_time_status(row):
                            end_d = row['Planned End Date']
                            if pd.isna(end_d):
                                return 'Unknown'
                            if end_d < now:
                                return 'Past Due'
                            return 'On Track'

                        g_df['Time_Status'] = g_df.apply(get_time_status, axis=1)

                        # --- Visualization Controls ---
                        # Toggle between Status Color and Priority Color
                        g_view_mode = st.radio("🎨 Color Scheme", ["Priority Level", "Timeline Status"], horizontal=True, label_visibility="collapsed")

                        import plotly.graph_objects as go # Ensure go is available

                        # Define Colors
                        if g_view_mode == "Priority Level":
                            # Ensure Priority column exists and fill defaults if missing
                            if 'Priority' not in g_df.columns:
                                g_df['Priority'] = 'Medium'
                            g_df['Priority'] = g_df['Priority'].fillna('Medium')
                                
                            color_col = "Priority"
                            color_map = {
                                'Critical': '#d32f2f', # Strong Red
                                'High': '#f57c00',     # Orange
                                'Medium': '#1976d2',   # Blue
                                'Low': '#388e3c',      # Green
                                'None': '#9e9e9e'      # Grey
                            }
                        else:
                            color_col = "Time_Status"
                            color_map = {'On Track': '#2ecc71', 'Past Due': '#e74c3c', 'Unknown': '#95a5a6'}

                        fig_gantt = px.timeline(
                            g_df, 
                            x_start="Plot_Start", 
                            x_end="Planned End Date", 
                            y="Epic Name",
                            color=color_col, # Dynamic Color Column
                            color_discrete_map=color_map,
                            text="Epic Key", # Display Epic Key in bars
                            hover_data=["Epic Key", "Priority", "Start Date", "Estimated Start Date", "Planned End Date", "Business Purpose", "Time_Status"],
                            title="Strategic Timeline"
                        )
                        
                        # Add Flags (Milestones)
                        if 'Milestone Date' in g_df.columns:
                            # Filter for valid dates
                            flags_df = g_df.dropna(subset=['Milestone Date']).copy()
                            if not flags_df.empty:
                                fig_gantt.add_trace(
                                    go.Scatter(
                                        x=flags_df['Milestone Date'],
                                        y=flags_df['Epic Name'],
                                        mode='markers',
                                        marker=dict(symbol='flag', size=14, color='red'),
                                        name='Milestone',
                                        hovertemplate="<b>Milestone:</b> %{x|%Y-%m-%d}<extra></extra>"
                                    )
                                )

                        # Layout tweaks - Matching the "Clean Grid" style
                        fig_gantt.update_traces(
                            textposition='inside',
                            marker_line_color='rgb(255, 255, 255)', 
                            marker_line_width=1, 
                            opacity=0.9,
                            selector=dict(type='bar') # Apply only to bars, not flags
                        )
                        
                        fig_gantt.update_yaxes(
                            categoryorder="total ascending", 
                            autorange="reversed",
                            showgrid=True,
                            gridcolor='#E5E5E5',
                            gridwidth=1,
                            tickson="boundaries" # Lines between rows
                        ) 
                        
                        # Standard Simple X-Axis (Months)
                        fig_gantt.update_xaxes(
                            range=["2025-12-01", "2026-12-31"], 
                            dtick="M1", 
                            tickformat="%b", # Just Month Name
                            side="top", 
                            showgrid=True,
                            gridcolor='#E5E5E5',
                            gridwidth=1,
                        )
                        
                        # Dynamic height
                        chart_height = max(400, len(g_df) * 40)
                        
                        fig_gantt.update_layout(
                            height=chart_height,
                            xaxis_title=None, 
                            yaxis_title=None,
                            showlegend=False,
                            plot_bgcolor='white', 
                            margin=dict(t=60, b=20), 
                            font=dict(family="Arial", size=12)
                        )
                        st.plotly_chart(fig_gantt, use_container_width=True)
                    else:
                        st.info("Insufficient data for Gantt Chart (Requires at least 'Planned End Date').")
                
                with c_side:
                    st.markdown("#### Business Purpose")
                    # Display a clean list of Epic -> Purpose
                    if not edited_df.empty:
                        # Filter to just Name and Purpose
                        purpose_df = edited_df[['Epic Name', 'Business Purpose']].copy()
                        purpose_df = purpose_df.dropna(subset=['Business Purpose'])
                        purpose_df = purpose_df[purpose_df['Business Purpose'] != '']
                        
                        if not purpose_df.empty:
                            st.dataframe(
                                purpose_df,
                                hide_index=True,
                                use_container_width=True
                            )
                        else:
                            st.caption("No Business Purposes defined yet.")
                    else:
                        st.caption("No data.")

                st.markdown("---")

                # --- 4. ALERT SESSION (Bottom) ---
                st.subheader("🚨 Plan Health & Alerts")
                st.caption("Automated checks against Jira Sprint Data and Planning Rules.")
                
                col_cross, col_logic = st.columns(2)
                
                # A. Cross Check with Sprint Data (Missing Epics)
                with col_cross:
                    st.markdown("##### Jira Sync Check")
                    if current_df is not None and 'Parent key' in current_df.columns and 'Parent summary' in current_df.columns:
                        # 1. Get unique parent keys from active sprint
                        active_sprint_parents = current_df[['Parent key', 'Parent summary']].dropna().drop_duplicates()
                        
                        # 2. Get existing keys in Plan
                        # Ensure string comparison
                        # Use reset_index() if 'Epic Key' is the index
                        temp_plan_df = edited_df.reset_index()
                        if 'Epic Key' in temp_plan_df.columns:
                            plan_keys = set(temp_plan_df['Epic Key'].dropna().astype(str).unique())
                        else:
                            plan_keys = set()
                        
                        # 3. Find diff
                        # Filter out empty keys
                        active_sprint_parents = active_sprint_parents[active_sprint_parents['Parent key'] != '']
                        
                        # Identify missing
                        missing_mask = ~active_sprint_parents['Parent key'].astype(str).isin(plan_keys)
                        missing_epics = active_sprint_parents[missing_mask]
                        
                        if not missing_epics.empty:
                            st.error(f"Found {len(missing_epics)} Epics in current Jira Sprint NOT in Plan.")
                            st.dataframe(missing_epics, hide_index=True, use_container_width=True)
                            
                            # Add Button
                            if st.button("➕ Add Missing Epics to Plan"):
                                new_entries = []
                                for _, row in missing_epics.iterrows():
                                    new_entries.append({
                                        'Epic Key': row['Parent key'],
                                        'Epic Name': row['Parent summary'],
                                        'Start Date': None,
                                        'Estimated Start Date': None,
                                        'Planned End Date': None,
                                        'Business Purpose': 'Imported from Sprint'
                                    })
                                
                                # Append to st.session_state['plan_data'] (which is source for edited_df next run)
                                # We need to update the source DF, not just the edited view (which is downstream)
                                # IMPORTANT: reset_index() on edited_df because 'Epic Key' might be frozen in the index
                                new_df_chunk = pd.DataFrame(new_entries)
                                if 'Epic Key' not in edited_df.columns and 'Epic Key' == edited_df.index.name:
                                     source_df = edited_df.reset_index()
                                else:
                                     source_df = edited_df
                                     
                                updated_plan = pd.concat([source_df, new_df_chunk], ignore_index=True)
                                
                                st.session_state['plan_data'] = updated_plan
                                st.success("Epics added! Please review and click 'Save Changes' at the top.")
                                st.rerun()
                        else:
                            st.success("✅ All Epics from current Sprint are covered in the Plan.")
                    else:
                        st.info("Jira Sprint Data not loaded or missing 'Parent key' column for sync check.")

                # B. Date Logic Checks
                with col_logic:
                    st.markdown("##### Timeline Validation")
                    today = pd.Timestamp(datetime.date.today())
                    
                    # Logic 1: Est Start Passed & No Start Date
                    # "Estimated Start Date is due but no value for Start Date"
                    mask_late = (edited_df['Estimated Start Date'] < today) & (edited_df['Start Date'].isna())
                    late_epics = edited_df[mask_late]
                    
                    if not late_epics.empty:
                        st.warning(f"⚠️ **{len(late_epics)} Epics** have passed Est. Start Date but haven't started.")
                        st.dataframe(
                            late_epics[['Epic Name', 'Estimated Start Date']], 
                            hide_index=True,
                            use_container_width=True
                        )
                    else:
                        st.success("✅ No 'Fail to Start' alerts.")
                    
                    # Logic 2: Planned End Date < 5 Working Days
                    # "Planned End Date is less than 5 wd comparing to today"
                    # Using calendar days approximation: 5 WD ~ 7 Calendar Days
                    # Also check if it's in the future (0 to 7 days)
                    
                    mask_impending = (
                        (edited_df['Planned End Date'] >= today) & 
                        (edited_df['Planned End Date'] <= today + pd.Timedelta(days=7))
                    )
                    # Optionally include Overdue? "less than 5 wd" implies proximity. 
                    # If it's already passed (negative), it's definitely less than 5 wd.
                    mask_overdue = (edited_df['Planned End Date'] < today)
                    
                    impending_epics = edited_df[mask_impending | mask_overdue]
                    
                    if not impending_epics.empty:
                        st.warning(f"🔥 **{len(impending_epics)} Epics** are due soon (< 5 WD) or overdue.")
                        st.dataframe(
                            impending_epics[['Epic Name', 'Planned End Date']], 
                            hide_index=True, 
                            use_container_width=True
                        )
                    else:
                        st.success("✅ No immediate deadlines (< 5 working days).")

             else:
                st.info("ℹ️ Please upload a 'Plan mgmt Excel' file in the sidebar to view data here.")

        with tab5:
             # --- NEW ENHANCED PLAN MANAGEMENT TAB ---
             st.markdown("### 🚀 Plan Management (Enhanced)")
             st.caption("New features: Progress tracking, Health status, Quick edit panel, and Backlog view")
             
             # --- AUTO-LOAD LOGIC FOR PLAN DATA ---
             if st.session_state.get('plan_data') is None:
                 plan_dirs = ["data/plans", "../data/plans"]
                 plan_dir = next((d for d in plan_dirs if os.path.exists(d)), None)
                 
                 if plan_dir:
                     files = [f for f in os.listdir(plan_dir) if f.startswith('plan_') and (f.endswith('.csv') or f.endswith('.xlsx'))]
                     if files:
                         files.sort(reverse=True)
                         latest_file = files[0]
                         latest_path = os.path.join(plan_dir, latest_file)
                         try:
                             if latest_file.endswith('.csv'):
                                 st.session_state['plan_data'] = pd.read_csv(latest_path)
                             else:
                                 st.session_state['plan_data'] = pd.read_excel(latest_path)
                             
                             snap_date_str = latest_file.replace('plan_', '').replace('.csv', '').replace('.xlsx', '')
                             st.session_state['plan_snapshot_date'] = pd.to_datetime(snap_date_str).date()
                         except Exception as e:
                             st.error(f"Error loading plan: {e}")

             plan_df_session = st.session_state.get('plan_data')
             plan_df = plan_df_session.copy() if plan_df_session is not None else None

             if plan_df is not None:
                # --- 1. DATA PREPARATION & NORMALIZATION ---
                col_map = {
                    'Issue key': 'Epic Key',
                    'Key': 'Epic Key',
                    'Parent key': 'Epic Key',
                    'Summary': 'Epic Name',
                    'Epic': 'Epic Name',
                    'Feature': 'Epic Name',
                    'Start Date': 'Start Date',
                    'Estimated Start Date': 'Estimated Start Date',
                    'Delivery Date': 'Planned End Date',
                    'Planned End Date': 'Planned End Date',
                    'Planned End': 'Planned End Date',
                    'Business Purpose': 'Business Purpose',
                    'Purpose': 'Business Purpose',
                    'Business Value': 'Business Purpose',
                    'Custom field (Story Points)': 'Story Points',
                    'Story Points': 'Story Points',
                    'Status': 'Status',
                    'Priority': 'Priority'
                }
                
                for src, dest in col_map.items():
                    if src in plan_df.columns:
                        if src == dest:
                            continue
                        if dest in plan_df.columns:
                            plan_df[dest] = plan_df[dest].fillna(plan_df[src])
                            plan_df.drop(columns=[src], inplace=True)
                        else:
                            plan_df.rename(columns={src: dest}, inplace=True)
                
                plan_df = plan_df.loc[:, ~plan_df.columns.duplicated()]

                sprint_cols = [c for c in plan_df.columns if 'Quarter Plan' in str(c)]
                assignee_cols = ['Assignee'] if 'Assignee' in plan_df.columns else []
                
                required_cols = ['Epic Key', 'Epic Name', 'Story Points', 'Status', 'Start Date', 'Estimated Start Date', 'Planned End Date', 'Business Purpose', 'Priority']
                for c in required_cols:
                    if c not in plan_df.columns:
                        if c == 'Priority':
                            plan_df[c] = 'Medium'
                        elif c == 'Status':
                            plan_df[c] = 'Backlog'
                        else:
                            plan_df[c] = None
                
                # Force Date Types
                date_cols = ['Start Date', 'Estimated Start Date', 'Planned End Date']
                if 'Milestone Date' not in plan_df.columns:
                    plan_df['Milestone Date'] = pd.NaT
                date_cols.append('Milestone Date')
                
                for dc in date_cols:
                    plan_df[dc] = pd.to_datetime(plan_df[dc], errors='coerce')
                
                # String conversions
                for c in sprint_cols:
                    if c in plan_df.columns:
                        plan_df[c] = plan_df[c].astype(str).replace('nan', '')
                
                if assignee_cols and assignee_cols[0] in plan_df.columns:
                    plan_df[assignee_cols[0]] = plan_df[assignee_cols[0]].astype(str).replace('nan', '')
                
                plan_df['Business Purpose'] = plan_df['Business Purpose'].astype(str).replace('nan', '')
                plan_df['Status'] = plan_df['Status'].astype(str).replace('nan', '')
                plan_df['Epic Name'] = plan_df['Epic Name'].astype(str).replace('nan', '')
                plan_df['Priority'] = plan_df['Priority'].astype(str).replace('nan', 'Medium')

                if 'Epic Key' not in plan_df.columns:
                    plan_df['Epic Key'] = [f"EPIC-{i}" for i in range(len(plan_df))]

                # --- 2. PROGRESS CALCULATION ---
                def calculate_progress(status):
                    """Map Status to Progress %"""
                    status_map = {
                        'Funnel': 0,
                        'Backlog': 0,
                        'Definition': 10,
                        'Implementing': 30,
                        'Validating': 70,
                        'Done': 100
                    }
                    return status_map.get(status, 0)
                
                plan_df['Progress'] = plan_df['Status'].apply(calculate_progress)

                # --- 3. ENHANCED GANTT CHART ---
                st.markdown("### 📅 Enhanced Roadmap")
                
                with st.expander("ℹ️ Priority Definitions & Health Status Logic", expanded=False):
                    st.markdown("""
                    **Priority Levels:**
                    *   **🔴 Critical**: BoW items, Compliance/Regulatory deadlines, system stability blockers.
                    *   **🟠 High**: Top production issues, significant manual effort reduction.
                    *   **🔵 Medium**: Standard roadmap features, technical debt.
                    *   **🟢 Low**: Minor changes, internal tools.
                    
                    **Health Status (Bar Colors):**
                    *   **🔴 Red (Past Due)**: Planned End Date < Today AND Status ≠ Done
                    *   **🟡 Yellow (At Risk)**: End Date within 7 days AND Progress < 70%, OR Started but Progress = 0%
                    *   **🟢 Green (On Track)**: Healthy progress
                    *   **⚪ Gray (Not Started)**: Start Date > 7 days from today
                    """)

                c_gantt, c_side = st.columns([3, 1])
                
                with c_gantt:
                    g_df = plan_df.copy()
                    
                    # Data prep
                    g_df['Plot_Start'] = g_df['Start Date'].fillna(g_df['Estimated Start Date'])
                    mask_no_end = g_df['Planned End Date'].isna() & g_df['Plot_Start'].notna()
                    if mask_no_end.any():
                        g_df.loc[mask_no_end, 'Planned End Date'] = g_df.loc[mask_no_end, 'Plot_Start'] + pd.Timedelta(days=30)
                    
                    g_df['Plot_Start'] = g_df['Plot_Start'].fillna(g_df['Planned End Date'] - pd.Timedelta(days=14))
                    g_df = g_df.dropna(subset=['Plot_Start', 'Planned End Date'])
                    
                    if not g_df.empty:
                        g_df['Business Purpose'] = g_df['Business Purpose'].fillna('N/A')
                        
                        now = pd.Timestamp.now().normalize()
                        
                        # Health Status Logic
                        def get_health_status(row):
                            end_d = row['Planned End Date']
                            start_d = row['Plot_Start']
                            status = row['Status']
                            progress = row['Progress']
                            
                            if pd.isna(end_d):
                                return 'Unknown'
                            
                            # Past Due
                            if end_d < now and status != 'Done':
                                return 'Past Due'
                            
                            # At Risk
                            days_to_deadline = (end_d - now).days
                            if days_to_deadline <= 7 and days_to_deadline >= 0 and progress < 70:
                                return 'At Risk'
                            
                            # Started but no progress
                            if not pd.isna(start_d) and start_d <= now and progress == 0:
                                return 'At Risk'
                            
                            # Not Started (future)
                            if not pd.isna(start_d) and (start_d - now).days > 7:
                                return 'Not Started'
                            
                            # On Track
                            return 'On Track'

                        g_df['Health_Status'] = g_df.apply(get_health_status, axis=1)
                        
                        # Create Y-axis label with format: Epic Name (Priority, XX%) - Bold the parentheses content
                        # Highlight "Critical" priority in red
                        def format_y_label(row):
                            priority = row['Priority']
                            progress = row['Progress']
                            epic_name = row['Epic Name']
                            
                            if priority == 'Critical':
                                return f"{epic_name} <b>(<span style='color:red;'>Critical</span>, {progress}%)</b>"
                            else:
                                return f"{epic_name} <b>({priority}, {progress}%)</b>"
                        
                        g_df['Y_Axis_Label'] = g_df.apply(format_y_label, axis=1)

                        import plotly.graph_objects as go

                        # Health Status Color Map
                        color_map = {
                            'Past Due': '#d32f2f',      # Red
                            'At Risk': '#ff9800',        # Orange/Yellow
                            'On Track': '#4caf50',       # Green
                            'Not Started': '#9e9e9e',    # Gray
                            'Unknown': '#757575'         # Dark Gray
                        }

                        fig_gantt = px.timeline(
                            g_df, 
                            x_start="Plot_Start", 
                            x_end="Planned End Date", 
                            y="Y_Axis_Label",
                            color="Health_Status",
                            color_discrete_map=color_map,
                            text="Epic Key",
                            hover_data=["Epic Key", "Epic Name", "Priority", "Progress", "Status", "Start Date", "Estimated Start Date", "Planned End Date", "Business Purpose", "Health_Status"],
                            title="Strategic Roadmap with Health Status"
                        )
                        
                        # Add TODAY vertical line
                        fig_gantt.add_vline(
                            x=now.timestamp() * 1000,  # Plotly uses milliseconds
                            line_dash="dash",
                            line_color="red",
                            line_width=2,
                            annotation_text="<b>TODAY</b>",
                            annotation_position="bottom"
                        )
                        
                        # Add Milestone Flags
                        if 'Milestone Date' in g_df.columns:
                            flags_df = g_df.dropna(subset=['Milestone Date']).copy()
                            if not flags_df.empty:
                                fig_gantt.add_trace(
                                    go.Scatter(
                                        x=flags_df['Milestone Date'],
                                        y=flags_df['Epic Name'],
                                        mode='markers',
                                        marker=dict(symbol='flag', size=14, color='red'),
                                        name='Milestone',
                                        hovertemplate="<b>Milestone:</b> %{x|%Y-%m-%d}<extra></extra>"
                                    )
                                )

                        # Layout
                        fig_gantt.update_traces(
                            textposition='inside',
                            textfont=dict(size=10),
                            marker_line_color='rgb(255, 255, 255)', 
                            marker_line_width=1, 
                            opacity=0.9,
                            selector=dict(type='bar')
                        )
                        
                        fig_gantt.update_yaxes(
                            categoryorder="total ascending", 
                            autorange="reversed",
                            showgrid=True,
                            gridcolor='#E5E5E5',
                            gridwidth=1,
                            tickson="boundaries"
                        ) 
                        
                        fig_gantt.update_xaxes(
                            range=["2025-12-01", "2026-12-31"], 
                            dtick="M1", 
                            tickformat="%b",
                            side="top", 
                            showgrid=True,
                            gridcolor='#E5E5E5',
                            gridwidth=1,
                        )
                        
                        chart_height = max(400, len(g_df) * 40)
                        
                        fig_gantt.update_layout(
                            height=chart_height,
                            xaxis_title=None, 
                            yaxis_title=None,
                            showlegend=True,
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            ),
                            plot_bgcolor='white', 
                            margin=dict(t=80, b=20), 
                            font=dict(family="Arial", size=12)
                        )
                        st.plotly_chart(fig_gantt, use_container_width=True)
                    else:
                        st.info("Insufficient data for Gantt Chart.")

                st.markdown("---")

                # --- 3.5. MULTI-LEVEL FOCUS DASHBOARD ---
                st.markdown("### 📋 Focus Areas & Business Context")
                
                # Filter data for focus sections
                focus_df = g_df.copy() if not g_df.empty else plan_df.copy()
                
                if not focus_df.empty and 'Health_Status' in focus_df.columns:
                    # 🔥 URGENT ATTENTION Section
                    urgent_items = focus_df[focus_df['Health_Status'].isin(['Past Due', 'At Risk'])]
                    
                    if not urgent_items.empty:
                        st.markdown("#### 🔥 URGENT ATTENTION")
                        st.caption(f"{len(urgent_items)} items need immediate action")
                        
                        cols = st.columns(min(3, len(urgent_items)))
                        for idx, (_, row) in enumerate(urgent_items.iterrows()):
                            with cols[idx % 3]:
                                # Determine card color based on health
                                if row['Health_Status'] == 'Past Due':
                                    card_color = "#ffebee"  # Light red
                                    status_emoji = "🔴"
                                else:
                                    card_color = "#fff3e0"  # Light orange
                                    status_emoji = "🟡"
                                
                                # Calculate days to deadline
                                days_left = (row['Planned End Date'] - now).days if pd.notna(row['Planned End Date']) else 0
                                deadline_text = f"{days_left} days left" if days_left >= 0 else f"{abs(days_left)} days overdue"
                                
                                st.markdown(f"""
                                <div style="background-color: {card_color}; padding: 15px; border-radius: 8px; border-left: 4px solid {'#d32f2f' if row['Health_Status'] == 'Past Due' else '#ff9800'};">
                                    <strong>{status_emoji} {row['Epic Key']}</strong><br>
                                    <small>{row['Epic Name'][:50]}...</small><br>
                                    <strong>Priority:</strong> {row['Priority']}<br>
                                    <strong>Progress:</strong> {row['Progress']}%<br>
                                    <strong>Deadline:</strong> {deadline_text}<br>
                                    <strong>Purpose:</strong> <em>{row['Business Purpose'][:80]}...</em>
                                </div>
                                """, unsafe_allow_html=True)
                                st.write("")  # Spacer
                    else:
                        st.success("✅ No urgent items - all epics are on track!")
                    
                    st.markdown("---")
                    
                    # 🏃 CURRENT SPRINT Section
                    # Identify current sprint items (those with Quarter Plan = current or near dates)
                    # For now, we'll show "Active Now" items (Implementing or Validating status)
                    with st.expander("🏃 ACTIVE NOW (Current Work)", expanded=True):
                        active_items = focus_df[focus_df['Status'].isin(['Implementing', 'Validating'])]
                        
                        if not active_items.empty:
                            st.caption(f"{len(active_items)} items in active development")
                            
                            # Group by status
                            for status in ['Implementing', 'Validating']:
                                status_items = active_items[active_items['Status'] == status]
                                if not status_items.empty:
                                    st.markdown(f"**{status}** ({len(status_items)} items)")
                                    
                                    cols = st.columns(min(3, len(status_items)))
                                    for idx, (_, row) in enumerate(status_items.iterrows()):
                                        with cols[idx % 3]:
                                            # Health-based card color
                                            if row['Health_Status'] == 'On Track':
                                                card_color = "#e8f5e9"  # Light green
                                                status_emoji = "🟢"
                                            elif row['Health_Status'] == 'At Risk':
                                                card_color = "#fff3e0"  # Light orange
                                                status_emoji = "🟡"
                                            else:
                                                card_color = "#f5f5f5"  # Gray
                                                status_emoji = "⚪"
                                            
                                            st.markdown(f"""
                                            <div style="background-color: {card_color}; padding: 12px; border-radius: 6px; margin-bottom: 10px;">
                                                <strong>{status_emoji} {row['Epic Key']}</strong><br>
                                                <small>{row['Epic Name'][:45]}...</small><br>
                                                <strong>Priority:</strong> {row['Priority']} | <strong>Progress:</strong> {row['Progress']}%<br>
                                                <em style="font-size: 0.85em;">{row['Business Purpose'][:70]}...</em>
                                            </div>
                                            """, unsafe_allow_html=True)
                        else:
                            st.info("No items currently in active development.")
                    
                    st.markdown("---")
                    
                    # 📅 THIS QUARTER - Summary
                    with st.expander("📅 THIS QUARTER - Overview", expanded=False):
                        st.caption("Strategic view of all planned items")
                        
                        # Group by priority for quarter view
                        priority_order = ['Critical', 'High', 'Medium', 'Low']
                        for priority in priority_order:
                            priority_items = focus_df[focus_df['Priority'] == priority]
                            if not priority_items.empty:
                                # Calculate summary stats
                                total = len(priority_items)
                                done = len(priority_items[priority_items['Status'] == 'Done'])
                                avg_progress = priority_items['Progress'].mean()
                                
                                st.markdown(f"**{priority} Priority** ({total} items, {done} completed, {avg_progress:.0f}% avg progress)")
                                
                                # Show condensed table
                                summary_cols = ['Epic Key', 'Epic Name', 'Status', 'Progress', 'Planned End Date']
                                display_df = priority_items[[c for c in summary_cols if c in priority_items.columns]].copy()
                                if 'Planned End Date' in display_df.columns:
                                    display_df['Planned End Date'] = display_df['Planned End Date'].dt.strftime('%Y-%m-%d')
                                
                                st.dataframe(display_df, hide_index=True, use_container_width=True, height=150)
                                st.write("")  # Spacer
                
                else:
                    st.info("No data available for focus areas.")

                st.markdown("---")

                # --- 4. QUICK EDIT PANEL ---
                st.markdown("### ⚡ Quick Edit Panel")
                st.caption("Select an epic to update key fields quickly. Current values are pre-populated for reference.")
                
                col_selector, col_rest = st.columns([2, 3])
                
                with col_selector:
                    epic_options = plan_df['Epic Key'].tolist()
                    selected_epic = st.selectbox("Select Epic", epic_options, key="quick_edit_epic_selector")
                
                if selected_epic:
                    epic_row = plan_df[plan_df['Epic Key'] == selected_epic].iloc[0]
                    
                    # Display current Epic Name for reference
                    st.info(f"**Epic:** {epic_row['Epic Name']}")
                    
                    # Create form layout with 2 rows
                    col1, col2, col3 = st.columns(3)
                    col4, col5, col6 = st.columns(3)
                    
                    with col1:
                        status_options = ['Funnel', 'Backlog', 'Definition', 'Implementing', 'Validating', 'Done']
                        current_status = epic_row['Status'] if epic_row['Status'] in status_options else 'Backlog'
                        new_status = st.selectbox("Status", status_options, index=status_options.index(current_status), key="quick_edit_status")
                    
                    with col2:
                        priority_options = ['Critical', 'High', 'Medium', 'Low']
                        current_priority = epic_row['Priority'] if epic_row['Priority'] in priority_options else 'Medium'
                        new_priority = st.selectbox("Priority", priority_options, index=priority_options.index(current_priority), key="quick_edit_priority")
                    
                    with col3:
                        current_sp = epic_row['Story Points'] if pd.notna(epic_row['Story Points']) else 0
                        new_story_points = st.number_input("Story Points", min_value=0.0, value=float(current_sp), step=1.0, key="quick_edit_sp")
                    
                    with col4:
                        current_start = epic_row['Start Date'] if pd.notna(epic_row['Start Date']) else None
                        new_start_date = st.date_input("Start Date", value=current_start, key="quick_edit_start")
                    
                    with col5:
                        current_est_start = epic_row['Estimated Start Date'] if pd.notna(epic_row['Estimated Start Date']) else None
                        new_est_start_date = st.date_input("Est. Start Date", value=current_est_start, key="quick_edit_est_start")
                    
                    with col6:
                        current_end = epic_row['Planned End Date'] if pd.notna(epic_row['Planned End Date']) else None
                        new_planned_end = st.date_input("Planned End Date", value=current_end, key="quick_edit_end")
                    
                    # Business Purpose in full width
                    current_purpose = epic_row['Business Purpose'] if pd.notna(epic_row['Business Purpose']) and epic_row['Business Purpose'] != 'nan' else ''
                    new_purpose = st.text_area("Business Purpose", value=current_purpose, height=80, key="quick_edit_purpose")
                    
                    # Assignee if exists
                    if 'Assignee' in plan_df.columns:
                        current_assignee = epic_row['Assignee'] if pd.notna(epic_row['Assignee']) and epic_row['Assignee'] != 'nan' else ''
                        new_assignee = st.text_input("Assignee", value=current_assignee, key="quick_edit_assignee")
                    else:
                        new_assignee = None
                    
                    col_btn1, col_btn2 = st.columns([1, 5])
                    with col_btn1:
                        if st.button("💾 Update", type="primary", key="quick_edit_update_btn", use_container_width=True):
                            # Update session state with all fields
                            plan_df.loc[plan_df['Epic Key'] == selected_epic, 'Status'] = new_status
                            plan_df.loc[plan_df['Epic Key'] == selected_epic, 'Priority'] = new_priority
                            plan_df.loc[plan_df['Epic Key'] == selected_epic, 'Story Points'] = new_story_points
                            plan_df.loc[plan_df['Epic Key'] == selected_epic, 'Start Date'] = pd.to_datetime(new_start_date)
                            plan_df.loc[plan_df['Epic Key'] == selected_epic, 'Estimated Start Date'] = pd.to_datetime(new_est_start_date)
                            plan_df.loc[plan_df['Epic Key'] == selected_epic, 'Planned End Date'] = pd.to_datetime(new_planned_end)
                            plan_df.loc[plan_df['Epic Key'] == selected_epic, 'Business Purpose'] = new_purpose
                            
                            if new_assignee is not None and 'Assignee' in plan_df.columns:
                                plan_df.loc[plan_df['Epic Key'] == selected_epic, 'Assignee'] = new_assignee
                            
                            st.session_state['plan_data'] = plan_df
                            
                            # Save to disk
                            plan_dir = "data/plans"
                            if not os.path.exists("data") and os.path.exists("../data"):
                                plan_dir = "../data/plans"
                            if not os.path.exists(plan_dir):
                                try:
                                    os.makedirs(plan_dir)
                                except:
                                    pass
                            
                            snap_date = st.session_state.get('plan_snapshot_date', str(datetime.date.today()))
                            save_path = os.path.join(plan_dir, f"plan_{snap_date}.csv")
                            
                            try:
                                plan_df.to_csv(save_path, index=False)
                                st.success(f"✅ Updated {selected_epic}! Chart will refresh.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to save: {e}")

                st.markdown("---")
                
                # --- 4.5. FULL EDITABLE TABLE ---
                st.markdown("### 📝 Complete Data Editor")
                st.caption("Edit all fields in the table below. Epic Key is frozen for reference. Scroll right to see all columns.")
                
                # Prepare editor dataframe
                # Add Delete Column
                if 'Delete' not in plan_df.columns:
                    plan_df['Delete'] = False
                
                # Define Display Order
                display_cols = ['Epic Name', 'Delete', 'Priority', 'Story Points', 'Status'] + sprint_cols + assignee_cols + ['Start Date', 'Estimated Start Date', 'Planned End Date', 'Milestone Date', 'Business Purpose']
                
                # Set Epic Key as Index for freezing
                plan_df_editor = plan_df.copy()
                if 'Epic Key' in plan_df_editor.columns:
                    try:
                        if not plan_df_editor['Epic Key'].duplicated().any():
                            plan_df_editor = plan_df_editor.set_index('Epic Key')
                        else:
                            st.warning("⚠️ Duplicate Epic Keys found. Freezing disabled.")
                            if 'Epic Key' not in display_cols:
                                display_cols = ['Epic Key'] + display_cols
                    except:
                        if 'Epic Key' not in display_cols:
                            display_cols = ['Epic Key'] + display_cols

                # Configure the editor
                editor_config = {
                    "Epic Key": st.column_config.TextColumn("Epic Key", width="medium", help="Unique ID (e.g., JIRA Key)", required=True),
                    "Epic Name": st.column_config.TextColumn("Epic Name", width=400, help="Description or Summary"),
                    "Delete": st.column_config.CheckboxColumn("🗑️", help="Select to remove this item", width="small", default=False),
                    "Story Points": st.column_config.NumberColumn("Story Points", width="small", help="Effort Estimate"),
                    "Status": st.column_config.TextColumn("Status", width="medium", help="Current Status"),
                    "Priority": st.column_config.SelectboxColumn(
                        "Priority", 
                        width="small", 
                        options=["Critical", "High", "Medium", "Low"],
                        required=True,
                        help="Strategic Priority Level"
                    ),
                    "Start Date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD"),
                    "Estimated Start Date": st.column_config.DateColumn("Est. Start Date", format="YYYY-MM-DD"),
                    "Planned End Date": st.column_config.DateColumn("Planned End Date", format="YYYY-MM-DD"),
                    "Milestone Date": st.column_config.DateColumn("🚩 Milestone", format="YYYY-MM-DD", help="Date for Red Flag indicator"),
                    "Business Purpose": st.column_config.TextColumn("Business Purpose", width="large", help="Strategic Value"),
                }
                
                # Dynamic sprint columns configuration
                qp_counter = 1
                for c in sprint_cols:
                    if "Quarter Plan" in c:
                        final_label = f"Quarter Plan {qp_counter}"
                        qp_counter += 1
                    else:
                        final_label = c.replace("Custom field (", "").replace(")", "").strip()
                    editor_config[c] = st.column_config.TextColumn(final_label, width="medium")

                if assignee_cols and assignee_cols[0] in plan_df.columns:
                    editor_config['Assignee'] = st.column_config.TextColumn("Assignee", width="medium", help="Owner")

                edited_df = st.data_editor(
                    plan_df_editor,
                    key="plan_editor_table_new",
                    num_rows="dynamic",
                    column_config=editor_config,
                    column_order=display_cols,
                    use_container_width=True,
                    height=400
                )
                
                # SAVE BUTTON
                col_save1, col_save2 = st.columns([1, 4])
                with col_save1:
                    if st.button("💾 Save All Changes", type="primary", key="save_table_new"):
                        # Reset index to get Epic Key back as column
                        final_df = edited_df.reset_index()
                        
                        # Process deletions
                        if 'Delete' in final_df.columns:
                            deleted_count = final_df['Delete'].sum()
                            if deleted_count > 0:
                                st.toast(f"🗑️ Deleting {deleted_count} items...")
                                final_df = final_df[~final_df['Delete']]
                            final_df = final_df.drop(columns=['Delete'])

                        st.session_state['plan_data'] = final_df
                        
                        # Save to disk
                        plan_dir = "data/plans"
                        if not os.path.exists("data") and os.path.exists("../data"):
                            plan_dir = "../data/plans"
                        if not os.path.exists(plan_dir):
                            try:
                                os.makedirs(plan_dir)
                            except:
                                pass
                        
                        snap_date = st.session_state.get('plan_snapshot_date', str(datetime.date.today()))
                        save_path = os.path.join(plan_dir, f"plan_{snap_date}.csv")
                        
                        try:
                            final_df.to_csv(save_path, index=False)
                            st.success(f"✅ Plan successfully saved to `{save_path}`!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to save plan: {e}")

                st.markdown("---")

                # --- 5. BACKLOG (TBD) SESSION ---
                st.markdown("### 📌 Backlog (TBD Items)")
                st.caption("Epics marked as 'TBD' in Quarter Plan columns.")

                if sprint_cols:
                    mask_tbd = pd.Series(False, index=plan_df.index)
                    
                    for c in sprint_cols:
                        if c in plan_df.columns:
                            condition = plan_df[c].astype(str).str.contains("TBD", case=False, na=False)
                            if condition.any():
                                mask_tbd = mask_tbd | condition
                    
                    if mask_tbd.any():
                        tbd_items = plan_df[mask_tbd]
                        
                        show_cols = ['Epic Key', 'Epic Name', 'Priority', 'Story Points', 'Status', 'Progress']
                        show_cols.extend([c for c in sprint_cols if c in plan_df.columns])
                        show_cols.append('Business Purpose')
                        
                        final_show_cols = [c for c in show_cols if c in tbd_items.columns]
                        
                        st.dataframe(tbd_items[final_show_cols], hide_index=True, use_container_width=True)
                    else:
                        st.success("✅ No items marked as 'TBD' in the Quarter Plan.")
                else:
                    st.info("No 'Quarter Plan' columns detected.")

             else:
                st.info("ℹ️ Please upload a 'Plan mgmt Excel' file in the sidebar to view enhanced plan data.")

    else:
        # Info box if no data
        st.warning(f"⚠️ No data available for {target_date_str}. Please upload a CSV file below.")
        
        # Main area uploader for better visibility
        st.markdown("### Upload Data")
        uploaded_main = st.file_uploader("Select JIRA Export (CSV)", type=['csv'], key="main_uploader")
        

        if st.button("Process File & Refresh View", key="process_main"):
            if uploaded_main is not None:
                try:
                    df = pd.read_csv(uploaded_main)
                    # Store data in session state
                    st.session_state['sprint_data'][target_date_str] = df
                    
                    # Update options list only on successful upload
                    if target_date_str not in st.session_state['sprint_options']:
                        st.session_state['sprint_options'].append(target_date_str)
                        st.session_state['sprint_options'].sort()
                    
                    # Update comparison logic: Set to immediate predecessor
                    current_opts = st.session_state['sprint_options']
                    try:
                        curr_idx = current_opts.index(target_date_str)
                        if curr_idx > 0:
                             st.session_state['compare_sprint_select'] = current_opts[curr_idx - 1]
                        elif len(current_opts) > 1:
                            pass
                    except ValueError:
                        pass
                        
                    st.success(f"Successfully loaded data for {target_date_str}")
                    st.rerun() # Refresh app to update lists
                except Exception as e:
                    st.error(f"Error processing file: {e}")
            else:
                 st.warning("Please select a file first.")

# Scan for persisted sprints in data/sprints
    sprint_dirs = ["data/sprints", "../data/sprints"]
    for d in sprint_dirs:
        if os.path.exists(d):
            for f in os.listdir(d):
                if f.startswith("sprint_") and f.endswith(".csv"):
                    try:
                        s_date = f.replace("sprint_", "").replace(".csv", "")
                        if s_date not in st.session_state['sprint_options']:
                             st.session_state['sprint_options'].append(s_date)
                    except: pass

if __name__ == "__main__":
    main()
