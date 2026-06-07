import pandas as pd
from typing import List, Dict, Any
from utils.fetch_raw_data import get_data
from .provider import AFLDataProvider

class FryziggProvider(AFLDataProvider):
    def __init__(self):
        self.df = get_data()

    def get_teams(self) -> List[Dict[str, Any]]:
        """Fetch all current AFL teams from the dataset."""
        # Use the team list from the logs dataframe since teams.json is failing
        if self.df is None or 'team' not in self.df.columns:
            return []
        teams = self.df['team'].dropna().unique().tolist()
        return [{"name": team} for team in teams]

    def get_matches(self, year: int) -> List[Dict[str, Any]]:
        """Fetch all matches for a given year."""
        import json
        import os
        # Base dir is one level up from src (where src/data/afl_provider.py lives)
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        fixture_path = os.path.join(base_dir, 'data', 'raw', f'fixture_{year}.json')
        if not os.path.exists(fixture_path):
            print(f"DEBUG: Fixture path {fixture_path} not found. (Base dir: {base_dir})")
            return []
        with open(fixture_path, 'r') as f:
            data = json.load(f)
            print(f"DEBUG: Found {len(data)} matches in {fixture_path}")
            return data

    def get_team_stats(self, team_name: str, year: int) -> List[Dict[str, Any]]:
        """Fetch player-level stats for a team in a specific year."""
        # Stats are cached as individual stats_YYYY_teamname.json files
        import json
        import os
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        safe_name = team_name.replace(" ", "_").lower()
        stats_path = os.path.join(base_dir, 'data', 'raw', f'stats_{year}_{safe_name}.json')
        
        if not os.path.exists(stats_path):
            return []
            
        with open(stats_path, 'r') as f:
            return json.load(f)

    def get_season_ladders(self, year: int) -> List[Dict[str, Any]]:
        """Fetch ladder states throughout the season."""
        return []
