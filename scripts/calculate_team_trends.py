import json
import os
import pandas as pd
from datetime import datetime
from pathlib import Path

def calculate_team_trends():
    # Use absolute paths relative to workspace root
    base_dir = Path(__file__).parent.parent.absolute()
    raw_dir = base_dir / 'data' / 'raw'
    metrics_dir = base_dir / 'data' / 'metrics'
    
    # Load teams
    teams_path = raw_dir / 'teams.json'
    if not teams_path.exists():
        print(f"Error: {teams_path} not found.")
        return

    with open(teams_path, 'r') as f:
        teams = json.load(f)
    
    # Load all matches
    match_files = list(raw_dir.glob('matches_*.json'))
    all_matches = []
    for file in match_files:
        with open(file, 'r') as f:
            all_matches.extend(json.load(f))
    
    # Process matches
    matches_data = []
    for m in all_matches:
        try:
            date = datetime.fromisoformat(m['Date'])
            matches_data.append({
                'date': date,
                'home_team': m['Home team'],
                'away_team': m['Away Team'],
                'home_score': m['Home team score'],
                'away_score': m['Away team score'],
                'winner': m['Winning team'],
                'margin': m['Margin'],
                'Home team score detail': m.get('Home team score detail', []),
                'Away team score detail': m.get('Away team score detail', [])
            })
        except (KeyError, ValueError):
            continue
            
    df_matches = pd.DataFrame(matches_data).sort_values('date')
    
    # Pre-calculate overall win rates for Strength of Schedule (SoS)
    team_win_rates = {}
    for team_obj in teams:
        t_name = team_obj['name']
        t_matches = df_matches[(df_matches['home_team'] == t_name) | (df_matches['away_team'] == t_name)]
        if len(t_matches) > 0:
            wins = len(t_matches[t_matches['winner'] == t_name])
            team_win_rates[t_name] = wins / len(t_matches)
        else:
            team_win_rates[t_name] = 0.5

    results = []
    
    for team_obj in teams:
        team_name = team_obj['name']
        
        # Get team matches
        team_matches = df_matches[
            (df_matches['home_team'] == team_name) | 
            (df_matches['away_team'] == team_name)
        ].copy()
        
        if len(team_matches) < 5:
            results.append({
                "team": team_name,
                "trend": "Stable",
                "supporting_metrics": {
                    "reason": "Insufficient data",
                    "games_played": len(team_matches)
                }
            })
            continue
            
        # Add team-specific stats to each match
        def get_team_stats(row):
            is_home = row['home_team'] == team_name
            score = row['home_score'] if is_home else row['away_score']
            opponent_score = row['away_score'] if is_home else row['home_score']
            won = row['winner'] == team_name
            margin = score - opponent_score
            return pd.Series([score, opponent_score, won, margin])

        team_matches[['score', 'opp_score', 'won', 'team_margin']] = team_matches.apply(get_team_stats, axis=1)
        
        def get_opponent(row):
            return row['away_team'] if row['home_team'] == team_name else row['home_team']
            
        team_matches['opponent'] = team_matches.apply(get_opponent, axis=1)
        team_matches['opp_strength'] = team_matches['opponent'].map(team_win_rates)
        
        def calculate_q4_margin(row):
            is_home = row['home_team'] == team_name
            # Score details are cumulative: [Q1_G, Q1_B, Q2_G, Q2_B, Q3_G, Q3_B, Q4_G, Q4_B]
            # No, wait, they are: [Q1_pts, Q2_pts, Q3_pts, Q4_pts] based on the JSON
            # Ah, the JSON has 8 items: e.g., 3, 3, 4, 3, 7, 10, 12, 14
            # This looks like [Q1_G, Q1_B, Q2_G, Q2_B, Q3_G, Q3_B, Q4_G, Q4_B]
            # So Q4 total points = (Q4_G * 6 + Q4_B) - (Q3_G * 6 + Q3_B)
            try:
                team_detail = row['Home team score detail'] if is_home else row['Away team score detail']
                opp_detail = row['Away team score detail'] if is_home else row['Home team score detail']
                
                team_q4_pts = (team_detail[6] * 6 + team_detail[7]) - (team_detail[4] * 6 + team_detail[5])
                opp_q4_pts = (opp_detail[6] * 6 + opp_detail[7]) - (opp_detail[4] * 6 + opp_detail[5])
                return team_q4_pts - opp_q4_pts
            except (KeyError, TypeError, IndexError):
                return 0
        
        team_matches['q4_margin'] = team_matches.apply(calculate_q4_margin, axis=1)

        # Load team specific micro-stats (from fetch_data.py updates)
        safe_name = team_name.replace(" ", "_").lower()
        stats_files = list(raw_dir.glob(f'stats_*_{safe_name}.json'))
        
        # We need a way to aggregate CP and T per match, but the raw stats files only contain season totals for each player.
        # So we can't do per-match CP/T aggregation accurately with just the season totals.
        # We will focus on Finishing Power and Rolling Efficiency.

        # Calculate trends based on last 5 vs previous 5
        last_5 = team_matches.tail(5)
        prev_5 = team_matches.iloc[-10:-5] if len(team_matches) >= 10 else pd.DataFrame()
        
        recent_win_rate = last_5['won'].mean()
        recent_avg_margin = last_5['team_margin'].mean()
        recent_avg_score = last_5['score'].mean()
        
        # Strength of Schedule (SoS)
        recent_sos = last_5['opp_strength'].mean() if not last_5.empty else 0.5
        recent_sos_multiplier = recent_sos / 0.5 if recent_sos > 0 else 1.0
        
        # New Metrics
        finishing_power = last_5['q4_margin'].mean() if not last_5.empty else 0
        
        # Rolling Efficiency (Last 3 games)
        last_3 = team_matches.tail(3)
        pts_for = last_3['score'].sum()
        pts_against = last_3['opp_score'].sum()
        rolling_efficiency = (pts_for / pts_against * 100) if pts_against > 0 else 100
        
        narrative_tags = []
        
        if finishing_power > 10:
            narrative_tags.append("Elite 4th Quarter")
        elif finishing_power < -10:
            narrative_tags.append("Late Game Fade")
            
        if rolling_efficiency > 130:
            narrative_tags.append("Highly Efficient")
        elif rolling_efficiency < 70:
            narrative_tags.append("Struggling to Convert")
        
        if not prev_5.empty:
            prev_win_rate = prev_5['won'].mean()
            prev_avg_margin = prev_5['team_margin'].mean()
            
            prev_sos = prev_5['opp_strength'].mean()
            prev_sos_multiplier = prev_sos / 0.5 if prev_sos > 0 else 1.0
            
            win_rate_diff = recent_win_rate - prev_win_rate
            margin_diff = recent_avg_margin - prev_avg_margin
            
            weighted_margin_diff = (recent_avg_margin * recent_sos_multiplier) - (prev_avg_margin * prev_sos_multiplier)
            
            # Trend Logic (using weighted margin diff)
            if win_rate_diff >= 0.2 or weighted_margin_diff >= 15:
                trend = "Rising"
            elif win_rate_diff <= -0.2 or weighted_margin_diff <= -15:
                trend = "Falling"
            else:
                trend = "Stable"
        else:
            # Fallback for teams with 5-9 games
            if recent_win_rate >= 0.6:
                trend = "Rising"
            elif recent_win_rate <= 0.4:
                trend = "Falling"
            else:
                trend = "Stable"
            win_rate_diff = 0
            margin_diff = 0
            weighted_margin_diff = 0

        # Adjust narrative tags based on SoS
        if recent_sos > 0.55 and trend == "Rising":
            narrative_tags.append("Battle-Tested Rise")
        elif recent_sos < 0.45 and trend == "Rising":
            narrative_tags.append("Soft Draw Rise")

        results.append({
            "team": team_name,
            "trend": trend,
            "narrative_tags": narrative_tags,
            "supporting_metrics": {
                "recent_win_rate": float(recent_win_rate),
                "recent_avg_margin": float(recent_avg_margin),
                "recent_avg_score": float(recent_avg_score),
                "win_rate_trend": float(win_rate_diff),
                "margin_trend": float(margin_diff),
                "weighted_margin_trend": float(weighted_margin_diff),
                "strength_of_schedule": float(recent_sos),
                "finishing_power": float(finishing_power),
                "rolling_efficiency": float(rolling_efficiency),
                "games_analyzed": len(team_matches)
            }
        })

    # Save output
    output_path = metrics_dir / 'team_trends.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Successfully calculated trends for {len(results)} teams.")
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    calculate_team_trends()
