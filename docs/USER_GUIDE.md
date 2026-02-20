# User Guide: JIRA Sprint Management & Analysis Tool

Welcome to the JIRA Sprint Management Tool! This guide is designed to help you get started, from installation to understanding the advanced analytics provided by the dashboard.

## 1. Introduction

This tool is designed for Scrum Masters, Business Analysts, and Project Managers to:
-   **Visualize Sprint Progress**: See burndown charts and completion metrics.
-   **Identify Risks**: Automatically spot "At Risk" items and "Workload Alerts" based on specific business rules.
-   **Analyze Workload**: View resource utilization by assignee.
-   **Audit & Log**: Keep track of daily alerts and dismissals.

## 2. Getting Started

### Prerequisites
-   **Python 3.8+** installed on your machine.
-   **VS Code** (Optional but recommended).

### Installation
1.  **Clone/Download** the repository to your local machine.
2.  **Open the folder** in VS Code or your terminal.
3.  **Set up the environment**:
    ```bash
    # Create a virtual environment (Mac/Linux)
    python3 -m venv .venv
    source .venv/bin/activate
    
    # Install dependencies
    pip install -r install_requirements.txt
    ```

## 3. Launching the Application

1.  Open your terminal in the project directory.
2.  Run the following command:
    ```bash
    streamlit run src/app.py
    ```
3.  A browser window will automatically open showing the dashboard (usually at `http://localhost:8501`).

## 4. Using the Dashboard

### A. Configuration (Sidebar)
The sidebar is your control center for *Default Settings* and *Admin* functions.
-   **Target Sprint End Date**: Sets the default scope for data processing.
-   **Admin Access**: Enter the password (`admin123`) to unlock advanced features.
-   **Data Upload**: Drag and drop your JIRA export (CSV format) here.

### B. Dashboard Tab (Main View)

#### 1. Sprint Selector & Overview
At the top of the dashboard, you will find:
-   **Switch Sprint View**: A dropdown that lets you instantly switch between different sprint periods to see historical data.
-   **Metrics**: Total Stories, Total Points, Completed Points, Carry Over.
-   **Status Distribution**: A pie chart showing the breakdown of ticket statuses for the selected sprint.

#### 2. Visualizations
-   **Sprint Burndown**: Shows the "Ideal" trajectory vs actual remaining estimates over time.
-   **Resource Utilization**:
    -   **Future Workload**: Bar chart of Remaining Estimate (Days) per assignee.

### B. Dashboard Tab (Main View)
This is the default view containing key metrics.

#### 1. Sprint Overview
-   **Total Stories**: Count of items in the sprint (excluding Epics/Subtasks).
-   **Total Points**: Sum of Story Points.
-   **Completed Points**: Points for items marked Done/Resolved/Closed.
-   **Carry Over**: Points remaining.

#### 2. Visualizations
-   **Sprint Burndown**: Shows the "Ideal" trajectory vs actual remaining estimates over time. Requires historical data points (uploaded daily).
-   **Resource Utilization**:
    -   **Future Workload**: Bar chart of Remaining Estimate (Days) per assignee.
    -   **Completed Work**: Bar chart of Time Spent (Days) per assignee.
    -   *Interactive*: Click on any bar to open the corresponding JIRA ticket in your browser.

#### 3. Alerts & Risks (Critical Section)
This section highlights immediate issues.

**⚠️ Workload Alerts**
*Potential underestimated tickets*
These alerts identify discrepancies between estimates and actuals.
-   **Rules**:
    1.  **Remaining > SP**: The Remaining Estimate exceeds the original Story Point estimate.
    2.  **Spent > SP**: The Time Spent already exceeds the original Story Point estimate.
-   **Actions**:
    -   **Dismiss**: You can dismiss an alert if it's a known issue. It will stay hidden for the current session.
    -   **Logging**: All alerts are logged daily to `logs/alerts_YYYY-MM-DD.log`.

**🔥 At Risk Items**
Items that require immediate management attention.
-   **Rules**:
    1.  **Critical/Blocker**: Any item with Priority "Critical" or "Blocker" that is **Not Done**.
    2.  **Estimate Blowout**: Any item (Not Done) where `(Time Spent + Remaining Estimate) > Story Points`.

### C. AI Agents Insight Tab
Use the "AI Agents" to get qualitative analysis.
-   **Business Analyst**: Checks requirement quality.
-   **Scrum Master**: Health check and retrospective points.
-   **Project Manager**: Risk assessment and forecasting.

### D. Detail Data Tab
View the raw data table for the current sprint.

## 5. File Management
(Located at the bottom of the Dashboard tab)
-   **Sprint Data Files**: View/Exclude uploaded sprint CSVs.
-   **Burndown History**: View/Edit historical data points used for the burndown chart.

## 6. Business Logic Rules Reference

| Category | Rule | Description |
| :--- | :--- | :--- |
| **Data Cleaning** | **To Do** | Rem = SP, Spent = 0 |
| | **Done** | Rem = 0, Spent = SP |
| | **Assignee** | Cleaned to first name only. "Calvinthio" excluded. |
| **Alerts** | **Rem > SP** | Remaining Estimate (Days) is greater than Story Points. |
| | **Spent > SP** | Time Spent (Days) is greater than Story Points. |
| **At Risk** | **Priority** | Priority is 'Critical' or 'Blocker' (and Status != 'Done'). |
| | **Blowout** | (Time Spent + Remaining) > Story Points (and Status != 'Done'). |

## 7. Troubleshooting
-   **Columns Missing?**: Ensure your CSV export has: `Status`, `Custom field (Story Points)`, `Remaining Estimate`, `Time Spent`, `Priority`, `Assignee`, `Issue key`.
-   **Burndown Flat?**: You need to upload data on different days. The history is built up over time by uploading daily snapshots.
