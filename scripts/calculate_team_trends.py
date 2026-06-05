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
            
    # Load player match logs
    player_logs_path = raw_dir / 'player_match_logs_2026.json'
    player_logs = []
    if player_logs_path.exists():
        with open(player_logs_path, 'r') as f:
            player_logs = json.load(f)
            
    # Group player logs by team and match_id
    team_player_logs = {}
    for log in player_logs:
        t = log.get('team')
        if t not in team_player_logs:
            team_player_logs[t] = {}
        m_id = log.get('match_id')
        if m_id not in team_player_logs[t]:
            team_player_logs[t][m_id] = []
        team_player_logs[t][m_id].append(log)
    
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
    
    # Load future fixtures
    future_data = []
    fixture_path = raw_dir / 'fixture_2026.json'
    if fixture_path.exists():
        with open(fixture_path, 'r') as f:
            fixtures = json.load(f)
            for fix in fixtures:
                if fix.get('complete') == 0:
                    try:
                        future_data.append({
                            'date': pd.to_datetime(fix['date']),
                            'home_team': fix['hteam'],
                            'away_team': fix['ateam'],
                            'home_score': None,
                            'away_score': None,
                            'winner': None,
                            'margin': None,
                            'is_future': True
                        })
                    except (KeyError, ValueError):
                        continue
                        
    df_future = pd.DataFrame(future_data).sort_values('date') if future_data else pd.DataFrame()
    if not df_matches.empty:
        df_matches['is_future'] = False
        
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
            
    # Now merge future matches for next_3_sos calculation
    if not df_future.empty:
        df_all_matches = pd.concat([df_matches, df_future], ignore_index=True)
    else:
        df_all_matches = df_matches.copy()

    # Pass 1: Calculate metrics and current ladder for all teams
    team_data_map = {}
    
    for team_obj in teams:
        team_name = team_obj['name']
        
        # Get team matches
        team_matches_all = df_all_matches[
            (df_all_matches['home_team'] == team_name) | 
            (df_all_matches['away_team'] == team_name)
        ].copy()
        
        team_matches = team_matches_all[~team_matches_all['is_future']].copy()
        team_future = team_matches_all[team_matches_all['is_future']].copy()
        
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
            
        # Predictive Friction / The Next 3 Weeks
        next_3 = team_future.head(3).copy()
        def get_future_opponent(row):
            return row['away_team'] if row['home_team'] == team_name else row['home_team']
        
        if len(next_3) > 0:
            next_3['opponent'] = next_3.apply(get_future_opponent, axis=1)
            next_3['opp_strength'] = next_3['opponent'].map(team_win_rates).fillna(0.5)
            next_3_sos = next_3['opp_strength'].mean()
        else:
            next_3_sos = 0.5
            
        if trend == "Rising" and next_3_sos > 0.55:
            narrative_tags.append("Reality Check Window")
        elif trend == "Falling" and next_3_sos < 0.45:
            narrative_tags.append("Soft Landing")

        # Step A: Calculate Form Modifier
        norm_efficiency = rolling_efficiency / 100.0
        norm_win_rate = recent_win_rate / 0.5
        norm_sos = recent_sos_multiplier
        form_modifier = (norm_efficiency * 0.5) + (norm_win_rate * 0.3) + (norm_sos * 0.2)

        # Step B: Calculate Expected Points & Percentage
        x_pts = current_points * form_modifier
        x_pct = current_percentage * form_modifier

        # Player Correlations
        key_players = []
        
        # We will use the 3 to 5 week match windows.
        # Find the match_ids for this team in 2026.
        if team_name in team_player_logs:
            team_matches_logs = team_player_logs[team_name]
            # Sort match_ids chronologically (last 8 chars are YYYYMMDD)
            sorted_m_ids = sorted(team_matches_logs.keys(), key=lambda x: x[-8:])
            
            if len(sorted_m_ids) >= 10:
                last_5_ids = sorted_m_ids[-5:]
                prev_5_ids = sorted_m_ids[-10:-5]
            else:
                last_5_ids = sorted_m_ids[-5:] if len(sorted_m_ids) >= 5 else []
                prev_5_ids = sorted_m_ids[:-5] if len(sorted_m_ids) >= 5 else []
                
            if last_5_ids and prev_5_ids:
                # Compile player stats for last 5 and prev 5
                def get_player_stats_for_window(m_ids):
                    p_stats = {}
                    for m_id in m_ids:
                        for log in team_matches_logs[m_id]:
                            p_name = log.get('Player')
                            if not p_name or "players used" in p_name.lower():
                                continue
                            if p_name not in p_stats:
                                p_stats[p_name] = {'games': 0, 'CP': 0, 'CL': 0, '#': log.get('#')}
                            p_stats[p_name]['games'] += 1
                            p_stats[p_name]['CP'] += log.get('CP', 0) if pd.notna(log.get('CP')) else 0
                            p_stats[p_name]['CL'] += log.get('CL', 0) if pd.notna(log.get('CL')) else 0
                    return p_stats
                    
                recent_stats = get_player_stats_for_window(last_5_ids)
                prev_stats = get_player_stats_for_window(prev_5_ids)

                if trend == "Rising":
                    # Look for top players by CP in recent window and check their growth vs prev window
                    candidates = sorted([p for p_name, p in recent_stats.items()], key=lambda x: x['CP'], reverse=True)[:5]
                    
                    best_player = None
                    max_delta = -1.0
                    
                    for p in candidates:
                        # Find name
                        p_name = next(name for name, stats in recent_stats.items() if stats == p)
                        avg_recent = p['CP'] / p['games'] if p['games'] > 0 else 0
                        
                        if p_name in prev_stats:
                            p_prev = prev_stats[p_name]
                            avg_prev = p_prev['CP'] / p_prev['games'] if p_prev['games'] > 0 else 0
                            delta = (avg_recent - avg_prev) / avg_prev if avg_prev > 0 else 0.2
                        else:
                            delta = 0.25 # arbitrary spike if they didn't play prev 5
                        
                        if delta > max_delta:
                            max_delta = delta
                            best_player = (p, p_name, avg_recent, avg_prev if p_name in prev_stats else avg_recent/1.25, delta)

                    if best_player:
                        p, p_name, avg_recent, avg_prev, delta = best_player
                        if delta > 0.05: # Only include if it's actually a spike
                            key_players.append({
                                "playerId": str(p.get("#", "")),
                                "playerName": p_name,
                                "baselineScore": round(avg_prev, 1),
                                "windowScore": round(avg_recent, 1),
                                "delta": round(delta, 3),
                                "role": "Engine Room",
                                "narrativeBlurb": f"has dominated the inside with a {delta*100:.1f}% spike in contested possessions over the last 5 weeks (avg {round(avg_recent, 1)}), fueling the team's surge.",
                                "statType": "Contested Possessions"
                            })
                            narrative_tags.append("The Engine Room")
                            
                elif trend == "Falling":
                    # Look for players who were high in CL in prev window and dropped in recent window
                    top_prev_cl = sorted([(name, p) for name, p in prev_stats.items()], key=lambda x: x[1]['CL'], reverse=True)[:5]
                    
                    worst_player = None
                    min_delta = 1.0
                    
                    for p_name, p_prev in top_prev_cl:
                        avg_prev = p_prev['CL'] / p_prev['games'] if p_prev['games'] > 0 else 0
                        
                        if p_name in recent_stats:
                            p_recent = recent_stats[p_name]
                            avg_recent = p_recent['CL'] / p_recent['games'] if p_recent['games'] > 0 else 0
                            delta = (avg_recent - avg_prev) / avg_prev if avg_prev > 0 else -0.2
                        else:
                            avg_recent = 0
                            delta = -1.0 # Player dropped completely
                        
                        if delta < min_delta:
                            min_delta = delta
                            worst_player = (p_prev, p_name, avg_recent, avg_prev, delta)

                    if worst_player:
                        p, p_name, avg_recent, avg_prev, delta = worst_player
                        if delta < -0.05: # Only include if it's a real drop
                            key_players.append({
                                "playerId": str(p.get("#", "")),
                                "playerName": p_name,
                                "baselineScore": round(avg_prev, 1),
                                "windowScore": round(avg_recent, 1),
                                "delta": round(delta, 3),
                                "role": "Missing Link",
                                "narrativeBlurb": f"has seen their clearance numbers plummet by {abs(delta)*100:.1f}% over the last 5 weeks (down to {round(avg_recent, 1)} per game), leaving a massive hole in the middle.",
                                "statType": "Clearances"
                            })
                            narrative_tags.append("The Missing Link")
                
                # Check for One-Man Band in recent window
                if recent_stats:
                    sorted_cl = sorted([(name, p) for name, p in recent_stats.items()], key=lambda x: x[1]['CL'], reverse=True)
                    if len(sorted_cl) > 0:
                        top_p_name, top_p = sorted_cl[0]
                        top_cl = top_p['CL']
                        total_cl = sum([p['CL'] for p in recent_stats.values()])
                        if total_cl > 0 and (top_cl / total_cl) > 0.35:
                            if not any(kp["role"] == "One-Man Band" for kp in key_players):
                                key_players.append({
                                    "playerId": str(top_p.get("#", "")),
                                    "playerName": top_p_name,
                                    "baselineScore": 0,
                                    "windowScore": round(top_cl / top_p['games'] if top_p['games'] > 0 else 0, 1),
                                    "delta": 0,
                                    "role": "One-Man Band",
                                    "narrativeBlurb": f"is carrying a ridiculous {(top_cl / total_cl * 100):.1f}% of the team's total clearances over the last 5 weeks.",
                                    "statType": "Clearances"
                                })
                                narrative_tags.append("The One-Man Band")

        team_data_map[team_name] = {
            "team": team_name,
            "trend": trend,
            "narrative_tags": narrative_tags,
            "key_players": key_players,
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
                "next_3_sos": float(next_3_sos),
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
