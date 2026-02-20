# Scrum Master Tool

## Overview
This tool helps Scrum Masters, Business Analysts, and teams manage sprints, track tasks, and organize Jira tickets using comprehensive data analysis and visualization. It provides actionable insights through Burndown charts, Resource utilization graphs, and automated Risk/Alert detection.

## 📚 Documentation

### Quick Links
-   **[📖 Documentation Index](docs/README.md)** - Complete navigation guide
-   **[👤 User Guide](docs/USER_GUIDE.md)** - How to use the dashboard
-   **[👥 Team Member Guide](docs/team-handover/TEAM_MEMBER_GUIDE.md)** - For team handover
-   **[🚀 Deployment Guide](docs/deployment/QUICK_START_DEPLOYMENT.md)** - Deploy to cloud
-   **[📋 Requirements](docs/REQUIREMENTS.md)** - Business logic and specifications

**🌐 Live Dashboard:** https://jiramanagement.streamlit.app

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

See **[User Guide](docs/USER_GUIDE.md)** for full details.

## 📂 Project Structure

```
JIRA management/
├── src/                    # Source code
│   ├── app.py             # Main Streamlit application
│   ├── jira_analyzer.py   # Data analysis logic
│   ├── sprint_manager.py  # Sprint calculations
│   └── agents/            # AI analysis agents
├── data/                   # Data storage
│   ├── sprints/           # Sprint data (Git-tracked)
│   ├── plans/             # Plan data (Git-tracked)
│   └── cache/             # Temporary cache (not tracked)
├── docs/                   # 📚 All documentation
│   ├── README.md          # Documentation index
│   ├── team-handover/     # Team member guides
│   ├── deployment/        # Deployment guides
│   ├── technical/         # Technical documentation
│   └── archive/           # Historical docs
├── .github/                # GitHub configuration
├── push_data.sh           # Data sync script
└── requirements.txt       # Python dependencies
```

## 🔄 Workflow

### For Team Members (Upload Data)
1. Run locally: `streamlit run src/app.py`
2. Upload JIRA export via browser
3. Sync to cloud: `./push_data.sh`
4. View updates at: https://jiramanagement.streamlit.app

**Note:** File uploads only work locally for security. Cloud is read-only.

### For Developers
- See **[Technical Documentation](docs/technical/)** for architecture details
- See **[Deployment Guide](docs/deployment/)** for hosting setup
