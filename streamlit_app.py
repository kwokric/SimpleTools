import streamlit as st
import pandas as pd
import sys
import os
import plotly.express as px

# Check if src is in path, if not add it
if 'src' not in sys.path:
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import local modules
# Rely on previous file's imports, assuming they work if src is in path
try:
    from jira_analyzer import JiraAnalyzer
    from agents import BusinessAnalystAgent, ScrumMasterAgent, ProjectManagerAgent
except ImportError:
    # Graceful fallback if path issues persist
    st.error("Error: Could not import project modules. Please ensure 'src' directory exists.")
    st.stop()

# Hardcoded valid sprints 
FIXED_SPRINTS = ["2025-12-30", "2026-01-13", "2026-01-23"]

def main():
    # 1. Critical: This must be the first Streamlit command
    st.set_page_config(page_title="JIRA Sprint Analyzer", layout="wide", page_icon="📊")
    
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
    
    # FORCE CLEANUP: Ensure 2026-02-02 is removed if present
    if "2026-02-02" in st.session_state['sprint_options']:
        st.session_state['sprint_options'].remove("2026-02-02")
    
    # Ensure valid fixed sprints are always present
    for s in FIXED_SPRINTS:
        if s not in st.session_state['sprint_options']:
            st.session_state['sprint_options'].append(s)
            
    st.session_state['sprint_options'].sort()

    # Initialize storage for dataframes
    if 'sprint_data' not in st.session_state:
        st.session_state['sprint_data'] = {}

    # --- Sidebar Controls ---
    st.sidebar.header("Configuration")

    # RESET BUTTON
    if st.sidebar.button("⚠️ Clear Cache & Restart"):
        st.session_state.clear()
        st.rerun()

    # Sprint Settings
    st.sidebar.subheader("Sprint Settings")
    use_past_sprint = st.sidebar.checkbox("Select from past sprints")
    
    if use_past_sprint:
        opts = st.session_state['sprint_options']
        default_idx = len(opts) - 1 if len(opts) > 0 else 0
        
        selected_past_sprint = st.sidebar.selectbox(
            "Choose Sprint", 
            opts,
            index=default_idx
        )
        default_date = pd.to_datetime(selected_past_sprint)
    else:
        # Default to 2026-01-23
        default_date = pd.to_datetime("2026-01-23")

    target_sprint_date = st.sidebar.date_input("Target Sprint End Date", value=default_date)
    target_date_str = target_sprint_date.strftime('%Y-%m-%d')

    st.sidebar.markdown("---")

    # Data Upload
    st.sidebar.subheader("Data Upload")
    uploaded_file = st.sidebar.file_uploader("Upload JIRA Export (CSV)", type=['csv'])
    


    # Manual Process Button
    if st.sidebar.button("Process File & Refresh View"):
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
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
                         # Fallback if it's the first item, maybe compare to next? or keep existing logic
                         pass 
                except ValueError:
                    pass
                    
                st.sidebar.success(f"Successfully loaded data for {target_date_str}")
                st.rerun() # Refresh app to update lists
            except Exception as e:
                st.sidebar.error(f"Error processing file: {e}")
        else:
             st.sidebar.warning("Please select a file first.")
    
    # Auto-load local data if available
    # Automatically loads data/Jan12.csv for sprint ending 2026-01-13
    if target_date_str == "2026-01-13" and target_date_str not in st.session_state['sprint_data']:
        local_path = "data/Jan12.csv"
        if os.path.exists(local_path):
            try:
                df_local = pd.read_csv(local_path)
                st.session_state['sprint_data'][target_date_str] = df_local
                # st.toast(f"Auto-loaded local data: {local_path}") # Optional toast
                st.rerun()
            except Exception as e:
                st.sidebar.warning(f"Failed to auto-load {local_path}: {e}")

    # --- Main Content ---
    
    # Retrieve data for current view
    current_df = st.session_state['sprint_data'].get(target_date_str)
    
    # Initialize Analyzer
    analyzer = None
    if current_df is not None:
        analyzer = JiraAnalyzer(current_df, sprint_end_date=target_date_str)

    if analyzer:
        # Use custom HTML success message or keep standard st.success
        st.success(f"Viewing Sprint Data: {target_date_str}")
        
        tab1, tab2, tab3 = st.tabs(["Dashboard", "AI Agents Insight", "Detail Data"])

        with tab1:
            st.markdown("### Sprint Overview")
            metrics = analyzer.calculate_metrics()
            
            # Using standard metrics but they will be styled by CSS
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Stories", metrics.get('total_stories', 0))
            m2.metric("Total Points", metrics.get('total_points', 0))
            m3.metric("Completed Points", metrics.get('completed_points', 0))
            m4.metric("Carry Over", metrics.get('carry_over_points', 0))

            st.markdown("---")

            st.markdown("### Chart Controls")
            
            # Chart Comparison - strictly from session state list
            opts = st.session_state['sprint_options']
            # Safely calculate index
            compare_index = 0
            if len(opts) >= 2:
                compare_index = len(opts) - 2
            
            compare_sprint = st.selectbox(
                "Compare with other Sprint (Chart only)", 
                options=opts,
                index=compare_index,
                key="compare_sprint_select"
            )
            
            # Simple Chart initialization
            if 'Status' in current_df.columns:
                fig = px.pie(current_df, names='Status', title=f'Status Distribution for {target_date_str}')
                st.plotly_chart(fig)

        with tab2:
            st.markdown("### AI Agent Analysis")
            agent_choice = st.radio("Choose Agent:", ["Business Analyst", "Scrum Master", "Project Manager"], horizontal=True)
            
            if st.button("Generate Agent Report"):
                with st.spinner("Analyzing..."):
                    if agent_choice == "Business Analyst":
                        agent = BusinessAnalystAgent(analyzer)
                        st.markdown(agent.analyze_requirements_quality())
                        st.markdown("---")
                        st.markdown(agent.generate_stakeholder_report())
                    elif agent_choice == "Scrum Master":
                        agent = ScrumMasterAgent(analyzer)
                        st.markdown(agent.check_sprint_health())
                        st.markdown("---")
                        st.markdown(agent.generate_retrospective_points())
                    elif agent_choice == "Project Manager":
                        agent = ProjectManagerAgent(analyzer)
                        st.markdown(agent.assess_project_risks())
                        st.markdown("---")
                        st.markdown(agent.forecast_delivery())

        with tab3:
            st.dataframe(current_df)
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

if __name__ == "__main__":
    main()
