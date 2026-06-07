import os
import pandas as pd
import requests
import json

def get_data():
    # Load player match logs from 2026 JSON files
    raw_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'raw'))
    log_files = [f for f in os.listdir(raw_dir) if f.startswith('stats_2026_') and f.endswith('.json')]
    
    all_logs = []
    team_name_map = {} # Dummy map: in a real scenario, use fixture data to map team IDs or filenames
    
    for f in log_files:
        # Extract team name from filename
        team_name = f.replace("stats_2026_", "").replace(".json", "").replace("_", " ").title()
        with open(os.path.join(raw_dir, f), 'r') as file:
            try:
                data = json.load(file)
                if isinstance(data, list):
                    for log in data:
                        # Ensure 'team' is set from filename
                        log['team'] = team_name
                        all_logs.append(log)
                else:
                    data['team'] = team_name
                    all_logs.append(data)

            except Exception as e:
                print(f"Error loading {f}: {e}")
                
    return pd.DataFrame(all_logs)

