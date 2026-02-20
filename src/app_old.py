import streamlit as st
import pandas as pd
import os
import datetime
import json
from fpdf import FPDF
from sprint_manager import SprintManager
from jira_analyzer import JiraAnalyzer
import matplotlib.pyplot as plt
from agents import BusinessAnalystAgent, ScrumMasterAgent

# Page Config
st.set_page_config(page_title="Scrum Master Tool", layout="wide")

# --- Rules Management ---
RULES_FILE = "data/rules.json"

def load_rules():
    defaults = {
        "risk_threshold_hours": 10,
        "workload_limit_days": 10,
        "critical_days_remaining": 1,
        "categorization_rules": {}
    }
    if os.path.exists(RULES_FILE):
        try:
            with open(RULES_FILE, 'r') as f:
                return {**defaults, **json.load(f)}
        except:
            pass
    return defaults

def save_rules(rules):
    with open(RULES_FILE, 'w') as f:
        json.dump(rules, f, indent=4)

RULES = load_rules()

# Custom CSS for McKinsey/IB Professional Look
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

    /* Status Indicators */
    .status-badge {
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    .status-good { background-color: #e8f5e9; color: #2e7d32; border: 1px solid #c8e6c9; }
    .status-warning { background-color: #fff3e0; color: #ef6c00; border: 1px solid #ffe0b2; }
    .status-danger { background-color: #ffebee; color: #c62828; border: 1px solid #ffcdd2; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e0e0e0;
    }
    
    /* Tables */
    div[data-testid="stTable"] {
        font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="main-header">
        <h1>Sprint Executive Dashboard</h1>
        <div class="sub-header">Strategic Insights & Performance Tracking</div>
    </div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("Navigation")
option = st.sidebar.radio("Choose Analysis", ["Sprint Burndown", "Ticket Analysis", "Recommendations", "AI Agents"])

# Sprint Settings
st.sidebar.markdown("### Sprint Settings")
# Default to 2 weeks from now, user can adjust
default_end = datetime.date.today() + datetime.timedelta(days=14)
# Try to load history to find available sprints
history_file = "data/burndown_history.csv"
available_sprints = []
if os.path.exists(history_file):
    try:
        hist_df = pd.read_csv(history_file)
        if 'Sprint End Date' in hist_df.columns:
            available_sprints = sorted(hist_df['Sprint End Date'].dropna().unique())
    except:
        pass

if available_sprints:
    use_existing_sprint = st.sidebar.checkbox("Select from past sprints", value=False)
else:
    use_existing_sprint = False

if use_existing_sprint and available_sprints:
    # Logic: Prioritize Saved User Selection > Closest Future > Latest
    
    # 1. Calculate base default (Closest Future or Latest)
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    default_idx = len(available_sprints) - 1 # Default to last
    
    for i, s_date in enumerate(available_sprints):
        if s_date >= today_str:
            default_idx = i
            break
            
    # 2. Check for saved selection
    saved_selection = RULES.get("last_selected_sprint")
    if saved_selection and saved_selection in available_sprints:
         default_idx = available_sprints.index(saved_selection)
         
    def on_sprint_change():
        RULES["last_selected_sprint"] = st.session_state.sprint_selector
        save_rules(RULES)

    sprint_end_date = st.sidebar.selectbox(
        "Select Sprint (End Date)", 
        available_sprints, 
        index=default_idx,
        key="sprint_selector",
        on_change=on_sprint_change
    )
    
    # Check if passed
    sprint_date_obj = datetime.datetime.strptime(sprint_end_date, '%Y-%m-%d').date()
    if sprint_date_obj < datetime.date.today():
        st.sidebar.warning("Target Sprint End Date has passed.")
        if st.sidebar.button("Save Graph to Output"):
            # Placeholder for saving
             st.sidebar.info("Please go to 'Sprint Burndown' tab and click 'Export Executive Report' to save properly.")
else:
    sprint_end_date = st.sidebar.date_input("Target Sprint End Date", default_end)

# File Uploaders
st.sidebar.markdown("### Data Upload")
sprint_file = st.sidebar.file_uploader("Upload Sprint Data (Excel/CSV)", type=['xlsx', 'csv'])
jira_file = st.sidebar.file_uploader("Upload Jira History (Excel/CSV)", type=['xlsx', 'csv'])

# Upload History Display
st.sidebar.markdown("### Upload History")
if os.path.exists("data/upload_history.csv"):
    try:
        hist_df = pd.read_csv("data/upload_history.csv")
        st.sidebar.dataframe(hist_df.sort_values('Upload Time', ascending=False).head(10), hide_index=True)
        if st.sidebar.button("Clear Upload Log"):
             if os.path.exists("data/upload_history.csv"):
                 os.remove("data/upload_history.csv")
                 st.experimental_rerun()
    except:
        st.sidebar.info("No history readable.")
else:
    st.sidebar.info("No upload history yet.")

with st.sidebar.expander("Manage Data History"):
    if os.path.exists(history_file):
        try:
            burndown_df = pd.read_csv(history_file)
            st.write("Burndown History:")
            
            # Allow deleting rows
            # Create a multiselect with "Date - Sprint End" labels
            burndown_df['Label'] = burndown_df['Date'].astype(str) + " (End: " + burndown_df['Sprint End Date'].astype(str) + ")"
            options = burndown_df['Label'].tolist()
            
            selected_to_delete = st.multiselect("Select entries to delete:", options)
            
            if st.button("Delete Selected History"):
                if selected_to_delete:
                    burndown_df = burndown_df[~burndown_df['Label'].isin(selected_to_delete)]
                    burndown_df.drop(columns=['Label'], inplace=True)
                    burndown_df.to_csv(history_file, index=False)
                    st.success("Deleted selected entries.")
                    st.experimental_rerun()
        except Exception as e:
            st.error(f"Error loading history: {e}")
    else:
        st.info("No burndown data history found.")

with st.sidebar.expander("Settings & Rules"):
    st.markdown("#### Risk Thresholds")
    new_risk_hours = st.number_input("High Risk Threshold (Hours)", value=RULES.get("risk_threshold_hours", 10))
    new_workload_limit = st.number_input("Workload Limit (Days)", value=RULES.get("workload_limit_days", 10))
    
    st.markdown("#### Categorization Rules")
    st.info("Add keyword:epic pairs (e.g. 'auth':'Security')")
    
    current_rules = RULES.get("categorization_rules", {})
    rules_text = json.dumps(current_rules, indent=2)
    new_rules_text = st.text_area("Edit Rules JSON", value=rules_text, height=150)
    
    if st.button("Save Settings"):
        try:
            parsed_rules = json.loads(new_rules_text)
            RULES["risk_threshold_hours"] = new_risk_hours
            RULES["workload_limit_days"] = new_workload_limit
            RULES["categorization_rules"] = parsed_rules
            save_rules(RULES)
            st.success("Rules saved!")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Invalid JSON format: {e}")

# Helper to save uploaded file temporarily
UPLOAD_HISTORY_FILE = "data/upload_history.csv"

def log_upload_event(filename):
    """Logs the upload event to a CSV file. Replaces existing entry if filename exists."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = pd.DataFrame([[timestamp, filename]], columns=['Upload Time', 'File Name'])
    
    if os.path.exists(UPLOAD_HISTORY_FILE):
        try:
            history_df = pd.read_csv(UPLOAD_HISTORY_FILE)
            
            # Remove existing entries with the same filename (User Request: Replace data)
            if not history_df.empty and 'File Name' in history_df.columns:
                history_df = history_df[history_df['File Name'] != filename]
            
            history_df = pd.concat([history_df, new_entry], ignore_index=True)
        except:
            history_df = new_entry
    else:
        history_df = new_entry
        
    history_df.to_csv(UPLOAD_HISTORY_FILE, index=False)

def save_uploaded_file(uploaded_file):
    try:
        if not os.path.exists("data"):
            os.makedirs("data")
        with open(os.path.join("data", uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        # Log the upload
        if 'logged_files' not in st.session_state:
            st.session_state.logged_files = set()
            
        if uploaded_file.name not in st.session_state.logged_files:
            log_upload_event(uploaded_file.name)
            st.session_state.logged_files.add(uploaded_file.name)
            
        return os.path.join("data", uploaded_file.name)
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return None

# Capacity Configuration (Sidebar)
low_capacity_assignees = []
# Determine source for capacity planning (Uploaded or Default)
capacity_source = sprint_file if sprint_file else ("data/Sample Input.csv" if os.path.exists("data/Sample Input.csv") else None)

if capacity_source:
    try:
        df_peek = None
        if isinstance(capacity_source, str): # File path
            if capacity_source.endswith('.csv'):
                df_peek = pd.read_csv(capacity_source)
            else:
                df_peek = pd.read_excel(capacity_source)
        else: # Uploaded file object
            capacity_source.seek(0)
            if capacity_source.name.endswith('.csv'):
                df_peek = pd.read_csv(capacity_source)
            else:
                df_peek = pd.read_excel(capacity_source)
            capacity_source.seek(0) # Reset buffer

        if df_peek is not None and 'Assignee' in df_peek.columns:
            all_assignees = sorted(df_peek['Assignee'].dropna().unique().tolist())
            st.sidebar.markdown("### Capacity Planning")
            st.sidebar.info("Select team members with 5 SP limit (Default is 10 SP)")
            low_capacity_assignees = st.sidebar.multiselect(
                "Less Story Points Allocated Members",
                options=all_assignees,
                default=[]
            )
    except Exception:
        pass

# PDF Generation Helper
def generate_pdf_report(sprint_manager=None, jira_analyzer=None, low_capacity_assignees=None):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Sprint Executive Report - {datetime.date.today()}", ln=True, align='C')
    pdf.ln(10)
    
    # Sprint Section
    if sprint_manager and sprint_manager.df is not None:
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Sprint Performance", ln=True)
        pdf.ln(5)
        
        # Save charts temporarily
        if not os.path.exists("output"):
            os.makedirs("output")
            
        # Burndown
        fig1 = sprint_manager.generate_burndown_chart()
        if fig1:
            fig1.savefig("output/temp_burndown.png", bbox_inches='tight')
            pdf.image("output/temp_burndown.png", x=10, y=40, w=130)
            
        # Assignee Progress
        fig2 = sprint_manager.generate_assignee_progress_chart()
        if fig2:
            fig2.savefig("output/temp_assignee.png", bbox_inches='tight')
            pdf.image("output/temp_assignee.png", x=150, y=40, w=130)
            
        pdf.ln(100) # Move down past images

        # Risk Items
        high_risk = sprint_manager.analyze_progress()
        if high_risk is not None and not high_risk.empty:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "High Risk Items (>10h Remaining)", ln=True)
            pdf.set_font("Arial", size=10)
            for index, row in high_risk.iterrows():
                # Prefer Remaining (Days) if available
                rem_str = f"{row['Remaining (Days)']} days" if 'Remaining (Days)' in row else f"{row['Remaining Estimate']}s"
                pdf.cell(0, 8, f"- {row['Task']}: {rem_str} remaining", ln=True)
            pdf.ln(5)

        # Assignee Workload (Rule 5)
        workload = sprint_manager.check_assignee_workload(low_capacity_assignees=low_capacity_assignees)
        if workload is not None and not workload.empty:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Assignee Workload Alerts", ln=True)
            pdf.set_font("Arial", size=10)
            for index, row in workload.iterrows():
                if row['Color'] == 'Red':
                    pdf.set_text_color(200, 0, 0)
                else:
                    pdf.set_text_color(200, 150, 0)
                pdf.cell(0, 8, f"- {row['Assignee']}: {row['Total Remaining (Days)']} days ({row['Status']})", ln=True)
            pdf.set_text_color(0, 0, 0) # Reset color
            pdf.ln(5)

    # Jira Section
    if jira_analyzer and jira_analyzer.df is not None:
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Jira Governance & Hygiene", ln=True)
        pdf.ln(5)
        
        # Critical Overdue
        critical = jira_analyzer.check_critical_overdue()
        if critical:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Critical Overdue Tickets (>1 Day Remaining)", ln=True)
            pdf.set_font("Arial", size=10)
            for item in critical:
                pdf.cell(0, 8, f"- {item['Issue key']} ({item['Priority']}): {item['Remaining (Days)']} days remaining", ln=True)
            pdf.ln(5)

        # Done Status Errors
        done_errors = jira_analyzer.check_done_status_remaining_estimate()
        if done_errors:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Done Status Validation Errors", ln=True)
            pdf.set_font("Arial", size=10)
            pdf.set_text_color(200, 0, 0)
            for item in done_errors:
                rem_str = f"{item.get('Remaining (Days)', item['Remaining Estimate'])} days"
                pdf.cell(0, 8, f"- {item['Issue key']}: Status '{item['Status']}' but {rem_str} remaining", ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(5)

        # Subtask Mismatches
        mismatches = jira_analyzer.validate_subtask_points()
        if mismatches:
            if isinstance(mismatches[0], dict) and 'Error' in mismatches[0]:
                 pdf.cell(0, 8, f"Validation Error: {mismatches[0]['Error']}", ln=True)
            else:
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "Sub-task Point Mismatches", ln=True)
                pdf.set_font("Arial", size=10)
                for item in mismatches:
                    pdf.cell(0, 8, f"- {item['Parent Story']}: Parent {item['Parent Points']} != Subtasks {item['Sub-task Sum']}", ln=True)

    # Save PDF
    filename = f"output/report_{datetime.date.today()}.pdf"
    if not os.path.exists("output"):
        os.makedirs("output")
    pdf.output(filename)
    return filename

# --- Sprint Burndown Section ---
if option == "Sprint Burndown":
    st.header("Sprint Burndown & Progress")
    
    # Determine Data Source (Upload or Default)
    path = None
    if sprint_file:
        path = save_uploaded_file(sprint_file)
    elif os.path.exists("data/Sample Input.csv"):
        path = "data/Sample Input.csv"
        st.info("Using default dataset: Sample Input.csv (Upload a file to override)")

    if path:
            sm = SprintManager(path)
            sm.load_data()
            
            # Update History for Burndown
            # Pass the manually selected date from sidebar to ensure consistency
            current_sprint_date = sprint_end_date
            if isinstance(current_sprint_date, str):
                   try:
                       current_sprint_date = datetime.datetime.strptime(current_sprint_date, '%Y-%m-%d').date()
                   except:
                       pass
                       
            sm.update_history(manual_sprint_end_date=current_sprint_date)
            
            # Refresh available sprints after update
            if os.path.exists(history_file):
                try:
                    hist_df = pd.read_csv(history_file)
                    if 'Sprint End Date' in hist_df.columns:
                         # Re-read to get newly added date
                        available_sprints = sorted(hist_df['Sprint End Date'].dropna().unique())
                except:
                    pass

    # --- View Mode (With or Without Upload) ---
    # Even if path is None, we want to show historical charts if available.
    
    # Initialize SM for history reading if not already created
    if not path:
        # Dummy path, won't load data but allows access to history methods
        sm = SprintManager("dummy") 
    
    # --- Graph Control (Issue 3) ---
    target_date_for_graph = sprint_end_date
    if available_sprints:
            st.markdown("### Chart Controls")
            col_sel, _ = st.columns([1, 3])
            with col_sel:
                # Default index finding
                graph_default_idx = 0
                if isinstance(sprint_end_date, str):
                    if sprint_end_date in available_sprints:
                            graph_default_idx = available_sprints.index(sprint_end_date)
                elif isinstance(sprint_end_date, datetime.date):
                        s_str = sprint_end_date.strftime('%Y-%m-%d')
                        if s_str in available_sprints:
                            graph_default_idx = available_sprints.index(s_str)

                target_date_for_graph = st.selectbox(
                   "Compare with other Sprint (Chart only)", 
                   available_sprints, 
                   index=graph_default_idx
                )

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Burndown Velocity")
        fig = sm.generate_burndown_chart(target_end_date=target_date_for_graph)
        if fig:
            st.pyplot(fig)
        else:
            if not path:
                st.info("No historical burndown data found for this sprint. Upload data to begin tracking.")
            else:
                st.warning("Not enough historical data to generate burndown chart. Please upload data daily to build history.")
        
        # New Workload Chart (Stacked Bar with Hover)
        if path:
            st.markdown("### Detailed Workload Breakdown")
            workload_fig = sm.generate_workload_chart()
            if workload_fig:
                st.plotly_chart(workload_fig, use_container_width=True)
            else:
                st.info("No remaining work data available for breakdown.")
        
        # Working Days Metric
        if target_date_for_graph:
            # Convert string to date if needed
            if isinstance(target_date_for_graph, str):
                target_date = datetime.datetime.strptime(target_date_for_graph, '%Y-%m-%d').date()
            else:
                    target_date = target_date_for_graph
                
            working_days = sm.calculate_working_days_left(target_date)
            st.info(f"📅 **{working_days} Working Days Remaining** in target sprint (including today)")

        if path:
            st.markdown("### Resource Utilization")
            fig2 = sm.generate_interactive_assignee_progress_chart()
            if fig2:
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Assignee chart requires 'Assignee', 'Remaining Estimate', 'Time Spent' columns.")

    with col2:
        if path:
            st.markdown("### Risk Assessment")
            with st.expander("ℹ️ Validation Rules"):
                st.markdown(f"- **High Risk**: > {RULES.get('risk_threshold_hours', 10)} hours remaining")
                st.markdown(f"- **Workload Limit**: > {RULES.get('workload_limit_days', 10)} days")
            
            # Rule 5: Workload
            workload = sm.check_assignee_workload(low_capacity_assignees=low_capacity_assignees)
            if workload is not None and not workload.empty:
                # Init dismissal state
                if 'dismissed_alerts' not in st.session_state:
                    st.session_state.dismissed_alerts = set()

                st.markdown("#### Workload Alerts")
                
                # Filter out dismissed
                visible_workload = []
                for index, row in workload.iterrows():
                    key = f"{row['Assignee']}_{row['Total Remaining (Days)']}"
                    if key not in st.session_state.dismissed_alerts:
                            visible_workload.append(row)
                
                if visible_workload:
                    # Display
                    for row in visible_workload:
                        c_msg, c_btn = st.columns([0.85, 0.15])
                        color_class = "status-danger" if row['Color'] == 'Red' else "status-warning"
                        
                        with c_msg:
                            st.markdown(f"""
                                <div class="status-badge {color_class}" style="margin-bottom: 5px; display: block;">
                                    {row['Assignee']}: {row['Total Remaining (Days)']} Days ({row['Status']})
                                </div>
                            """, unsafe_allow_html=True)
                        
                        with c_btn:
                            key = f"{row['Assignee']}_{row['Total Remaining (Days)']}"
                            if st.button("❌", key=f"btn_{key}", help="Dismiss Alert"):
                                st.session_state.dismissed_alerts.add(key)
                                st.experimental_rerun()
                    st.markdown("<br>", unsafe_allow_html=True)
                else:
                    st.success("All alerts dismissed or resolved.")
                
                if st.session_state.dismissed_alerts:
                    if st.button("Reset Dismissed Alerts"):
                        st.session_state.dismissed_alerts = set()
                        st.experimental_rerun()

            high_risk = sm.analyze_progress()
            if high_risk is not None and not high_risk.empty:
                st.markdown(f"""
                    <div class="kpi-card" style="border-left-color: #c62828;">
                        <div class="kpi-value" style="color: #c62828;">{len(high_risk)}</div>
                        <div class="kpi-label">At Risk Items</div>
                    </div>
                    <br>
                """, unsafe_allow_html=True)
                # Display Remaining (Days) if available
                cols = ['Task', 'Remaining (Days)'] if 'Remaining (Days)' in high_risk.columns else ['Task', 'Remaining Estimate']
                st.dataframe(high_risk[cols], hide_index=True)
            else:
                st.markdown("""
                    <div class="kpi-card">
                        <div class="kpi-value">0</div>
                        <div class="kpi-label">At Risk Items</div>
                    </div>
                """, unsafe_allow_html=True)
        else:
             st.info("Upload daily estimate report to see Risk Assessment and Workload details.")
    
    if path:
        # PDF Export Button
        if st.button("Export Executive Report (PDF)"):
            report_path = generate_pdf_report(sprint_manager=sm, low_capacity_assignees=low_capacity_assignees)
            st.success(f"Report generated: {report_path}")
            with open(report_path, "rb") as pdf_file:
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_file,
                    file_name=os.path.basename(report_path),
                    mime="application/pdf"
                )

# --- Ticket Analysis Section ---
elif option == "Ticket Analysis":
    st.header("Jira Governance & Hygiene")
    
    # Determine Data Source (Upload or Default)
    path = None
    if jira_file:
        path = save_uploaded_file(jira_file)
    elif os.path.exists("data/Sample Input.csv"):
        path = "data/Sample Input.csv"
        st.info("Using default dataset: Sample Input.csv (Upload a file to override)")

    if path:
            ja = JiraAnalyzer(path)
            ja.load_data()
            
            with st.expander("ℹ️ Validation Rules"):
                 st.markdown(f"- **Critical Overdue**: < {RULES.get('critical_days_remaining', 1)} days remaining")
                 st.markdown("- **Done Status**: Status 'Done' must have 0 remaining")
                 st.markdown("- **Categorization**: Checks keywords in Summary vs Epic")
                 st.json(RULES.get('categorization_rules', {}))

            # 1. Critical Overdue
            st.subheader("Critical Items Watchlist")
            critical_overdue = ja.check_critical_overdue()
            if critical_overdue:
                 st.markdown(f"""
                    <div class="status-badge status-danger">
                        {len(critical_overdue)} Critical Items Overdue
                    </div>
                    <br><br>
                """, unsafe_allow_html=True)
                 st.dataframe(pd.DataFrame(critical_overdue))
            else:
                st.success("No critical overdue items found.")

            # 2. Done Status Check (New Rule)
            st.subheader("Done Status Validation")
            done_errors = ja.check_done_status_remaining_estimate()
            if done_errors:
                st.error(f"Found {len(done_errors)} tickets with Status='Done' but Remaining Estimate > 0")
                st.dataframe(pd.DataFrame(done_errors))
            else:
                st.success("All 'Done' tickets have 0 remaining estimate.")

            st.markdown("---")

            # 3. Subtask Validation
            st.subheader("Story Point Integrity (Parent vs Sub-tasks)")
            point_mismatches = ja.validate_subtask_points()
            if point_mismatches:
                if isinstance(point_mismatches[0], dict) and 'Error' in point_mismatches[0]:
                    st.warning(point_mismatches[0]['Error'])
                else:
                    st.markdown(f"""
                        <div class="status-badge status-warning">
                            {len(point_mismatches)} Point Mismatches Detected
                        </div>
                        <br><br>
                    """, unsafe_allow_html=True)
                    st.table(pd.DataFrame(point_mismatches))
            else:
                 st.markdown('<div class="status-badge status-good">Story Points Aligned</div>', unsafe_allow_html=True)

            st.markdown("---")

            # 3. Categorization
            st.subheader("Categorization Audit")
            mismatches = ja.validate_categorization()
            
            if mismatches:
                st.markdown(f"""
                    <div class="status-badge status-warning">
                        {len(mismatches)} Potential Mismatches Identified
                    </div>
                    <br><br>
                """, unsafe_allow_html=True)
                st.table(pd.DataFrame(mismatches))
            else:
                st.markdown('<div class="status-badge status-good">All Tickets Compliant</div>', unsafe_allow_html=True)
            
            # PDF Export Button (Jira only)
            if st.button("Export Governance Report (PDF)"):
                report_path = generate_pdf_report(jira_analyzer=ja)
                st.success(f"Report generated: {report_path}")
                with open(report_path, "rb") as pdf_file:
                    st.download_button(
                        label="Download PDF Report",
                        data=pdf_file,
                        file_name=os.path.basename(report_path),
                        mime="application/pdf"
                    )

    else:
        st.info("Please upload 'Jira History' file (Excel/CSV) to see the analysis.")

# --- Recommendations Section ---
elif option == "Recommendations":
    st.header("Strategic Recommendations")
    
    # Placeholder for recommendation logic
    st.info("Recommendations feature coming soon based on rule engine.")

elif option == "AI Agents":
    st.header("AI Team Assistants")
    st.markdown("Consult with your specialized AI agents for insights and process management.")

    col1, col2 = st.columns(2)

    # Initialize Managers (attempt to load data if files are uploaded)
    sm_agent_instance = None
    ba_agent_instance = None
    
    # Load Sprint Manager if available
    if sprint_file:
         # Save temporary file to process
        temp_path = f"data/temp_sprint_{sprint_file.name}"
        with open(temp_path, "wb") as f:
            f.write(sprint_file.getbuffer())
        
        sm = SprintManager(temp_path)
        try:
            sm.load_data()
            sm_agent_instance = ScrumMasterAgent(sm)
        except Exception as e:
            st.error(f"Error initializing Scrum Master: {e}")
    
    # Load Jira Analyzer if available
    if jira_file:
        temp_path = f"data/temp_jira_{jira_file.name}"
        with open(temp_path, "wb") as f:
            f.write(jira_file.getbuffer())
            
        ja = JiraAnalyzer(temp_path)
        try:
            ja.load_data()
            ba_agent_instance = BusinessAnalystAgent(ja)
        except Exception as e:
            st.error(f"Error initializing Business Analyst: {e}")

    with col1:
        st.subheader("🕵️ Business Analyst Check")
        if ba_agent_instance:
            if st.button("Analyze Requirements Quality"):
                st.markdown(ba_agent_instance.analyze_requirements_quality())
            
            if st.button("Propose Strategic Groupings"):
                st.markdown(ba_agent_instance.propose_strategic_groupings())
                
            if st.button("Generate Stakeholder Report"):
                st.markdown(ba_agent_instance.generate_stakeholder_report())
        else:
            st.warning("Please upload 'Jira History' to consult the Business Analyst.")

    with col2:
        st.subheader("🛡️ Scrum Master Check")
        if sm_agent_instance:
            if st.button("Identify Blockers"):
                st.markdown(sm_agent_instance.identify_blockers())
                
            if st.button("Check Process Adherence"):
                st.markdown(sm_agent_instance.check_process_adherence())
                
            st.markdown("---")
            st.caption("Ceremony Templates")
            if st.button("Daily Stand-up Agenda"):
                st.markdown(sm_agent_instance.facilitate_standup())
                
            if st.button("Retrospective Template"):
                st.markdown(sm_agent_instance.facilitate_retrospective())
        else:
            st.warning("Please upload 'Sprint Data' to consult the Scrum Master.")
    
# Footer
st.markdown("---")
st.caption("Confidential | Internal Use Only | Generated by Copilot")