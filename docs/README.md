# Documentation Index

Welcome to the JIRA Sprint Management Dashboard documentation!

## 📂 Quick Navigation

### 🚀 Getting Started
- **[Main README](../README.md)** - Project overview and quick start
- **[User Guide](USER_GUIDE.md)** - How to use the dashboard
- **[Requirements](REQUIREMENTS.md)** - Project requirements and specifications

---

## 📁 Documentation Sections

### 1. 👥 Team Handover
Documentation for team members who need to manage the dashboard while you're away.

- **[Team Member Guide](team-handover/TEAM_MEMBER_GUIDE.md)** ⭐ - **START HERE** - Complete step-by-step guide
- **[Handover Email](team-handover/HANDOVER_EMAIL.md)** - Email template for team handover
- **[Quick Reference](team-handover/QUICK_REFERENCE.md)** - One-page cheat sheet
- **[Setup Script](team-handover/setup_for_team.sh)** - Automated first-time setup

**Use case:** Handing over dashboard maintenance to a colleague

---

### 2. 🚀 Deployment
Documentation about deploying and hosting the application.

- **[Deployment Plan](deployment/DEPLOYMENT_PLAN.md)** - Complete deployment strategy
- **[Quick Start Deployment](deployment/QUICK_START_DEPLOYMENT.md)** - Fast deployment guide
- **[Deployment Summary](deployment/DEPLOYMENT_SUMMARY.md)** - Overview of deployment process
- **[Hosting Comparison](deployment/HOSTING_COMPARISON.md)** - Comparison of hosting options

**Use case:** Setting up the app on Streamlit Cloud or other hosting platforms

---

### 3. 🔧 Technical Documentation
In-depth technical documentation about features and architecture.

- **[Auto-Save Guide](technical/AUTO_SAVE_GUIDE.md)** - Data persistence implementation
- **[Persistence Strategy](technical/PERSISTENCE_STRATEGY.md)** - Data storage architecture
- **[Localhost Upload Security](technical/LOCALHOST_UPLOAD_SECURITY.md)** - Upload restriction feature

**Use case:** Understanding how the system works or making modifications

---

### 4. 📦 Archive
Older documentation and features not currently in use.

- **[SharePoint Integration](archive/SHAREPOINT_INTEGRATION.md)** - Planned SharePoint feature (not implemented)
- **[Issues Log](archive/ISSUES.md)** - Historical issues and resolutions

**Use case:** Reference for future features or historical context

---

## 🎯 Common Tasks

### I want to...

#### Upload new JIRA data
→ **[Team Member Guide](team-handover/TEAM_MEMBER_GUIDE.md)** - Section "Step 4: Export and Upload Your Data"

#### Deploy to cloud for the first time
→ **[Quick Start Deployment](deployment/QUICK_START_DEPLOYMENT.md)**

#### Understand how data persistence works
→ **[Auto-Save Guide](technical/AUTO_SAVE_GUIDE.md)**

#### Give dashboard access to a team member
→ **[Handover Email](team-handover/HANDOVER_EMAIL.md)** - Copy and customize

#### Troubleshoot upload issues
→ **[Localhost Upload Security](technical/LOCALHOST_UPLOAD_SECURITY.md)** - Explains upload restrictions

#### See all available hosting options
→ **[Hosting Comparison](deployment/HOSTING_COMPARISON.md)**

---

## 📱 Quick Links

- **Live Dashboard:** https://jiramanagement.streamlit.app
- **GitHub Repository:** https://github.com/kwokric/SimpleTools
- **JIRA Filter:** https://manulife-gwam.atlassian.net/issues/?filter=37000

---

## 🔄 Update Workflow

```
1. Run locally:        streamlit run src/app.py
2. Upload data:        Via browser at http://localhost:8501
3. Push to GitHub:     ./push_data.sh
4. Auto-deploy:        Streamlit Cloud updates automatically
```

---

## 📝 Notes

- All documentation is written in Markdown
- Files are organized by purpose for easy navigation
- Archive folder contains historical/unused documentation
- Main README is in the project root

---

**Need help?** Start with the **[Team Member Guide](team-handover/TEAM_MEMBER_GUIDE.md)** for most common tasks!
