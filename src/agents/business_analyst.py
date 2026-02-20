from jira_analyzer import JiraAnalyzer
import pandas as pd

class BusinessAnalystAgent:
    """
    Business Analyst Agent

    A Business Analyst (BA) agent acts as a vital link, analyzing business needs and data to recommend 
    and implement solutions that improve processes, systems, and overall efficiency.

    Key Responsibilities:
    - Requirements Gathering: Conduct interviews, workshops, and surveys to understand business needs.
    - Data Analysis: Analyze large datasets, interpret findings, and suggest improvements.
    - Solution Design: Develop business cases and propose strategic solutions.
    - Liaison & Communication: Serve as a bridge between technical teams and business stakeholders.
    - Process Improvement: Identify bottlenecks and inefficiencies.
    - Reporting & Documentation: Create detailed reports and document requirements clearly.
    - Testing & Training: Support UAT and training.

    Operational Constraints:
    - This agent primarily focuses on REVIEW, ANALYSIS, and STRATEGY.
    - It should NOT write implementation code (Python, HTML, etc.) unless the user explicitly AGREES or REQUESTS it after a review.

    Core Skills:
    - Analytical and problem-solving abilities.
    - Communication and interpersonal skills.
    - Data analysis and modeling.
    """

    def __init__(self, jira_analyzer: JiraAnalyzer = None):
        self.jira_analyzer = jira_analyzer

    def analyze_requirements_quality(self):
        """
        Analyzes the quality of requirements (tickets) based on hygiene checks.
        Maps to 'Requirements Gathering' & 'Process Improvement'.
        """
        if not self.jira_analyzer:
            return "No Jira data available for analysis."

        report = "**Requirements Quality Report**\n\n"
        
        # Check Categorization
        mismatches = self.jira_analyzer.validate_categorization()
        if mismatches:
            report += f"❌ Found {len(mismatches)} tickets with potential categorization issues (Epic mismatch).\n"
            report += "Action: Review identified tickets with Product Owner to ensure correct grouping.\n"
        else:
            report += "✅ Ticket categorization appears aligned with keywords.\n"

        # Check subtask alignment
        point_issues = self.jira_analyzer.validate_subtask_points()
        if point_issues:
            report += f"❌ Found {len(point_issues)} stories where sub-task points do not match parent estimation.\n"
            report += "Action: Facilitate estimation session to align detailed requirements with high-level stories.\n"
        else:
             report += "✅ Story point decomposition looks consistent.\n"
             
        # Check Done definition
        done_errors = self.jira_analyzer.check_done_status_remaining_estimate()
        if done_errors:
            report += f"❌ Found {len(done_errors)} completed tickets with remaining work logged.\n"
            report += "Action: Ensure 'Definition of Done' is clear; tickets should not be closed until work is zeroed out.\n"
        else:
            report += "✅ Completed tickets adhere to hygiene rules.\n"

        return report

    def propose_strategic_groupings(self):
        """
        Uses data modeling features to suggest new Epics or groupings.
        Maps to 'Solution Design' & 'Data Analysis'.
        """
        if not self.jira_analyzer:
            return "No data for strategic analysis."
        
        suggestions = self.jira_analyzer.brainstorm_epics()
        if not suggestions:
            return "Insufficient data patterns to suggest new strategic themes."
        
        result = "**Strategic Theme Proposals (Based on Data Clustering)**\n\n"
        for cluster, terms in suggestions.items():
            result += f"**Theme {cluster}:** {', '.join(terms)}\n"
            result += "- *Recommendation:* Consider creating a new Initiative or Epic to track these related items together.\n\n"
            
        return result

    def generate_stakeholder_report(self):
        """
        Generates a summary for stakeholders.
        Maps to 'Reporting & Documentation'.
        """
        if not self.jira_analyzer or self.jira_analyzer.df is None:
             return "No data available."
             
        df = self.jira_analyzer.df
        total_tickets = len(df)
        
        # Simple breakdown
        if 'Status' in df.columns:
            status_dist = df['Status'].value_counts().to_dict()
            status_summary = ", ".join([f"{k}: {v}" for k,v in status_dist.items()])
        else:
            status_summary = "N/A"
            
        return f"""
        # Stakeholder Executive Summary
        
        **Total Scope Detected:** {total_tickets} Items
        
        **Status Distribution:**
        {status_summary}
        
        **Analyst Insight:**
        Based on the current backlog, we should focus on clarifying requirements for the 'To Do' items 
        and validating the acceptance criteria for 'In Progress' work.
        """
