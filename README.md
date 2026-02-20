# Scrum Master Tool

## Overview
This tool helps Scrum Masters, Business Analysts, and teams manage sprints, track tasks, and organize Jira tickets using comprehensive data analysis and visualization. It provides actionable insights through Burndown charts, Resource utilization graphs, and automated Risk/Alert detection.

## Documentation
-   **[User Guide](USER_GUIDE.md)**: Comparison step-by-step instructions on setup, usage, and features. **Start Here!**
-   **[Requirements & Logic](REQUIREMENTS.md)**: Detailed breakdown of the business logic, formulas, and rules used by the system.

## Quick Start

1.  **Install Dependencies**:
    ```bash
    pip install -r install_requirements.txt
    ```

2.  **Run the Application**:
    ```bash
    streamlit run src/app.py
    ```

3.  **Upload Data**:
    -   Go to the dashboard in your browser.
    -   Upload your Jira CSV export in the sidebar.

## Key Features
-   **Interactive Dashboard**: Visualize sprint progress and team workload.
-   **Automated Alerts**: Detects estimates exceeding story points and critical blockers.
-   **Audit Logging**: Tracks daily alerts and user dismissals.
-   **AI Insights**: Integrated agents for qualitative analysis of requirements and sprint health.

See `USER_GUIDE.md` for full details.
