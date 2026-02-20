import os
import json
import datetime
import pandas as pd

class AlertLogger:
    def __init__(self, log_dir="logs", data_dir="data"):
        self.log_dir = log_dir
        self.data_dir = data_dir
        self.dismissals_file = os.path.join(data_dir, "alert_dismissals.json")
        
        # Ensure directories exist
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)
        
        self.dismissed_alerts = self._load_dismissals()

    def _load_dismissals(self):
        """Load dismissed alerts from JSON file."""
        if os.path.exists(self.dismissals_file):
            try:
                with open(self.dismissals_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_dismissals(self):
        """Save dismissed alerts to JSON file."""
        with open(self.dismissals_file, 'w') as f:
            json.dump(self.dismissed_alerts, f, indent=4)

    def log_alerts_to_file(self, alerts_df):
        """
        Log current alerts to a daily log file.
        alerts_df: DataFrame with 'Issue key', 'Assignee', 'Alert Type', 'Details'
        """
        if alerts_df is None or alerts_df.empty:
            return

        today = datetime.date.today().strftime('%Y-%m-%d')
        log_file = os.path.join(self.log_dir, f"alerts_{today}.log")
        
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            with open(log_file, 'a') as f:
                f.write(f"\n--- Alert Scan: {timestamp} ---\n")
                for _, row in alerts_df.iterrows():
                    line = f"[{row.get('Issue key')}] {row.get('Assignee')} - {row.get('Alert Type')}: {row.get('Details')}\n"
                    f.write(line)
        except Exception as e:
            print(f"Error logging alerts: {e}")

    def dismiss_alert(self, issue_key, alert_type, user="user", remarks=""):
        """
        Mark an alert as dismissed with optional remarks.
        """
        key = f"{issue_key}|{alert_type}"
        self.dismissed_alerts[key] = {
            "issue_key": issue_key,
            "alert_type": alert_type,
            "dismissed_at": datetime.datetime.now().isoformat(),
            "dismissed_by": user,
            "remarks": remarks
        }
        self._save_dismissals()

    def is_dismissed(self, issue_key, alert_type):
        """Check if an alert is dismissed."""
        key = f"{issue_key}|{alert_type}"
        return key in self.dismissed_alerts

    def get_dismissal_info(self, issue_key, alert_type):
        """Get info about dismissal."""
        key = f"{issue_key}|{alert_type}"
        return self.dismissed_alerts.get(key)
    
    def get_all_dismissed_alerts(self):
        """Returns a list of all dismissed alerts."""
        return list(self.dismissed_alerts.values())
