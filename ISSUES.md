# Issues Log

Use this file to track issues found during testing or usage.

## Resolved Issues

### Issues of Jan 18

- [x] **Unable to clear up uploaded data**
  - Problem: The user cannot delete specific incorrect data points (e.g., data from Jan 13/19 when sprint date is Jan 23).
  - Requirement: Add functionality to view and delete history entries from `burndown_history.csv`.
  - Resolution: Added "Manage Data History" expander in sidebar to select and delete history entries.

- [x] **Target Sprint End Date default selection**
  - Problem: Default selection logic is not smart enough relative to current date.
  - Requirement:
    - Default to the current active sprint (End Date >= Today) if available.
    - If Target Sprint End Date has passed, prompt user to save graph/PDF to Sharepoint location.
  - Resolution: Updated selection logic to default to >= Today. Added warning and "Save Graph" placeholder when date is passed.

- [x] **Switch Sprint Date in Graphs**
  - Problem: Usage on "Sprint Burndown" page requires better navigation for historical comparison.
  - Requirement: Add a dropdown in the "Sprint Burndown" main area to switch `Target Sprint End Date` locally for the charts.
  - Resolution: Added "Compare with other Sprint" dropdown in "Sprint Burndown" section.

- [x] **Validation rules display in Risk assessments**
  - Problem: Users cannot remember all rules.
  - Requirement:
    - Add a "?" tooltip or expander to view current rules.
    - Allow users to add/edit rules (saved to file).
  - Resolution: Added "Validation Rules" info box and "Settings & Rules" sidebar section to edit `rules.json`.

### Issues of Jan 19

- [x] **Convert Remaining Estimate to Man Days**
  - Problem: Remaining Estimate is currently displayed in seconds (Jira default), which is hard to read.
  - Requirement: Transform all display of Remaining Estimate to Man Days (1d = 8h).
  - Resolution: Updated `analyze_progress` and `check_done_status_remaining_estimate` to calculate and return `Remaining (Days)`. Updated UI tables and PDF generation to display this field instead of raw seconds.

### Issues of Jan 19 (Part 2)

- [x] **Workload Alert Dismissal**
    - Problem: Workload alerts persist even if acknowledged or deemed irrelevant for the moment.
    - Requirement: Add a "cross" (x) button to dismiss individual workload alerts.
    - Resolution: Added state management (`dismissed_alerts`) and a dismissal button (❌) next to each workload alert. Added a "Reset Dismissed Alerts" button to restore them.

- [x] **Sprint Date Detection & Chart Updates**
    - Problem: Uploaded data often fails to register under the correct "Target Sprint End Date" in the charts, especially for non-standard sprint lengths (e.g. 3 weeks) or Friday end dates (Jan 23). The charts do not update.
    - Requirement: 
        - Ensure uploaded data is tagged with the user-selected "Target Sprint End Date" from the sidebar, rather than relying solely on auto-detection from file content.
        - Fix "Chart Control" dropdown to include these correctly tagged dates.
    - Resolution: Modified `SprintManager.update_history` to accept a `manual_sprint_end_date`. Updated `app.py` to pipe the sidebar selection into this function, ensuring the history file (and thus the dropdowns) reflects the user's intent.

### Issues of Jan 19 (Part 3)

- [x] **Persist Selected Sprint**
    - Problem: The "Select Sprint (End Date)" dropdown resets or defaults incorrectly (e.g. to wrong date) after reloads or updates, causing frustration.
    - Requirement: Remember the last selected sprint date (e.g., 2026-01-23) and default to it in subsequent sessions or reloads, effectively providing "memory".
    - Resolution: Utilized `rules.json` to store a `last_selected_sprint` key. Updated the selectbox to check this saved value and default to it if available. Added an `on_change` callback to update the saved value immediately upon user selection.

- [x] **Default "Select from past sprints" to Unchecked**
    - Problem: User prefers to not have "Select from past sprints" checked by default.
    - Requirement: Change default value of the sidebar checkbox to `False`.
    - Resolution: Changed `st.sidebar.checkbox` default value to `False`.


