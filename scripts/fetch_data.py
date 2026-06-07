import os
import json
import sys
from datetime import datetime
import pandas as pd
import numpy as np

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.afl_provider import FryziggProvider as Provider

class AFLDataEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        if isinstance(obj, (np.int64, np.int32, np.float64, np.float32)):
            if np.isnan(obj):
                return None
            return obj.item()
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if pd.isna(obj):
            return None
        return super().default(obj)

def save_json(data, filename):
    # Absolute path to workspace root data folder
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    path = os.path.join(base_dir, 'data', 'raw', filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, cls=AFLDataEncoder)
    print(f"Saved {filename} to {path}")

def main():
    provider = Provider()
    
    print("Fetching teams...")
    try:
        teams = provider.get_teams()
        save_json(teams, 'teams.json')
    except Exception as e:
        print(f"Error fetching teams: {e}")
        
    print("Fetching fixtures from Squiggle API...")
    try:
        import urllib.request
        url = 'https://api.squiggle.com.au/?q=games;year=2026'
        req = urllib.request.Request(url, headers={'User-Agent': 'AFL Narrative Engine'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            save_json(data['games'], 'fixture_2026.json')
    except Exception as e:
        print(f"Error fetching fixtures: {e}")
    
    # Use 2026
    years = [2026]
    
    for year in years:
        print(f"Fetching data for {year}...")
        try:
            # Fetch Matches (from fixture)
            # The provider now expects all matches in the provider's df.
            # We filter by year within get_matches.
            matches = provider.get_matches(year)
            if matches:
                save_json(matches, f'matches_{year}.json')
                print(f"  Saved {len(matches)} matches for {year}.")
            else:
                print(f"No match data found for {year}")

            # Fetch Ladders
            ladders = provider.get_season_ladders(year)
            if ladders:
                save_json(ladders, f'ladders_{year}.json')

            # Fetch Team Stats (Micro-metrics)
            if teams:
                for team_obj in teams:
                    team_name = team_obj['name']
                    print(f"  Fetching stats for {team_name} in {year}...")
                    team_stats = provider.get_team_stats(team_name, year)
                    if team_stats:
                        # Sanitize filename
                        safe_name = team_name.replace(" ", "_").lower()
                        save_json(team_stats, f'stats_{year}_{safe_name}.json')
        except Exception as e:
            print(f"Error fetching data for {year}: {e}")

if __name__ == "__main__":
    main()
