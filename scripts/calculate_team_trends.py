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

    # Pass 1: Calculate metrics and current ladder for all teams
    team_data_map = {}
    
    for team_obj in teams:
        team_name = team_obj['name']
        
        # Get team matches
        team_matches = df_matches[
            (df_matches['home_team'] == team_name) | 
            (df_matches['away_team'] == team_name)
        ].copy()
        
        if len(team_matches) < 5:
            team_data_map[team_name] = {
                "team": team_name,
                "trend": "Stable",
                "supporting_metrics": {
                    "reason": "Insufficient data",
                    "games_played": len(team_matches)
                },
                "current_points": 0,
                "current_percentage": 100,
                "form_modifier": 1.0,
                "x_pts": 0,
                "x_pct": 100
            }
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
        
        def calculate_quarter_margins(row):
            is_home = row['home_team'] == team_name
            try:
                team_detail = row['Home team score detail'] if is_home else row['Away team score detail']
                opp_detail = row['Away team score detail'] if is_home else row['Home team score detail']
                
                t_q1 = team_detail[0] * 6 + team_detail[1]
                t_q2 = team_detail[2] * 6 + team_detail[3]
                t_q3 = team_detail[4] * 6 + team_detail[5]
                t_q4 = team_detail[6] * 6 + team_detail[7]
                
                o_q1 = opp_detail[0] * 6 + opp_detail[1]
                o_q2 = opp_detail[2] * 6 + opp_detail[3]
                o_q3 = opp_detail[4] * 6 + opp_detail[5]
                o_q4 = opp_detail[6] * 6 + opp_detail[7]
                
                return pd.Series([
                    t_q1 - o_q1,
                    (t_q2 - t_q1) - (o_q2 - o_q1),
                    (t_q3 - t_q2) - (o_q3 - o_q2),
                    (t_q4 - t_q3) - (o_q4 - o_q3)
                ])
            except (KeyError, TypeError, IndexError):
                return pd.Series([0, 0, 0, 0])
        
        team_matches[['q1_margin', 'q2_margin', 'q3_margin', 'q4_margin']] = team_matches.apply(calculate_quarter_margins, axis=1)

        # Calculate current season (2026) ladder for the team
        team_matches_current = team_matches[team_matches['date'].dt.year == 2026]
        
        current_points = 0
        current_pts_for = 0
        current_pts_against = 0
        
        for _, row in team_matches_current.iterrows():
            current_pts_for += row['score']
            current_pts_against += row['opp_score']
            if row['won']:
                current_points += 4
            elif row['score'] == row['opp_score']:
                current_points += 2
                
        current_percentage = (current_pts_for / current_pts_against * 100) if current_pts_against > 0 else 100

        # Calculate trends based on last 5 vs previous 5
        last_5 = team_matches.tail(5)
        prev_5 = team_matches.iloc[-10:-5] if len(team_matches) >= 10 else pd.DataFrame()
        
        recent_win_rate = last_5['won'].mean()
        recent_avg_margin = last_5['team_margin'].mean()
        recent_avg_score = last_5['score'].mean()
        
        # Strength of Schedule (SoS)
        recent_sos = last_5['opp_strength'].mean() if not last_5.empty else 0.5
        recent_sos_multiplier = recent_sos / 0.5 if recent_sos > 0 else 1.0
        
        # Consecutive losses
        consecutive_losses = 0
        for won in reversed(team_matches['won'].tolist()):
            if not won:
                consecutive_losses += 1
            else:
                break
                
        # New Metrics
        finishing_power = last_5['q4_margin'].mean() if not last_5.empty else 0
        q1_power = last_5['q1_margin'].mean() if not last_5.empty else 0
        q3_power = last_5['q3_margin'].mean() if not last_5.empty else 0
        
        # Rolling Efficiency (Last 3 games)
        last_3 = team_matches.tail(3)
        pts_for = last_3['score'].sum()
        pts_against = last_3['opp_score'].sum()
        rolling_efficiency = (pts_for / pts_against * 100) if pts_against > 0 else 100
        
        narrative_tags = []
        
        # Group Chat Fuel Tags (from PRD)
        if recent_win_rate > 0.6 and recent_sos < 0.4:
            narrative_tags.append("Flat-Track Bullies")
            
        if finishing_power > 10 and abs(recent_avg_margin) < 12:
            narrative_tags.append("The Cardiac Kids")
            
        if q3_power > 15 and q3_power > (q1_power + 10) and q3_power > (finishing_power + 10):
            narrative_tags.append("Premiership Quarter Specialists")
            
        if recent_win_rate < 0.3 and -15 < recent_avg_margin < 0:
            narrative_tags.append("Honourable Losses")
            
        if len(team_matches) >= 15 and recent_win_rate <= 0.2 and consecutive_losses >= 3:
            # We don't have season_win_rate easily available without extra calculation, so just proxy it
            narrative_tags.append("September Teasers")
        
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

        # Step A: Calculate Form Modifier
        norm_efficiency = rolling_efficiency / 100.0
        norm_win_rate = recent_win_rate / 0.5
        norm_sos = recent_sos_multiplier
        form_modifier = (norm_efficiency * 0.5) + (norm_win_rate * 0.3) + (norm_sos * 0.2)

        # Step B: Calculate Expected Points & Percentage
        x_pts = current_points * form_modifier
        x_pct = current_percentage * form_modifier

        team_data_map[team_name] = {
            "team": team_name,
            "trend": trend,
            "narrative_tags": narrative_tags,
            "current_points": current_points,
            "current_percentage": current_percentage,
            "form_modifier": form_modifier,
            "x_pts": x_pts,
            "x_pct": x_pct,
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
                "consecutive_losses": int(consecutive_losses),
                "games_analyzed": len(team_matches)
            }
        }

    # Pass 2: Sort to find CLP and ELP, and apply final narrative tags
    # Calculate Current Ladder Position (CLP)
    sorted_by_clp = sorted(
        team_data_map.values(), 
        key=lambda x: (x.get("current_points", 0), x.get("current_percentage", 0)), 
        reverse=True
    )
    
    for i, t in enumerate(sorted_by_clp):
        t["current_ladder_position"] = i + 1

    # Calculate Expected Ladder Position (ELP)
    sorted_by_elp = sorted(
        team_data_map.values(), 
        key=lambda x: (x.get("x_pts", 0), x.get("x_pct", 0)), 
        reverse=True
    )

    for i, t in enumerate(sorted_by_elp):
        t["expected_ladder_position"] = i + 1

    results = []
    for team_data in team_data_map.values():
        if team_data["trend"] == "Stable" and "reason" in team_data["supporting_metrics"]:
            results.append(team_data)
            continue
            
        clp = team_data["current_ladder_position"]
        elp = team_data["expected_ladder_position"]
        trend = team_data["trend"]
        
        # Tag Name Triggers / Logic
        if trend == "Falling" and team_data["supporting_metrics"]["consecutive_losses"] >= 3:
            team_data["narrative_tags"].append("Sinking Ship")
            
        if clp > elp and (clp - elp) >= 3 and team_data["supporting_metrics"]["finishing_power"] < -10:
            team_data["narrative_tags"].append("The Ultimate Tease")
            
        if clp <= 4 and elp >= clp + 4:
            team_data["narrative_tags"].append("Paper Tigers")
            
        if clp >= 8 and elp <= clp - 4:
            team_data["narrative_tags"].append("Sleeping Giants")
            
        if abs(clp - elp) <= 1:
            team_data["narrative_tags"].append("Market Corrected")
            
        if elp <= 4 and trend == "Falling":
            team_data["narrative_tags"].append("Glass Ceiling")
            
        if clp >= 11 and elp <= 10 and trend == "Rising":
            team_data["narrative_tags"].append("The Great Escape")
            
        if 7 <= clp <= 10:
            team_data["narrative_tags"].append("Wildcard Contender")

        results.append(team_data)

    # Save output
    output_path = metrics_dir / 'team_trends.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Successfully calculated trends for {len(results)} teams.")
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    calculate_team_trends()
