import pandas as pd
import os
import datetime
from sprint_manager import SprintManager
from jira_analyzer import JiraAnalyzer

# --- Configuration ---
TEMP_DATA_FILE = "data/temp_test_sprint_data.csv"
TEMP_HISTORY_FILE = "data/temp_test_history.csv"

def create_test_csv(sprint_values):
    """Creates a temporary CSV file with the given Sprint column values."""
    df = pd.DataFrame({
        'Issue key': [f'TEST-{i}' for i in range(len(sprint_values))],
        'Sprint': sprint_values,
        'Remaining Estimate': [28800] * len(sprint_values), # 1 day
        'Custom field (Story Points)': [1] * len(sprint_values)
    })
    df.to_csv(TEMP_DATA_FILE, index=False)

def cleanup_temp_files():
    """Removes temporary files."""
    if os.path.exists(TEMP_DATA_FILE):
        os.remove(TEMP_DATA_FILE)
    if os.path.exists(TEMP_HISTORY_FILE):
        os.remove(TEMP_HISTORY_FILE)

def run_sprint_test(test_name, sprint_values, expected_date_str, description):
    print(f"\n--- {test_name} ---")
    print(f"Description: {description}")
    
    create_test_csv(sprint_values)
    
    # Initialize SprintManager with temp history file
    sm = SprintManager(TEMP_DATA_FILE, history_file=TEMP_HISTORY_FILE)
    sm.load_data()
    
    detected_date = sm.get_sprint_end_date_from_data()
    
    print(f"Input Sprints: {sprint_values}")
    print(f"Detected Date: {detected_date}")
    
    if expected_date_str:
        expected_date = datetime.datetime.strptime(expected_date_str, "%Y-%m-%d").date()
        if detected_date == expected_date:
            print("✅ PASS: Date matches expected.")
        else:
            print(f"❌ FAIL: Expected {expected_date}, got {detected_date}")
    else:
        print(f"ℹ️ Result: {detected_date}")

    return sm

# Setup
file_path = "data/Sample Input.csv"
if not os.path.exists(file_path):
    print(f"Error: {file_path} not found.")
    exit()

print("=== INITIALIZING TESTER AGENT ===")
print(f"Loading data from: {file_path}")

# Initialize Managers
sm = SprintManager(file_path)
sm.load_data()
ja = JiraAnalyzer(file_path)
ja.load_data()

# --- INJECTING TEST CASES ---
print("\n[TEST SETUP] Injecting synthetic data to validate detection logic...")

# 1. Inject High Workload for Rule 5
# Find an assignee and boost their remaining estimate
if sm.df is not None and not sm.df.empty:
    target_assignee = sm.df['Assignee'].iloc[0]
    print(f"-> Boosting workload for {target_assignee} to 12 days (should be RED)")
    # Add a dummy row
    new_row = sm.df.iloc[0].copy()
    new_row['Remaining Estimate'] = 12 * 28800 # 12 days in seconds
    new_row['Issue Type'] = 'Story' # Ensure it's not a sub-task so it gets counted
    sm.df = pd.concat([sm.df, pd.DataFrame([new_row])], ignore_index=True)

# 2. Inject Empty Remaining Estimate (Test Assumption)
# Add a row with Story Points=5 but Empty Remaining Estimate
print("-> Injecting row with Empty Remaining Estimate but Story Points=5 (Should be treated as 5 days)")
empty_rem_row = sm.df.iloc[0].copy()
empty_rem_row['Issue key'] = 'TEST-EMPTY-REM'
empty_rem_row['Remaining Estimate'] = None # Empty
empty_rem_row['Custom field (Story Points)'] = 5.0

# 3. Inject Done Ticket with Remaining Estimate (New Rule)
print("-> Injecting 'Done' ticket with 1 day remaining estimate (Should be flagged)")
done_row = ja.df.iloc[0].copy()
done_row['Issue key'] = 'TEST-DONE-ERROR'
done_row['Status'] = 'Done'
done_row['Remaining Estimate'] = 28800 # 1 day
ja.df = pd.concat([ja.df, pd.DataFrame([done_row])], ignore_index=True)

print("Injection complete.\n")
# ----------------------------

print("\n" + "="*50)
print("TEST 1: RULE 5 - ASSIGNEE WORKLOAD CHECK")
print("="*50)
print("Logic: Red if > 10 days (288,000s), Yellow if > 8 days (230,400s)")
workload = sm.check_assignee_workload()

if workload is not None and not workload.empty:
    print("\n[!] Workload Alerts Triggered:")
    print(workload.to_string(index=False))
    
    # Verification Logic
    print("\n--- Verification ---")
    for _, row in workload.iterrows():
        assignee = row['Assignee']
        days = row['Total Remaining (Days)']
        status = row['Status']
        color = row['Color']
        
        if days > 10 and color == 'Red':
            print(f"✅ PASS: {assignee} has {days} days -> Correctly flagged RED.")
        elif days > 8 and days <= 10 and color == 'Yellow':
            print(f"✅ PASS: {assignee} has {days} days -> Correctly flagged YELLOW.")
        else:
            print(f"❌ FAIL: {assignee} has {days} days but flagged {color}/{status}.")
else:
    print("No workload alerts triggered based on current data.")


print("\n" + "="*50)
print("TEST 2: CRITICAL TICKET CHECK")
print("="*50)
print("Logic: Priority='Critical' AND Remaining Estimate > 1 day (28,800s)")
critical_issues = ja.check_critical_overdue()

if critical_issues:
    print(f"\n[!] Found {len(critical_issues)} Critical Overdue Tickets:")
    df_crit = pd.DataFrame(critical_issues)
    print(df_crit[['Issue key', 'Priority', 'Remaining (Days)']].to_string(index=False))
    
    # Verification
    print("\n--- Verification ---")
    for item in critical_issues:
        key = item['Issue key']
        rem_days = item['Remaining (Days)']
        prio = item['Priority']
        
        if prio == 'Critical' and rem_days > 1.0:
             print(f"✅ PASS: {key} is Critical with {rem_days} days > 1.0.")
        else:
             print(f"❌ FAIL: {key} (Prio: {prio}, Days: {rem_days}) should not be flagged.")
else:
    print("No critical overdue tickets found.")

print("\n" + "="*50)
print("TEST 2.5: DONE STATUS CHECK")
print("="*50)
print("Logic: Status='Done' AND Remaining Estimate > 0")
done_errors = ja.check_done_status_remaining_estimate()

if done_errors:
    print(f"\n[!] Found {len(done_errors)} Done Tickets with Remaining Estimate:")
    df_done = pd.DataFrame(done_errors)
    print(df_done[['Issue key', 'Status', 'Remaining Estimate']].to_string(index=False))
    
    # Verification
    found_injected = False
    for item in done_errors:
        if item['Issue key'] == 'TEST-DONE-ERROR':
            found_injected = True
            print(f"✅ PASS: Detected injected error ticket {item['Issue key']}")
            
    if not found_injected:
        print("❌ FAIL: Did not detect injected error ticket.")
else:
    print("❌ FAIL: No errors found (Expected at least injected one).")


print("\n" + "="*50)
print("TEST 3: SUB-TASK POINT VALIDATION")
print("="*50)
print("Logic: Sum of Sub-task points must equal Parent Story points")
mismatches = ja.validate_subtask_points()

if mismatches:
    if isinstance(mismatches[0], dict) and 'Error' in mismatches[0]:
        print(f"Validation Message: {mismatches[0]['Error']}")
    else:
        print(f"\n[!] Found {len(mismatches)} Mismatches:")
        df_mis = pd.DataFrame(mismatches)
        print(df_mis.to_string(index=False))
else:
    print("✅ All sub-tasks align with parent stories.")

print("\n" + "="*50)
print("TEST 4: SPRINT CATEGORIZATION & TUESDAY LOGIC")
print("="*50)
try:
    # Test 1: Future Tuesday
    run_sprint_test(
        "Test 4.1: Future Tuesday",
        ["26 WRS.Sprint.2025.Dec.30"],
        "2025-12-30",
        "Should detect Dec 30, 2025 as it is a Tuesday."
    )

    # Test 2: Multiple Tuesdays
    run_sprint_test(
        "Test 4.2: Multiple Tuesdays",
        ["25 WRS.Sprint.2025.Dec.16", "26 WRS.Sprint.2025.Dec.30"],
        "2025-12-30",
        "Should pick Dec 30 (Future) over Dec 16 (Past)."
    )

    # Test 3: Past Tuesdays Only
    run_sprint_test(
        "Test 4.3: Past Tuesdays Only",
        ["24 WRS.Sprint.2025.Dec.2", "25 WRS.Sprint.2025.Dec.16"],
        "2025-12-16",
        "Should pick Dec 16 as the latest past Tuesday."
    )

    # Test 4: No Valid Tuesdays (Fallback)
    run_sprint_test(
        "Test 4.4: No Valid Tuesdays",
        ["25 WRS.Sprint.2025.Dec.24"], # Wednesday
        "2025-12-30", # Next Tuesday from Dec 23
        "Should fallback to next Tuesday (Dec 30) if no valid Tuesdays found."
    )
    
    # Test 5: History Update
    print("\n--- Test 4.5: History Update ---")
    # Re-run Test 1 setup to get a valid SM
    create_test_csv(["26 WRS.Sprint.2025.Dec.30"])
    sm_hist = SprintManager(TEMP_DATA_FILE, history_file=TEMP_HISTORY_FILE)
    sm_hist.load_data()
    
    # Ensure history file is clean
    if os.path.exists(TEMP_HISTORY_FILE):
        os.remove(TEMP_HISTORY_FILE)
        
    sm_hist.update_history()
    
    if os.path.exists(TEMP_HISTORY_FILE):
        hist_df = pd.read_csv(TEMP_HISTORY_FILE)
        latest_sprint_end = hist_df.iloc[-1]['Sprint End Date']
        if latest_sprint_end == "2025-12-30":
             print(f"✅ PASS: History updated with correct Sprint End Date: {latest_sprint_end}")
        else:
             print(f"❌ FAIL: History has {latest_sprint_end}, expected 2025-12-30")
    else:
        print("❌ FAIL: History file was not created.")

finally:
    print("\nCleaning up temp files...")
    cleanup_temp_files()

print("\n" + "="*50)
print("TEST 5: WORKLOAD CHART GENERATION")
print("="*50)
try:
    fig = sm.generate_workload_chart()
    if fig:
        print("✅ PASS: Workload chart generated successfully (Plotly Figure created).")
    else:
        print("⚠️ WARNING: Workload chart returned None (possibly no data with remaining estimate > 0).")
except Exception as e:
    print(f"❌ FAIL: Error generating workload chart: {e}")

print("\n" + "="*50)
print("TEST 6: SPRINT MANAGER DATA CLEANING (DONE STATUS)")
print("="*50)
# Create a temp CSV with a Done ticket that has remaining estimate
temp_done_csv = "data/temp_done_test.csv"
df_done_test = pd.DataFrame({
    'Issue key': ['TEST-DONE-1'],
    'Status': ['Done'],
    'Remaining Estimate': [28800], # 1 day
    'Custom field (Story Points)': [1],
    'Sprint': ['26 WRS.Sprint.2025.Dec.30']
})
df_done_test.to_csv(temp_done_csv, index=False)

sm_clean = SprintManager(temp_done_csv)
sm_clean.load_data()

rem_est = sm_clean.df.iloc[0]['Remaining Estimate']
if rem_est == 0:
    print(f"✅ PASS: Done ticket Remaining Estimate cleaned to {rem_est}.")
else:
    print(f"❌ FAIL: Done ticket Remaining Estimate is {rem_est}, expected 0.")

if os.path.exists(temp_done_csv):
    os.remove(temp_done_csv)

print("\n" + "="*50)
print("TEST 7: VARIABLE CAPACITY CHECK")
print("="*50)
# Inject a user with 6 days of work (48 hours)
# If they are normal capacity (10 days), they should be fine.
# If they are low capacity (5 days), they should be flagged RED.

# Create a temp CSV
temp_cap_csv = "data/temp_capacity_test.csv"
df_cap_test = pd.DataFrame({
    'Assignee': ['Junior Dev', 'Senior Dev'],
    'Remaining Estimate': [6 * 28800, 6 * 28800], # 6 days each
    'Issue Type': ['Story', 'Story'],
    'Sprint': ['Sprint 1', 'Sprint 1']
})
df_cap_test.to_csv(temp_cap_csv, index=False)

sm_cap = SprintManager(temp_cap_csv)
sm_cap.load_data()

# Check without low capacity list (Default)
workload_default = sm_cap.check_assignee_workload()
# Expect no flags because 6 < 10
if workload_default.empty:
    print("✅ PASS: Default check (10 SP limit) flagged no one for 6 days work.")
else:
    print(f"❌ FAIL: Default check flagged users: {workload_default['Assignee'].tolist()}")

# Check WITH low capacity list
workload_low = sm_cap.check_assignee_workload(low_capacity_assignees=['Junior Dev'])
# Expect Junior Dev to be flagged (6 > 5), Senior Dev not flagged (6 < 10)

flagged_users = workload_low['Assignee'].tolist() if not workload_low.empty else []

if 'Junior Dev' in flagged_users:
    print("✅ PASS: Junior Dev flagged when in low_capacity_assignees (6 > 5).")
else:
    print("❌ FAIL: Junior Dev NOT flagged despite being low capacity.")

if 'Senior Dev' not in flagged_users:
    print("✅ PASS: Senior Dev NOT flagged (Standard Capacity 10).")
else:
    print("❌ FAIL: Senior Dev flagged incorrectly.")

if os.path.exists(temp_cap_csv):
    os.remove(temp_cap_csv)

print("\n" + "="*50)
print("TEST 8: INTERACTIVE ASSIGNEE CHART")
print("="*50)
try:
    fig_interactive = sm.generate_interactive_assignee_progress_chart()
    if fig_interactive:
        print("✅ PASS: Interactive Assignee Progress chart generated successfully (Plotly Figure).")
        # Optional: Check if it has 2 traces (Spent and Remaining)
        if len(fig_interactive.data) == 2:
             print("✅ PASS: Chart has 2 traces (Spent and Remaining).")
        else:
             print(f"⚠️ WARNING: Chart has {len(fig_interactive.data)} traces, expected 2.")
    else:
        print("⚠️ WARNING: Interactive chart returned None (possibly missing columns).")
except Exception as e:
    print(f"❌ FAIL: Error generating interactive chart: {e}")

print("\n=== TEST COMPLETE ===")
