from sprint_manager import SprintManager
import datetime

class ScrumMasterAgent:
    """
    Scrum Master Agent
    
    A Scrum Master agent should focus on facilitating the Scrum framework, coaching agile teams as a servant leader, 
    removing impediments, and ensuring continuous improvement by running ceremonies and fostering collaboration.

    Key Responsibilities:
    - Facilitate Scrum Ceremonies: Lead daily stand-ups, sprint planning, sprint reviews, and retrospectives.
    - Remove Impediments: Identify and eliminate blockers that slow the team down.
    - Coach & Mentor: Guide the team and organization in understanding and applying Scrum/Agile principles.
    - Foster Collaboration: Promote open communication, self-organization, and cross-functional teamwork.
    - Shield the Team: Protect the team from external interruptions and distractions.
    - Support Product Owner: Help manage the product backlog and align team efforts.
    - Drive Improvement: Encourage a culture of continuous learning and process enhancement.

    Role & Mindset:
    - Servant Leader
    - Process Guardian
    - Coach/Mentor
    - Facilitator
    """

    def __init__(self, analyzer=None):
        self.analyzer = analyzer

    def check_sprint_health(self):
        """
        Checks the health of the sprint based on metrics and rules.
        """
        if not self.analyzer:
            return "No data available."
        
        health_report = "### 🩺 Sprint Health Check\n\n"
        
        # 1. Check Metrics
        metrics = self.analyzer.calculate_metrics()
        total = metrics.get('total_points', 0)
        completed = metrics.get('completed_points', 0)
        
        if total > 0:
            completion_rate = (completed / total) * 100
            health_report += f"- **Completion Rate:** {completion_rate:.1f}%\n"
            if completion_rate < 50:
                health_report += "  - ⚠️ **Risk:** Low completion rate. Consider descoping or swarming on remaining tickets.\n"
            elif completion_rate > 90:
                health_report += "  - ✅ **Status:** Excellent progress!\n"
        else:
            health_report += "- **Status:** No points estimated in this sprint.\n"

        # 2. Check Critical Issues
        criticals = self.analyzer.check_critical_overdue()
        if criticals:
            health_report += f"- ⚠️ **Critical Blockers:** Found {len(criticals)} critical tickets overdue/high risk.\n"
        else:
            health_report += "- ✅ **Blockers:** No critical overdue tickets found.\n"

        # 3. Check Hygiene
        hygiene = self.analyzer.check_done_status_remaining_estimate()
        if hygiene:
             health_report += f"- 🧹 **Hygiene:** {len(hygiene)} done tickets have remaining estimates not cleared.\n"

        return health_report

    def generate_retrospective_points(self):
        """
        Generates discussion points for the retrospective.
        """
        return """### 🔄 Retrospective Focus Areas

1. **Velocity Check:** Did we meet our forecast?
2. **Quality:** Discuss any returned tickets or bugs found in-sprint.
3. **Process:** Were the acceptance criteria clear for all stories?
4. **Team Health:** sustainable pace vs. crunch time?
"""
