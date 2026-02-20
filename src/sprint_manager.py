import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import os
import datetime
import re
import json

class SprintManager:
    def __init__(self, data_path, history_file="data/burndown_history.csv", rules_path="data/rules.json"):
        self.data_path = data_path
        self.df = None
        self.history_file = history_file
        self.rules = self.load_rules(rules_path)

    def load_rules(self, rules_path):
        default_rules = {
            "risk_threshold_hours": 10,
            "workload_limit_days": 10
        }
        if os.path.exists(rules_path):
            try:
                with open(rules_path, 'r') as f:
                    loaded = json.load(f)
                    # Merge defaults to ensure keys exist
                    return {**default_rules, **loaded}
            except:
                pass
        return default_rules

    def load_data(self):
        """Loads sprint data from Excel or CSV."""
        try:
            if self.data_path.endswith('.csv'):
                self.df = pd.read_csv(self.data_path)
            else:
                self.df = pd.read_excel(self.data_path)
            
            # --- Data Cleaning / Assumptions ---
            # Assumption: If Time Spent is empty, assume 0
            if 'Time Spent' in self.df.columns:
                self.df['Time Spent'] = pd.to_numeric(self.df['Time Spent'], errors='coerce').fillna(0)
            
            # Assumption: If Remaining Estimate is empty, assume Remaining (Days) = Story Points
            # Convert Story Points (Days) to Seconds (1 Day = 8h = 28800s)
            if 'Remaining Estimate' in self.df.columns and 'Custom field (Story Points)' in self.df.columns:
                self.df['Remaining Estimate'] = pd.to_numeric(self.df['Remaining Estimate'], errors='coerce')
                self.df['Custom field (Story Points)'] = pd.to_numeric(self.df['Custom field (Story Points)'], errors='coerce').fillna(0)
                
                missing_rem = self.df['Remaining Estimate'].isna()
                # Fill missing with Story Points * 28800
                self.df.loc[missing_rem, 'Remaining Estimate'] = self.df.loc[missing_rem, 'Custom field (Story Points)'] * 28800
            
            # Assumption: If Status is Done/Resolved/Closed, Remaining Estimate must be 0
            if 'Status' in self.df.columns and 'Remaining Estimate' in self.df.columns:
                done_statuses = ['Done', 'Resolved', 'Closed', 'Cancelled']
                # Ensure we match regardless of case if needed, but standard Jira is usually Title Case
                mask_done = self.df['Status'].isin(done_statuses)
                self.df.loc[mask_done, 'Remaining Estimate'] = 0
                
            print(f"Loaded data from {self.data_path}")
        except Exception as e:
            print(f"Error loading data: {e}")

    def get_sprint_end_date_from_data(self):
        """
        Scans the 'Sprint' column to find the Sprint End Date.
        Logic:
        1. Extract all dates from 'Sprint' column values.
        2. Filter for dates that are Tuesdays.
        3. Find the closest date that is >= Today (Current Sprint End).
        4. If none, find the latest past date (Past Sprint End).
        """
        if self.df is None:
            return None

        today = datetime.date.today()
        sprint_cols = [col for col in self.df.columns if 'Sprint' in col]
        
        found_dates = set()
        pattern = re.compile(r"Sprint\.(\d{4})\.([A-Za-z]+)\.(\d+)")
        
        for col in sprint_cols:
            unique_values = pd.unique(self.df[col].astype(str))
            for val in unique_values:
                match = pattern.search(val)
                if match:
                    year, month_str, day = match.groups()
                    try:
                        month = datetime.datetime.strptime(month_str, "%b").month
                        d = datetime.date(int(year), month, int(day))
                        found_dates.add(d)
                    except:
                        pass

        if not found_dates:
            # Fallback: Next Tuesday from today
            days_ahead = 1 - today.weekday()
            if days_ahead <= 0: # Target day already happened this week
                days_ahead += 7
            return today + datetime.timedelta(days=days_ahead)

        sorted_dates = sorted(list(found_dates))
        
        # Filter for Tuesdays (weekday == 1)
        tuesdays = [d for d in sorted_dates if d.weekday() == 1]
        
        if not tuesdays:
            # Fallback: Next Tuesday from today if no Tuesdays found in data
            days_ahead = 1 - today.weekday()
            if days_ahead <= 0: # Target day already happened this week
                days_ahead += 7
            return today + datetime.timedelta(days=days_ahead)

        # Find closest future/today date
        future_dates = [d for d in tuesdays if d >= today]
        if future_dates:
            return future_dates[0]
        
        # Else return latest past date
        return tuesdays[-1]

    def update_history(self, manual_sprint_end_date=None):
        """
        Saves the current daily stats to a history CSV.
        Tracks: Date, Sprint End Date, Total Remaining Estimate, Total Remaining Tasks
        """
        if self.df is None:
            return

        today = datetime.date.today()
        
        # Use manual date if provided, otherwise auto-detect
        if manual_sprint_end_date:
            sprint_end_date = manual_sprint_end_date
            # Ensure it's a date object
            if isinstance(sprint_end_date, str):
                 try:
                     sprint_end_date = datetime.datetime.strptime(sprint_end_date, '%Y-%m-%d').date()
                 except:
                     pass # Keep as string or handle error? Standardize on YYYY-MM-DD string for CSV usually best.
            elif isinstance(sprint_end_date, datetime.datetime):
                sprint_end_date = sprint_end_date.date()
        else:
            sprint_end_date = self.get_sprint_end_date_from_data()
        
        # Calculate stats
        total_remaining = self.df['Remaining Estimate'].sum()
        
        if 'Status' in self.df.columns:
            done_statuses = ['Done', 'Resolved', 'Closed', 'Cancelled']
            remaining_tasks = self.df[~self.df['Status'].isin(done_statuses)].shape[0]
        else:
            remaining_tasks = self.df.shape[0]

        # Load or Create History
        if os.path.exists(self.history_file):
            history_df = pd.read_csv(self.history_file)
            history_df['Date'] = pd.to_datetime(history_df['Date']).dt.date
            # Ensure 'Sprint End Date' column exists
            if 'Sprint End Date' not in history_df.columns:
                history_df['Sprint End Date'] = None
        else:
            history_df = pd.DataFrame(columns=['Date', 'Sprint End Date', 'Remaining Estimate', 'Remaining Tasks'])

        # Update or Append
        # Check if today already exists for this sprint
        # We use Date AND Sprint End Date as key? Or just Date?
        # Assuming one upload per day per sprint.
        
        mask = (history_df['Date'] == today)
        if not history_df[mask].empty:
            # Update existing row
            history_df.loc[mask, 'Remaining Estimate'] = total_remaining
            history_df.loc[mask, 'Remaining Tasks'] = remaining_tasks
            history_df.loc[mask, 'Sprint End Date'] = sprint_end_date
        else:
            # Append
            new_row = pd.DataFrame([{
                'Date': today, 
                'Sprint End Date': sprint_end_date,
                'Remaining Estimate': total_remaining,
                'Remaining Tasks': remaining_tasks
            }])
            history_df = pd.concat([history_df, new_row], ignore_index=True)
        
        history_df.sort_values('Date', inplace=True)
        history_df.to_csv(self.history_file, index=False)
        print(f"History updated for {today} (Sprint End: {sprint_end_date})")

    def calculate_working_days_left(self, target_date):
        """Calculates working days (Mon-Fri) from today until target_date (inclusive)."""
        today = datetime.date.today()
        if target_date < today:
            return 0
        
        # Generate range of dates
        delta = (target_date - today).days
        dates = [today + datetime.timedelta(days=i) for i in range(delta + 1)]
        
        # Count weekdays (0=Mon, 4=Fri)
        working_days = sum(1 for d in dates if d.weekday() < 5)
        return working_days

    def generate_burndown_chart(self, target_end_date=None):
        """
        Generates a dual-axis burndown chart:
        - Left Axis: Remaining Effort (Line), Ideal Burndown (Line), Predicted Trend (Dashed)
        - Right Axis: Remaining Tasks (Line), Completed Tasks (Bar)
        """
        if not os.path.exists(self.history_file):
            return None

        history_df = pd.read_csv(self.history_file)
        history_df['Date'] = pd.to_datetime(history_df['Date'])
        
        if history_df.empty:
            return None

        # Determine Sprint End Date
        if target_end_date:
            end_date = pd.to_datetime(target_end_date)
        else:
            # Default to the latest Sprint End Date found in history
            if 'Sprint End Date' in history_df.columns:
                latest_end = history_df['Sprint End Date'].dropna().max()
                if latest_end:
                    end_date = pd.to_datetime(latest_end)
                else:
                    # Fallback if column empty
                    end_date = pd.to_datetime(datetime.date.today() + datetime.timedelta(days=14))
            else:
                 end_date = pd.to_datetime(datetime.date.today() + datetime.timedelta(days=14))

        # Determine Start Date (End Date - 13 days for 2 week sprint)
        start_date = end_date - datetime.timedelta(days=13)

        # Filter history for this sprint
        # We filter by 'Sprint End Date' column if available, otherwise fallback to date range
        if 'Sprint End Date' in history_df.columns:
            # Convert target to string YYYY-MM-DD for comparison if needed, or just use date object
            # history_df['Sprint End Date'] is likely string.
            target_end_str = end_date.strftime('%Y-%m-%d')
            mask = (history_df['Sprint End Date'] == target_end_str)
            sprint_data = history_df.loc[mask].copy()
            
            # If no data found with explicit tag (e.g. old data), try date range fallback
            if sprint_data.empty:
                 mask = (history_df['Date'] >= start_date) & (history_df['Date'] <= end_date)
                 sprint_data = history_df.loc[mask].copy()
        else:
            mask = (history_df['Date'] >= start_date) & (history_df['Date'] <= end_date)
            sprint_data = history_df.loc[mask].copy()
        
        # Calculate Completed Tasks (Daily)
        # Completed = Previous Remaining Tasks - Current Remaining Tasks (Simplified)
        sprint_data['Completed Tasks'] = -sprint_data['Remaining Tasks'].diff()
        sprint_data['Completed Tasks'] = sprint_data['Completed Tasks'].apply(lambda x: max(0, x)).fillna(0)

        # Plotting
        try:
            plt.style.use('seaborn-v0_8-whitegrid')
        except:
            pass

        # Reduced size by ~30% (Original: 12, 7)
        fig, ax1 = plt.subplots(figsize=(8.5, 5))

        # --- Axis 1: Effort (Days) ---
        # Convert Seconds to Days (1d = 8h = 28800s)
        sprint_data['Effort Days'] = sprint_data['Remaining Estimate'] / 28800
        
        # Ideal Line
        # Start: Max effort at start date (or first recorded date)
        # End: 0 at end date
        if not sprint_data.empty:
            max_effort = sprint_data['Effort Days'].max()
            # Ideal: From Start Date (Max Effort) to End Date (0)
            ax1.plot([start_date, end_date], [max_effort, 0], 
                    color='#388e3c', linestyle='-', linewidth=2, label='Ideal Burndown')
            
            # Actual Effort Line
            ax1.plot(sprint_data['Date'], sprint_data['Effort Days'], 
                    marker='D', color='#1565c0', linewidth=2, label='Remaining Effort (Days)')

            # --- Prediction Logic ---
            # If we have at least 2 data points, we can project
            if len(sprint_data) >= 2:
                # Calculate average daily burn rate (slope)
                # Simple approach: (Start Effort - Current Effort) / Days Elapsed
                current_effort = sprint_data['Effort Days'].iloc[-1]
                days_elapsed = (sprint_data['Date'].iloc[-1] - sprint_data['Date'].iloc[0]).days
                
                if days_elapsed > 0:
                    burn_rate = (sprint_data['Effort Days'].iloc[0] - current_effort) / days_elapsed
                    
                    if burn_rate > 0:
                        days_to_finish = current_effort / burn_rate
                        predicted_end = sprint_data['Date'].iloc[-1] + datetime.timedelta(days=days_to_finish)
                        
                        # Plot Prediction Line (Current -> Predicted End)
                        ax1.plot([sprint_data['Date'].iloc[-1], predicted_end], [current_effort, 0],
                                color='#d32f2f', linestyle='--', linewidth=2, label='Predicted Trend')
                    else:
                        # Negative or zero burn rate (scope creep or stuck)
                        pass

        ax1.set_xlabel('Date', fontsize=10)
        ax1.set_ylabel('Remaining Effort (Days)', fontsize=10, color='#1565c0')
        ax1.tick_params(axis='y', labelcolor='#1565c0')
        ax1.set_title(f'Sprint Burndown Chart (End: {end_date.date()})', fontsize=14, fontweight='bold', pad=20)
        
        # Force X-Axis to show full 14-day sprint range
        ax1.set_xlim(start_date, end_date)
        import matplotlib.dates as mdates
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')

        # --- Axis 2: Tasks ---
        ax2 = ax1.twinx()
        
        # Remaining Tasks (Line)
        ax2.plot(sprint_data['Date'], sprint_data['Remaining Tasks'], 
                 color='#90caf9', linewidth=2, linestyle='-', label='Remaining Tasks')
        
        # Completed Tasks (Bar)
        ax2.bar(sprint_data['Date'], sprint_data['Completed Tasks'], 
                color='#ffb300', alpha=0.6, width=0.4, label='Completed Tasks')

        ax2.set_ylabel('Tasks Count', fontsize=10, color='#555')
        ax2.tick_params(axis='y', labelcolor='#555')
        
        # Grid & Spines
        ax1.grid(True, linestyle='--', alpha=0.3)
        ax2.grid(False) # Disable second grid
        
        # Legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', frameon=True)

        plt.tight_layout()
        return fig

    def generate_interactive_assignee_progress_chart(self):
        """
        Generates an interactive Plotly bar chart of Time Spent vs Remaining Estimate per Assignee.
        Input units: Seconds. Output units: Days (8h).
        """
        if self.df is None:
            return None

        required_cols = ['Assignee', 'Remaining Estimate', 'Time Spent']
        if not all(col in self.df.columns for col in required_cols):
            return None

        # Data Prep
        # 1 day = 28800 seconds (8 hours)
        CONVERSION_FACTOR = 28800
        
        df_chart = self.df.copy()
        
        # Filter out Sub-tasks to avoid double counting (User Request)
        if 'Issue Type' in df_chart.columns:
            df_chart = df_chart[df_chart['Issue Type'] != 'Sub-task']
            
        df_chart['Remaining Days'] = pd.to_numeric(df_chart['Remaining Estimate'], errors='coerce').fillna(0) / CONVERSION_FACTOR
        df_chart['Spent Days'] = pd.to_numeric(df_chart['Time Spent'], errors='coerce').fillna(0) / CONVERSION_FACTOR
        
        # Group by Assignee
        assignee_stats = df_chart.groupby('Assignee')[['Remaining Days', 'Spent Days']].sum().reset_index()
        
        if assignee_stats.empty:
            return None

        # Create Plotly Figure
        fig = go.Figure()

        # Add Time Spent Bar
        fig.add_trace(go.Bar(
            x=assignee_stats['Assignee'],
            y=assignee_stats['Spent Days'],
            name='Time Spent (Days)',
            marker_color='#4caf50', # Green
            hovertemplate='<b>%{x}</b><br>Time Spent: %{y:.2f} Days<extra></extra>'
        ))

        # Add Remaining Estimate Bar
        fig.add_trace(go.Bar(
            x=assignee_stats['Assignee'],
            y=assignee_stats['Remaining Days'],
            name='Remaining (Days)',
            marker_color='#2196f3', # Blue
            hovertemplate='<b>%{x}</b><br>Remaining: %{y:.2f} Days<extra></extra>'
        ))

        # Update Layout
        fig.update_layout(
            title='<b>Resource Utilization: Spent vs Remaining</b>',
            xaxis_title='Assignee',
            yaxis_title='Days (8h)',
            barmode='stack', # Stacked to show total effort load
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=60, b=20),
            height=500
        )

        return fig

    def generate_assignee_progress_chart(self):
        """
        Generates a bar chart of Time Spent vs Remaining Estimate per Assignee.
        Input units: Seconds. Output units: Days (8h).
        """
        if self.df is None:
            return None

        required_cols = ['Assignee', 'Remaining Estimate', 'Time Spent']
        if not all(col in self.df.columns for col in required_cols):
            return None

        # Data Prep
        # 1 day = 28800 seconds (8 hours)
        CONVERSION_FACTOR = 28800
        
        df_chart = self.df.copy()
        
        # Filter out Sub-tasks to avoid double counting (User Request)
        if 'Issue Type' in df_chart.columns:
            df_chart = df_chart[df_chart['Issue Type'] != 'Sub-task']
            
        df_chart['Remaining Days'] = pd.to_numeric(df_chart['Remaining Estimate'], errors='coerce').fillna(0) / CONVERSION_FACTOR
        df_chart['Spent Days'] = pd.to_numeric(df_chart['Time Spent'], errors='coerce').fillna(0) / CONVERSION_FACTOR
        
        # Group by Assignee
        assignee_stats = df_chart.groupby('Assignee')[['Remaining Days', 'Spent Days']].sum().reset_index()
        
        if assignee_stats.empty:
            return None

        # Plotting
        try:
            plt.style.use('seaborn-v0_8-whitegrid')
        except:
            pass

        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Bar width
        bar_width = 0.35
        index = range(len(assignee_stats))
        
        # Bars
        bar1 = ax.bar(index, assignee_stats['Spent Days'], bar_width, label='Time Spent (Days)', color='#1a4d2e')
        bar2 = ax.bar([i + bar_width for i in index], assignee_stats['Remaining Days'], bar_width, label='Remaining (Days)', color='#81c784')
        
        # Styling
        ax.set_xlabel('Assignee', fontsize=10, color='#666')
        ax.set_ylabel('Days (8h)', fontsize=10, color='#666')
        ax.set_title('Resource Utilization: Spent vs Remaining', fontsize=14, fontweight='bold', pad=20, loc='left', color='#333')
        ax.set_xticks([i + bar_width / 2 for i in index])
        ax.set_xticklabels(assignee_stats['Assignee'], rotation=45, ha='right')
        ax.legend()
        
        # Spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#ccc')
        ax.spines['bottom'].set_color('#ccc')
        
        plt.tight_layout()
        return fig

    def check_assignee_workload(self, low_capacity_assignees=None):
        """
        Rule 5: Check total sum of Remaining Estimate for each assignee.
        Standard Capacity: 10 Days (Red > 10, Yellow > 8)
        Low Capacity (for specific assignees): 5 Days (Red > 5, Yellow > 4)
        Assumes Remaining Estimate is in seconds (converted to 8h days).
        """
        if self.df is None:
            return None
            
        if 'Assignee' not in self.df.columns or 'Remaining Estimate' not in self.df.columns:
            return None
            
        low_capacity_assignees = low_capacity_assignees or []
            
        # 1 day = 28800 seconds (8 hours)
        CONVERSION_FACTOR = 28800
        
        df_workload = self.df.copy()
        
        # Filter out Sub-tasks to avoid double counting (User Request)
        if 'Issue Type' in df_workload.columns:
            df_workload = df_workload[df_workload['Issue Type'] != 'Sub-task']
            
        # Convert to numeric, handle errors
        df_workload['Remaining Estimate'] = pd.to_numeric(df_workload['Remaining Estimate'], errors='coerce').fillna(0)
        
        # Group by Assignee
        workload = df_workload.groupby('Assignee')['Remaining Estimate'].sum().reset_index()
        
        # Convert to Days
        workload['Remaining Days'] = workload['Remaining Estimate'] / CONVERSION_FACTOR
        
        # Filter for flags
        flagged = []
        default_limit = self.rules.get('workload_limit_days', 10.0)
        
        for _, row in workload.iterrows():
            days = row['Remaining Days']
            assignee = row['Assignee']
            
            # Determine Capacity Limit
            if assignee in low_capacity_assignees:
                limit = default_limit / 2.0 # Half capacity rule
                warning_limit = limit * 0.8
            else:
                limit = float(default_limit)
                warning_limit = limit * 0.8
            
            if days > limit:
                flagged.append({
                    'Assignee': assignee,
                    'Total Remaining (Days)': round(days, 2),
                    'Capacity Limit': limit,
                    'Status': 'Overloaded',
                    'Color': 'Red'
                })
            elif days > warning_limit:
                flagged.append({
                    'Assignee': assignee,
                    'Total Remaining (Days)': round(days, 2),
                    'Capacity Limit': limit,
                    'Status': 'High Load',
                    'Color': 'Yellow'
                })
                
        return pd.DataFrame(flagged)

    def analyze_progress(self):
        """Analyzes task progress and identifies risks."""
        if self.df is None:
            return None

        # Identify tasks with high remaining time
        if 'Remaining Estimate' in self.df.columns and 'Summary' in self.df.columns:
             # Threshold from rules (hours -> seconds)
            threshold_hours = self.rules.get('risk_threshold_hours', 10)
            threshold_seconds = threshold_hours * 3600
            
            # Using 'Summary' or 'Task' depending on data. 'Task' was used in previous code but 'Summary' is standard Jira
            col_name = 'Task' if 'Task' in self.df.columns else 'Summary'
            
            # Ensure numeric
            self.df['Remaining Estimate'] = pd.to_numeric(self.df['Remaining Estimate'], errors='coerce').fillna(0)
            
            high_risk = self.df[self.df['Remaining Estimate'] > threshold_seconds].copy()
            
            # Formatting for display if needed
            if not high_risk.empty:
                high_risk['Task'] = high_risk[col_name]
                high_risk['Remaining (Days)'] = (high_risk['Remaining Estimate'] / 28800).round(2)
                
            return high_risk
        return None

    def generate_workload_chart(self):
        """
        Generates a stacked bar chart of workload per assignee using Plotly.
        """
        if self.df is None or self.df.empty:
            return None
            
        # Prepare data
        # Filter for items with remaining estimate > 0
        if 'Remaining Estimate' not in self.df.columns or 'Assignee' not in self.df.columns:
            return None

        work_df = self.df[self.df['Remaining Estimate'] > 0].copy()
        
        # Filter out Sub-tasks to avoid double counting (User Request)
        if 'Issue Type' in work_df.columns:
            work_df = work_df[work_df['Issue Type'] != 'Sub-task']
        
        if work_df.empty:
            return None
            
        # Convert seconds to days
        work_df['Remaining Days'] = work_df['Remaining Estimate'] / 28800
        
        # Create chart
        # Stacked by Issue Key to show individual tickets
        fig = px.bar(
            work_df, 
            x='Assignee', 
            y='Remaining Days', 
            color='Issue key', 
            title='Individual Workload Breakdown (Days)',
            hover_data=['Summary', 'Priority', 'Status'],
            labels={'Remaining Days': 'Days Required'},
            text_auto='.1f'
        )
        
        fig.update_layout(
            xaxis_title="Assignee",
            yaxis_title="Days Required",
            legend_title="Ticket",
            hovermode="closest"
        )
        
        return fig
