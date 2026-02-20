# Scrum Master Tool Requirements

## Overview
This tool assists the Scrum Master and the team in managing sprints, tracking tasks, and organizing Jira tickets. It leverages data from Excel exports to provide insights and automation.

## Features

### 1. Sprint Burndown Monitoring
- **Input**: Excel/CSV file containing task details.
- **Functionality**:
    - **Historical Tracking**: Automatically saves daily snapshots of `Total Remaining Estimate` and `Remaining Tasks` to `data/burndown_history.csv`.
    - **Dual-Axis Chart**:
        - **Left Axis**: Remaining Effort (Days) vs Ideal Burndown (Green Line).
        - **Right Axis**: Remaining Tasks (Blue Line) and Completed Tasks (Yellow Bars).
    - **Sprint Detection**: Automatically detects active sprint start/end dates from `Sprint` column (e.g., `Sprint.2025.Dec.16`).

### 2. Jira Ticket Organization & Validation
- **Input**: List of Jira tickets with titles and current Parent Epics.
- **Functionality**:
    - Analyze ticket titles to infer the correct category/Epic.
    - Flag tickets that appear to be linked to the wrong Parent Epic.
    - Suggest correct Epics based on keywords in the title.

### 4. Process Logic & Validation (Updated)
-   **Data Standardization**:
    -   **Base Calculation**: 
        -   `Story Points` (SP) assumed in Days.
        -   `Remaining Estimate` (Rem) & `Time Spent` (Spent) input in Seconds, converted to Days (1 Day = 8h = 28,800s).
    -   **State-Based Rules**:
        -   If Status is 'To Do': `Rem = SP`, `Spent = 0`.
        -   If Status is 'Done'/'Resolved'/'Closed'/'Cancelled': `Rem = 0`, `Spent = SP`.
    -   **Assignee Cleaning**:
        -   Names filtered to First Name only.
        -   Rows with Assignee "Calvinthio" are automatically excluded.

-   **Workload Alerts (Potential Underestimated Tickets)**:
    -   **Rule 1 (Rem > SP)**: Flag if `Remaining Estimate > Story Points`.
    -   **Rule 2 (Spent > SP)**: Flag if `Time Spent > Story Points`.
    -   **Logging**: Alerts are logged to `logs/alerts_YYYY-MM-DD.log`.
    -   **Persistence**: Users can dismiss alerts; these choices persist via `data/alert_dismissals.json`.

-   **At Risk Items (Immediate Attention)**:
    -   **Criterion 1 (Priority)**: Priority is 'Critical' or 'Blocker' AND Status is **NOT** 'Done'/'Resolved'/'Closed'/'Cancelled'.
    -   **Criterion 2 (Estimate Blowout)**: Status is **NOT** 'Done' etc. AND (`Time Spent` + `Remaining Estimate`) > `Story Points`.

-   **Data Assumptions**:
    -   If `Time Spent` is empty/null, assume **0**.
    -   If `Remaining Estimate` is empty/null, it is inferred from `SP - Spent` (floored at 0).

### 5. Reporting
- **PDF Export**:
    - Generate a landscape PDF report containing the analysis results and charts.
    - File naming: `report_YYYY-MM-DD.pdf`.
    - Save to `output/` folder.

## Technical Stack
- **Language**: Python
- **Libraries**:
    - `pandas`: Data manipulation and analysis.
    - `matplotlib` / `seaborn`: Visualization (Burndown charts).
    - `scikit-learn`: Text analysis (TF-IDF, Clustering) for ticket categorization and brainstorming.
    - `openpyxl`: Excel file reading/writing.
    - `streamlit`: Frontend UI.
    - `fpdf`: PDF generation.
1. Place Excel data files in the `data/` directory.
2. Run the scripts in `src/` to generate reports and insights.
