import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import json
import os

class JiraAnalyzer:
    def __init__(self, data_source, rules_path="data/rules.json", sprint_end_date=None):
        self.data_source = data_source
        self.df = None
        self.rules = self.load_rules(rules_path)
        self.sprint_end_date = sprint_end_date
        
        # Determine if data_source is path or dataframe
        if isinstance(data_source, pd.DataFrame):
            self.df = data_source
            # IMPORTANT: Ensure processing runs even when initialized with DF
            self.process_and_clean_data()
        else:
            self.load_data()

    def load_rules(self, rules_path):
        default_rules = {
            "critical_days_remaining": 1,
            "categorization_rules": {}
        }
        if os.path.exists(rules_path):
            try:
                with open(rules_path, 'r') as f:
                    loaded = json.load(f)
                    return {**default_rules, **loaded}
            except:
                pass
        return default_rules

    def process_and_clean_data(self):
        """
        Applies specific business rules for standardization.
        Rules:
        1. Base Units: Remaining Estimate is in column M (assumed Seconds or user provides), 
                  'Time Spent' is in column N (assumed Seconds),
                  'Custom field (Story Points)' is in Days.
        2. Status 'To Do': Remaining = Story Points, Time Spent = 0.
        3. Status 'Done': Remaining = 0, Time Spent = Story Points.
        4. Others (In Progress): If Remaining is empty, Remaining = Story Points - Time Spent.
        """
        if self.df is None:
            return

        # Ensure required columns exist (create if missing to avoid errors, fill 0)
        req_cols = ['Status', 'Custom field (Story Points)', 'Remaining Estimate', 'Time Spent']
        for col in req_cols:
            if col not in self.df.columns:
                self.df[col] = 0

        # --- GLOBAL FILTER: Remove Calvinthio ---
        if 'Assignee' in self.df.columns:
            # Drop rows where Assignee contains 'Calvinthio' (case-insensitive)
            self.df = self.df[~self.df['Assignee'].astype(str).str.contains('Calvinthio', case=False, na=False)]
            
            # --- GLOBAL FORMATTING: Use First Name Only ---
            # Take the first part of the string before the first space
            self.df['Assignee'] = self.df['Assignee'].astype(str).str.split().str[0]

        # Create Normalized 'Days' columns
        self.df['SP (Days)'] = pd.to_numeric(self.df['Custom field (Story Points)'], errors='coerce').fillna(0)
        self.df['Rem (Secs)'] = pd.to_numeric(self.df['Remaining Estimate'], errors='coerce') # Keep NaN to detect empty
        self.df['Spent (Secs)'] = pd.to_numeric(self.df['Time Spent'], errors='coerce').fillna(0)
        
        # Calculate Base Days from Seconds (1 Day = 8h = 28800s)
        self.df['Rem (Days)'] = self.df['Rem (Secs)'] / 28800
        self.df['Spent (Days)'] = self.df['Spent (Secs)'] / 28800

        # Apply Row-wise Logic
        def apply_rules(row):
            status = str(row.get('Status', '')).strip().lower()
            sp = row['SP (Days)']
            rem = row['Rem (Days)']
            spent = row['Spent (Days)']

            # Rule: To Do -> Rem = SP, Spent = 0
            if status == 'to do':
                return sp, 0.0

            # Rule: Done -> Rem = 0, Spent = SP
            if status in ['done', 'resolved', 'closed', 'cancelled']:
                return 0.0, sp

            # Rule: In Progress / Other
            # If Time Spent is present
            final_spent = spent
            
            # If Remaining is Empty (NaN), inferred Rem = SP - Spent
            # Note: Spent is in Days here.
            if pd.isna(rem):
                # If SP is 3, Spent is 1 -> Rem 2.
                final_rem = max(0, sp - final_spent)
            else:
                final_rem = rem
            
            return final_rem, final_spent

        # Apply and update main columns
        # We store the final calculated values back into new Cleaned Columns for graph usage
        # Or overwrite existing ones? Overwriting allows seamless downstream usage.
        # But 'Remaining Estimate' is usually Seconds in Jira. 
        # Let's overwrite 'Remaining Estimate' with SECONDS equivalent of our calculated Days
        # so other functions don't break.
        
        results = self.df.apply(apply_rules, axis=1, result_type='expand')
        self.df['Calculated Rem (Days)'] = results[0]
        self.df['Calculated Spent (Days)'] = results[1]
        
        # Update original columns for compatibility (converting back to seconds)
        self.df['Remaining Estimate'] = self.df['Calculated Rem (Days)'] * 28800
        self.df['Time Spent'] = self.df['Calculated Spent (Days)'] * 28800

    def load_data(self):
        """Loads Jira data from Excel or CSV."""
        if isinstance(self.data_source, pd.DataFrame):
            self.df = self.data_source
             # Run processing immediately on load
            self.process_and_clean_data()
            return

        try:
            if self.data_source.endswith('.csv'):
                self.df = pd.read_csv(self.data_source)
            else:
                self.df = pd.read_excel(self.data_source)
            
            # Run processing
            self.process_and_clean_data()

            print(f"Loaded and processed data from {self.data_source}")
        except Exception as e:
            print(f"Error loading data: {e}")

    def validate_categorization(self):
        """Checks if tickets are linked to the correct Parent Epic."""
        if self.df is None:
            return []

        mismatches = []
        rules = self.rules.get('categorization_rules', {})
        
        if 'Summary' in self.df.columns and 'Parent Epic' in self.df.columns:
            for index, row in self.df.iterrows():
                summary = str(row['Summary']).lower()
                epic = str(row['Parent Epic']).lower()
                
                for keyword, required_epic in rules.items():
                    if keyword.lower() in summary and required_epic.lower() not in epic:
                        mismatches.append({
                            'Ticket': row['Summary'],
                            'Current Epic': row['Parent Epic'],
                            'Suggested Epic': required_epic,
                            'Rule': f"Contains '{keyword}'"
                        })
                        break # Only report one mismatch per ticket
        return mismatches

    def validate_subtask_points(self):
        """
        Checks if Sub-task story points sum up to the Parent Story's points.
        Requires columns: 'Issue key', 'Issue Type', 'Parent', 'Custom field (Story Points)'
        """
        if self.df is None:
            return []

        issues = []
        required_cols = ['Issue key', 'Issue Type', 'Parent', 'Custom field (Story Points)']
        
        # Check if columns exist (case-insensitive matching could be added, but strict for now)
        missing_cols = [col for col in required_cols if col not in self.df.columns]
        if missing_cols:
            # Try to map common variations if exact match fails
            # For now, return empty and maybe log warning
            return [{"Error": f"Missing columns: {', '.join(missing_cols)}"}]

        # 1. Get all Stories and their points
        stories = self.df[self.df['Issue Type'] == 'Story'].set_index('Issue key')['Custom field (Story Points)'].to_dict()
        
        # 2. Get all Sub-tasks, group by Parent, and sum points
        subtasks = self.df[self.df['Issue Type'] == 'Sub-task'].copy()
        if subtasks.empty:
            return []

        # Ensure numeric
        subtasks['Custom field (Story Points)'] = pd.to_numeric(subtasks['Custom field (Story Points)'], errors='coerce').fillna(0)
        
        # Use 'Parent key' if available, otherwise fallback to 'Parent' (assuming it might be Key in some exports)
        group_col = 'Parent key' if 'Parent key' in subtasks.columns else 'Parent'
        
        grouped_subtasks = subtasks.groupby(group_col)['Custom field (Story Points)'].sum()

        # 3. Compare
        for parent_key, subtask_sum in grouped_subtasks.items():
            if parent_key in stories:
                parent_points = pd.to_numeric(stories[parent_key], errors='coerce') or 0
                if parent_points != subtask_sum:
                    issues.append({
                        'Parent Story': parent_key,
                        'Parent Points': parent_points,
                        'Sub-task Sum': subtask_sum,
                        'Status': 'Mismatch'
                    })
        
        return issues

    def check_critical_overdue(self):
        """
        Identifies Critical tickets with > 1 day remaining.
        Requires columns: 'Priority', 'Remaining Estimate' (seconds)
        """
        if self.df is None:
            return []

        critical_issues = []
        # Assuming 'Remaining Estimate' is in seconds. 1 day = 8 hours = 28800 seconds.
        ONE_DAY_SECONDS = 28800 

        if 'Priority' in self.df.columns and 'Remaining Estimate' in self.df.columns:
            # Filter Critical
            # Adjust 'Critical' string based on actual data (e.g., 'High', 'Highest')
            critical_df = self.df[self.df['Priority'].astype(str).str.contains('Critical', case=False, na=False)]
            
            for index, row in critical_df.iterrows():
                remaining = pd.to_numeric(row['Remaining Estimate'], errors='coerce') or 0
                if remaining > ONE_DAY_SECONDS:
                    critical_issues.append({
                        'Issue key': row.get('Issue key', 'N/A'),
                        'Summary': row.get('Summary', 'N/A'),
                        'Priority': row['Priority'],
                        'Remaining (Days)': round(remaining / ONE_DAY_SECONDS, 2)
                    })
        
        return critical_issues

    def check_done_status_remaining_estimate(self):
        """
        Rule: If Status is 'Done' (or similar), Remaining Estimate must be 0.
        """
        if self.df is None:
            return []
            
        required_cols = ['Issue key', 'Status', 'Remaining Estimate']
        if not all(col in self.df.columns for col in required_cols):
            return []
            
        mismatches = []
        # Filter for Done status (case insensitive)
        done_statuses = ['Done', 'Resolved', 'Closed', 'Cancelled']
        
        # Ensure Remaining Estimate is numeric
        # Note: load_data already handles some conversion, but good to be safe
        temp_df = self.df.copy()
        temp_df['Remaining Estimate'] = pd.to_numeric(temp_df['Remaining Estimate'], errors='coerce').fillna(0)
        
        for index, row in temp_df.iterrows():
            status = str(row['Status'])
            if status in done_statuses:
                if row['Remaining Estimate'] > 0:
                    mismatches.append({
                        'Issue key': row['Issue key'],
                        'Status': status,
                        'Remaining Estimate': row['Remaining Estimate'],
                        'Remaining (Days)': round(row['Remaining Estimate'] / 28800, 2),
                        'Error': 'Done ticket has remaining estimate'
                    })
        return mismatches

    def brainstorm_epics(self):
        """Brainstorms new epics based on historical data."""
        if self.df is None:
            return {}

        suggestions = {}
        if 'Summary' in self.df.columns:
            documents = self.df['Summary'].fillna('').tolist()
            
            if not documents:
                return {}

            # TF-IDF Vectorization
            vectorizer = TfidfVectorizer(stop_words='english')
            try:
                X = vectorizer.fit_transform(documents)
            except ValueError:
                return {} # Handle empty vocabulary

            # Clustering (K-Means)
            num_clusters = min(5, len(documents)) # Example number of potential epics
            if num_clusters < 1:
                return {}
                
            kmeans = KMeans(n_clusters=num_clusters, random_state=42)
            kmeans.fit(X)

            # Get top terms per cluster
            order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
            terms = vectorizer.get_feature_names_out()
            
            for i in range(num_clusters):
                top_terms = [terms[ind] for ind in order_centroids[i, :3]]
                suggestions[f"New Epic {i+1}"] = f"Consider epic around: {', '.join(top_terms)}"

        return suggestions

    def calculate_metrics(self):
        """Calculates high-level sprint metrics."""
        metrics = {
             'total_stories': 0,
             'total_points': 0,
             'completed_points': 0,
             'carry_over_points': 0
        }
        
        if self.df is None:
            return metrics
        
        # Determine "Done" statuses (Adjust as needed based on your Jira workflow)
        done_statuses = ['Done', 'Resolved', 'Closed']
        
        # 1. Total Stories (Count of items in sprint)
        # Exclude Epics usually as they span sprints. Exclude Sub-tasks from "Story count" often.
        if 'Issue Type' in self.df.columns:
             # Standard items: Not Epic, Not Sub-task
             # Handle case sensitivity if needed, but standard Jira is usually capitalized
             work_items = self.df[~self.df['Issue Type'].isin(['Epic', 'Sub-task'])]
             metrics['total_stories'] = len(work_items)
        else:
             metrics['total_stories'] = len(self.df)

        # 2. Points
        # Check for common Story Point column names
        sp_col = 'Custom field (Story Points)'
        if sp_col not in self.df.columns:
             # Try alternatives or check if user mapped it. For now, try finding a column with "Story Points"
             cols = [c for c in self.df.columns if 'Story Points' in c]
             if cols:
                 sp_col = cols[0]
        
        if sp_col in self.df.columns:
            # Ensure numeric
            current_sp = pd.to_numeric(self.df[sp_col], errors='coerce').fillna(0)
            
            # Use all items for points (including subtasks if they have points, though usually they don't add to velocity if parent has points)
            # Standard practice: Sum of points on Stories/Tasks/Bugs.
            # If we filter by work_items earlier:
            if 'Issue Type' in self.df.columns:
                # Filter rows that are main work items
                mask = ~self.df['Issue Type'].isin(['Epic', 'Sub-task'])
                metrics['total_points'] = current_sp[mask].sum()
                
                if 'Status' in self.df.columns:
                    # Check done status for these items
                    done_mask = self.df['Status'].isin(done_statuses)
                    metrics['completed_points'] = current_sp[mask & done_mask].sum()
            else:
                 metrics['total_points'] = current_sp.sum()
                 if 'Status' in self.df.columns:
                    metrics['completed_points'] = current_sp[self.df['Status'].isin(done_statuses)].sum()
            
            metrics['carry_over_points'] = metrics['total_points'] - metrics['completed_points']
            
            # Format for display (remove decimal if .0)
            metrics['total_points'] = int(metrics['total_points']) if metrics['total_points'].is_integer() else metrics['total_points']
            metrics['completed_points'] = int(metrics['completed_points']) if metrics['completed_points'].is_integer() else metrics['completed_points']
            metrics['carry_over_points'] = int(metrics['carry_over_points']) if metrics['carry_over_points'].is_integer() else metrics['carry_over_points']
        
        return metrics

    def check_ticket_alerts(self):
        """
        New Alert Logic:
        1. Remaining Estimate > Story Points --> Alert
        2. Time Spent > Story Points --> Alert
        Returns DataFrame with 'Assignee', 'Issue key', 'Summary', 'Alert Type', 'Values'
        """
        if self.df is None:
            return pd.DataFrame()
        
        alerts = []
        
        # Ensure we have necessary columns
        if 'Assignee' not in self.df.columns:
            return pd.DataFrame()

        # Iterate rows
        for index, row in self.df.iterrows():
            assignee = row.get('Assignee', 'Unassigned')
            key = row.get('Issue key', 'N/A')
            summary = row.get('Summary', '')
            
            # Get values in Days
            sp = row.get('SP (Days)', 0) # Already calculated in cleanup
            rem = row.get('Calculated Rem (Days)', 0)
            spent = row.get('Calculated Spent (Days)', 0)
            
            # Rule 1: Remaining Estimate > Story Points
            # Use small epsilon for float comparison
            if rem > (sp + 0.01):
                alerts.append({
                    'Assignee': assignee,
                    'Issue key': key,
                    'Summary': summary,
                    'Alert Type': 'Rem > SP',
                    'Details': f"Rem: {rem:.1f}d > SP: {sp:.1f}d"
                })

            # Rule 2: Time Spent > Story Points
            if spent > (sp + 0.01):
                alerts.append({
                    'Assignee': assignee,
                    'Issue key': key,
                    'Summary': summary,
                    'Alert Type': 'Spent > SP',
                    'Details': f"Spent: {spent:.1f}d > SP: {sp:.1f}d"
                })
                
        return pd.DataFrame(alerts)

    def get_at_risk_count(self):
        """
        Returns number of items at risk.
        Rule 1: Priority usually Critical or Blocker (removed High).
        Rule 2: Status Not Done AND (Time Spent + Remaining) > Story Points.
        """
        items = self.get_at_risk_items()
        return len(items)
    
    def get_at_risk_items(self):
        """
        Returns dataframe of at risk items with detailed reasons.
        Rule 1: Priority is Critical or Blocker AND Status not Done.
        Rule 2: Status Not Done AND (Time Spent + Remaining Estimate > Story Points).
        """
        if self.df is None:
            return pd.DataFrame()
        
        # Define Done Statuses
        done_statuses = ['done', 'resolved', 'closed', 'cancelled']
        
        risk_items = []
        
        for index, row in self.df.iterrows():
            status = str(row.get('Status', '')).strip().lower()
            if status in done_statuses:
                continue

            reasons = []

            # Check Rule 1: Priority
            priority = str(row.get('Priority', '')).lower()
            if 'critical' in priority or 'blocker' in priority:
                reasons.append("High Priority")

            # Check Rule 2: Exceeds Estimate
            # Logic: (Time Spent + Remaining) > Story Points
            sp = row.get('SP (Days)', 0)
            rem = row.get('Calculated Rem (Days)', 0)
            spent = row.get('Calculated Spent (Days)', 0)
            
            if (spent + rem) > (sp + 0.01):
                 reasons.append("Est. Exceeded")
            
            if reasons:
                # Format Risk Reason
                risk_str = ", ".join(reasons)
                if len(reasons) > 1:
                    risk_str = "Multiple"
                
                # Using dictionary to create clean DataFrame with Reason
                risk_record = {
                    'Issue key': row.get('Issue key'),
                    'Summary': row.get('Summary'),
                    'Assignee': row.get('Assignee'),
                    'Priority': row.get('Priority'),
                    'Status': row.get('Status'),
                    'Remaining (Days)': round(rem, 2),
                    'Risk Reason': risk_str
                }
                risk_items.append(risk_record)

        if not risk_items:
             return pd.DataFrame()

        df_risk = pd.DataFrame(risk_items)
        
        # Ensure consistent column order
        cols = ['Issue key', 'Summary', 'Assignee', 'Priority', 'Remaining (Days)', 'Status', 'Risk Reason']
        # Filter purely for available columns just in case
        cols = [c for c in cols if c in df_risk.columns]
            
        return df_risk[cols]

    def generate_workload_chart_data(self):
        """
        Generates data for workload breakdown chart.
        """
        if self.df is None:
            return None
            
        required_cols = ['Assignee', 'Remaining Estimate', 'Time Spent']
        # Check if cols exist
        existing_cols = [c for c in required_cols if c in self.df.columns]
        
        if 'Assignee' in existing_cols:
             df_chart = self.df.copy()
             
             # Calculate Days (assuming columns are in Seconds)
             if 'Remaining Estimate' in df_chart.columns:
                 df_chart['Remaining (Days)'] = pd.to_numeric(df_chart['Remaining Estimate'], errors='coerce').fillna(0) / 28800
             else:
                 df_chart['Remaining (Days)'] = 0
                 
             if 'Time Spent' in df_chart.columns:
                 df_chart['Spent (Days)'] = pd.to_numeric(df_chart['Time Spent'], errors='coerce').fillna(0) / 28800
             else:
                 df_chart['Spent (Days)'] = 0

             # Return cols needed for plotting
             # We do NOT filter by > 0 here because one row might have Spent > 0 but Rem = 0
             return df_chart[['Assignee', 'Issue key', 'Remaining (Days)', 'Spent (Days)', 'Priority']] 
        return None
    
    def append_to_history(self, snapshot_date, sprint_end_date, history_path="data/burndown_history.csv"):
        """
        Appends current dataset stats to history file.
        """
        if self.df is None:
            return

        # Calculate Totals
        # Note: process_and_clean_data has already normalized 'Remaining Estimate' to calculated seconds
        total_remaining = self.df['Remaining Estimate'].sum()
        
        # Remaining Tasks: Count of items not Done
        count_remaining = 0
        if 'Status' in self.df.columns:
            done_statuses = ['Done', 'Resolved', 'Closed', 'Cancelled']
            count_remaining = len(self.df[~self.df['Status'].isin(done_statuses)])
        
        # Adjust path for src/ run context
        if not os.path.exists(os.path.dirname(history_path)):
             # fallback to ../data if needed, but let's assume caller handles path or we check
             if os.path.exists("../data"):
                 history_path = "../" + history_path

        # Load or Create
        if os.path.exists(history_path):
            hist_df = pd.read_csv(history_path)
        else:
            hist_df = pd.DataFrame(columns=['Date', 'Sprint End Date', 'Remaining Estimate', 'Remaining Tasks'])

        # Ensure Date format
        snapshot_str = snapshot_date.strftime('%Y-%m-%d')
        sprint_end_str = sprint_end_date # String already

        # Check if entry exists for this Date + Sprint
        # If so, update it. If not, append.
        # Logic: User might re-upload corrected file for same date. We should overwrite.
        
        # Filter for match
        mask = (hist_df['Date'] == snapshot_str) & (hist_df['Sprint End Date'] == sprint_end_str)
        
        if hist_df[mask].empty:
            # Append
            new_row = pd.DataFrame([{
                'Date': snapshot_str,
                'Sprint End Date': sprint_end_str,
                'Remaining Estimate': total_remaining,
                'Remaining Tasks': count_remaining
            }])
            hist_df = pd.concat([hist_df, new_row], ignore_index=True)
        else:
            # Update
            hist_df.loc[mask, 'Remaining Estimate'] = total_remaining
            hist_df.loc[mask, 'Remaining Tasks'] = count_remaining
        
        hist_df.sort_values('Date', inplace=True)
        hist_df.to_csv(history_path, index=False)
