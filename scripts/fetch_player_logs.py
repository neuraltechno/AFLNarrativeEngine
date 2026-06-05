import os
import json
import re
import urllib.request
import pandas as pd
from datetime import datetime

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
raw_dir = os.path.join(base_dir, 'data', 'raw')

def fetch_match_logs(year=2026):
    print(f"Fetching match logs for {year}...")
    url = f'https://afltables.com/afl/seas/{year}.html'
    
    req = urllib.request.Request(url, headers={'User-Agent': 'AFL Narrative Engine'})
    html = urllib.request.urlopen(req).read().decode('utf-8')
    
    match_urls = re.findall(r'href="([^"]*/stats/games/[^"]+\.html)"', html)
    # Deduplicate and fix relative URLs
    match_urls = list(dict.fromkeys(match_urls))
    
    match_logs = []
    
    for i, rel_url in enumerate(match_urls):
        full_url = rel_url.replace('../', 'https://afltables.com/afl/')
        print(f"[{i+1}/{len(match_urls)}] Fetching {full_url}")
        
        try:
            dfs = pd.read_html(full_url)
            # Find the player stats tables
            # Usually they are DataFrames with columns containing '#', 'Player', 'CP', 'CL', etc.
            for df in dfs:
                # Flatten MultiIndex columns if necessary
                if isinstance(df.columns, pd.MultiIndex):
                    # Usually ('Team Name - 2026', 'Player')
                    # We can extract the team name from the first level
                    team_col = df.columns[0][0]
                    if " - " in team_col:
                        team_name = team_col.split(" - ")[0]
                    else:
                        team_name = team_col
                    df.columns = [col[1] for col in df.columns]
                else:
                    continue
                
                if 'Player' in df.columns and 'CP' in df.columns:
                    # Extract date from URL or html (optional, can join with match data later)
                    # For now, let's just use the URL as a unique match ID
                    match_id = rel_url.split('/')[-1].replace('.html', '')
                    
                    # Filter out summary rows
                    df = df[df['#'].astype(str).str.isnumeric()]
                    
                    # Convert to dicts
                    records = df.to_dict(orient='records')
                    for rec in records:
                        rec['match_id'] = match_id
                        rec['team'] = team_name
                        rec['year'] = year
                        match_logs.append(rec)
        except Exception as e:
            print(f"Error fetching {full_url}: {e}")
            
    output_path = os.path.join(raw_dir, f'player_match_logs_{year}.json')
    with open(output_path, 'w') as f:
        # Convert nan to None for JSON
        import numpy as np
        
        class NpEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                if isinstance(obj, np.floating):
                    if np.isnan(obj):
                        return None
                    return float(obj)
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                return super(NpEncoder, self).default(obj)
                
        json.dump(match_logs, f, cls=NpEncoder, indent=2)
    print(f"Saved {len(match_logs)} player match records to {output_path}")

if __name__ == '__main__':
    fetch_match_logs(2026)