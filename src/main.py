from sprint_manager import SprintManager
from jira_analyzer import JiraAnalyzer
import os

def main():
    print("Scrum Master Tool Started")
    
    # Example paths - user should replace these or we can make them arguments
    sprint_data_path = os.path.join('data', 'sprint_data.xlsx')
    jira_data_path = os.path.join('data', 'jira_history.xlsx')

    # 1. Sprint Management
    if os.path.exists(sprint_data_path):
        sm = SprintManager(sprint_data_path)
        sm.load_data()
        sm.analyze_progress()
        sm.generate_burndown_chart()
    else:
        print(f"Sprint data file not found at {sprint_data_path}")

    # 2. Jira Analysis
    if os.path.exists(jira_data_path):
        ja = JiraAnalyzer(jira_data_path)
        ja.load_data()
        ja.validate_categorization()
        ja.brainstorm_epics()
    else:
        print(f"Jira history file not found at {jira_data_path}")

if __name__ == "__main__":
    main()
