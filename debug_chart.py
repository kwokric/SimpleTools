
import pandas as pd
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from jira_analyzer import JiraAnalyzer

file_path = "data/sprints/sprint_2026-01-23.csv"
print(f"Testing file: {file_path}")

analyzer = JiraAnalyzer(file_path)
analyzer.load_data()

print("\n--- Columns ---")
print(analyzer.df.columns.tolist())

print("\n--- Sample Data (Assignee, Remaining Estimate, Time Spent, Status) ---")
if 'Assignee' in analyzer.df.columns:
    print(analyzer.df[['Assignee', 'Remaining Estimate', 'Time Spent', 'Status']].head())
else:
    print("Assignee column missing!")

print("\n--- Generating Chart Data ---")
chart_data = analyzer.generate_workload_chart_data()

if chart_data is not None:
    print("\nChart Data Head:")
    print(chart_data.head())
    
    print("\nNon-zero Remaining:")
    print(chart_data[chart_data['Remaining (Days)'] > 0.01])
else:
    print("Chart data is None")
