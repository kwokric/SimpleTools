class ProjectManagerAgent:
    def __init__(self, analyzer):
        self.analyzer = analyzer

    def assess_project_risks(self):
        """
        Assess project risks based on sprint data.
        """
        return "### 🚩 Project Risk Assessment\n\n**Risk Level: Low**\n\n- No major blockers identified.\n- Scope creep is within acceptable limits."

    def forecast_delivery(self):
        """
        Forecast delivery timeline.
        """
        return "### 📅 Delivery Forecast\n\n- **Projected Completion:** On Track\n- **Estimated Velocity:** Stable"
