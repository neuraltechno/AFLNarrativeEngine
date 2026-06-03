import pandas as pd
from typing import List, Dict, Any
from pyAFL.teams import CURRENT_TEAMS
from pyAFL.seasons.models import Season
from .provider import AFLDataProvider

class PyAFLProvider(AFLDataProvider):
    def get_teams(self) -> List[Dict[str, Any]]:
        """Fetch all current AFL teams."""
        teams_data = []
        for team in CURRENT_TEAMS:
            # Safely handle attributes
            team_dict = {
                "name": getattr(team, 'name', str(team)),
            }
            # Add any other useful attributes found in __dict__
            teams_data.append(team_dict)
        return teams_data

    def get_matches(self, year: int) -> List[Dict[str, Any]]:
        """Fetch all matches for a given year."""
        season = Season(year)
        stats = season.get_season_stats()
        
        # match_summary is a DataFrame
        matches_df = stats.match_summary
        
        # Convert to records
        if isinstance(matches_df, pd.DataFrame):
            return matches_df.to_dict(orient='records')
        return []

    def get_team_stats(self, team_name: str, year: int) -> List[Dict[str, Any]]:
        """Fetch player-level stats for a team in a specific year."""
        for team in CURRENT_TEAMS:
            if team.name == team_name:
                stats_df = team.season_stats(year)
                if isinstance(stats_df, pd.DataFrame):
                    return stats_df.to_dict(orient='records')
        return []

    def get_season_ladders(self, year: int) -> List[Dict[str, Any]]:
        """Fetch ladder states throughout the season."""
        season = Season(year)
        stats = season.get_season_stats()
        if hasattr(stats, 'season_ladders') and isinstance(stats.season_ladders, dict):
            # season_ladders is often a dict of DataFrames keyed by round
            serialized_ladders = {}
            for round_name, df in stats.season_ladders.items():
                if isinstance(df, pd.DataFrame):
                    serialized_ladders[str(round_name)] = df.to_dict(orient='records')
            return [serialized_ladders]
        return []
