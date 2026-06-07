import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from utils.fetch_raw_data import get_data
import json
import os
import pandas as pd
from datetime import datetime

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
    # Using the new fetch system via utils.fetch_raw_data
    # The new get_data() function loads all logs from 2026 into a single DF.
    # To keep compatibility, let's load it and convert to the list of dicts required by the rest of the script.
    df_logs = get_data()
    player_logs = df_logs.to_dict(orient='records')
            
    # Group player logs by team and match_id
    team_player_logs = {}
    for log in player_logs:
        t = log.get('team')
        # match_id is not in these logs, but we have 'GM' (games played/match number proxy)
        # Use 'GM' as match_id to maintain consistency with team_player_logs structure
        m_id = str(log.get('GM')) 
        if t not in team_player_logs:
            team_player_logs[t] = {}
        if m_id not in team_player_logs[t]:
            team_player_logs[t][m_id] = []
        team_player_logs[t][m_id].append(log)
    
    # Process matches
    matches_data = []
    for m in all_matches:
        try:
            # Handle possible datetime parsing issues
            date_str = m.get('date') or m.get('Date')
            date = pd.to_datetime(date_str)
            
            # Squiggle API keys are 'hteam', 'ateam', 'hscore', 'ascore' etc, 
            # check what they actually are in matches_2026.json
            matches_data.append({
                'date': date,
                'home_team': m.get('hteam') or m.get('Home team'),
                'away_team': m.get('ateam') or m.get('Away Team'),
                'home_score': m.get('hscore') or m.get('Home team score'),
                'away_score': m.get('ascore') or m.get('Away team score'),
                'winner': m.get('winner') or m.get('Winning team'),
                'margin': m.get('margin') or m.get('Margin'),
                'Home team score detail': m.get('h_score_detail') or m.get('Home team score detail', []),
                'Away team score detail': m.get('a_score_detail') or m.get('Away team score detail', []),
                'round': m.get('round') or m.get('Round', 1)
            })
        except (KeyError, ValueError):
            continue
            
    df_matches = pd.DataFrame(matches_data).sort_values('date')
    # Filter 2026 only
    df_matches = df_matches[df_matches['date'].dt.year == 2026]
    
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
                            'is_future': True,
                            'round': fix.get('round', 1)
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

    # Pre-calculate previous season (2025) endpoints for anchor weights
    # We find each team's 2025 points and percentages to use as an anchor in early 2026
    df_matches_2025 = df_matches[df_matches['date'].dt.year == 2025]
    team_2025_stats = {}
    for team_obj in teams:
        t_name = team_obj['name']
        t_m_2025 = df_matches_2025[(df_matches_2025['home_team'] == t_name) | (df_matches_2025['away_team'] == t_name)]
        pts_2025 = 0
        pf_2025 = 0
        pa_2025 = 0
        for _, r in t_m_2025.iterrows():
            is_home = r['home_team'] == t_name
            score = r['home_score'] if is_home else r['away_score']
            opp_score = r['away_score'] if is_home else r['home_score']
            won = r['winner'] == t_name
            pf_2025 += score
            pa_2025 += opp_score
            if won:
                pts_2025 += 4
            elif score == opp_score:
                pts_2025 += 2
        pct_2025 = (pf_2025 / pa_2025 * 100) if pa_2025 > 0 else 100.0
        team_2025_stats[t_name] = {
            "pts": pts_2025,
            "pct": pct_2025
        }

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

        # Step A: Calculate Form Modifier (PIR / Trend upgrade centering around 1.0)
        form_modifier = 1.0 + (((rolling_efficiency - 100) / 100) * 0.4) + ((recent_win_rate - 0.5) * 0.4) + ((recent_sos - 0.5) * 0.2)

        # Step B: Calculate Expected Points & Percentage (With Early Season Anchor Weight)
        # Determine 2026 games played to apply decay weight
        games_played_2026 = len(team_matches_current)
        if games_played_2026 > 0 and games_played_2026 <= 5:
            # Anchor decays by 20% each week: round 1 has 80% 2025, round 5 has 0% 2025.
            # Blend current points/percent with last season endpoints.
            hist_weight = 1.0 - (games_played_2026 * 0.2)
            curr_weight = games_played_2026 * 0.2
            
            anchor_stats = team_2025_stats.get(team_name, {"pts": 32, "pct": 100.0}) # default average fallback
            # Scale 2025 points down to match the progression of 2026 games played
            # Average pts per game in 2025 * games played in 2026 is a good base
            scaled_2025_pts = (anchor_stats["pts"] / 23) * games_played_2026
            
            blended_pts = (scaled_2025_pts * hist_weight) + (current_points * curr_weight)
            blended_pct = (anchor_stats["pct"] * hist_weight) + (current_percentage * curr_weight)
            
            x_pts = blended_pts * form_modifier
            x_pct = blended_pct * form_modifier
        else:
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
                    # Upgrade: The Missing Link Identity Guard (Clearance delta <= -0.15 AND raw drop >= 1.5 clearances)
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
                        
                        raw_diff = avg_recent - avg_prev
                        # Apply Identity Guard filters
                        if delta <= -0.15 and raw_diff <= -1.5:
                            if delta < min_delta:
                                min_delta = delta
                                worst_player = (p_prev, p_name, avg_recent, avg_prev, delta)

                    if worst_player:
                        p, p_name, avg_recent, avg_prev, delta = worst_player
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
                
                # Check for One-Man Band in recent window (Upgrade: One-Man Band Safety Valve)
                if recent_stats:
                    sorted_cl = sorted([(name, p) for name, p in recent_stats.items()], key=lambda x: x[1]['CL'], reverse=True)
                    if len(sorted_cl) > 0:
                        top_p_name, top_p = sorted_cl[0]
                        top_cl = top_p['CL']
                        total_cl = sum([p['CL'] for p in recent_stats.values()])
                        
                        # Calculate team clearance differential over last 5 weeks
                        team_cl_games = last_5_ids
                        team_total_clearances = 0
                        opponent_total_clearances = 0
                        for m_id in team_cl_games:
                            # Search df_matches for this match to compare team clearances (using player logs sum vs opponent logs sum)
                            # Or we can just check if team average matches are won or margins are okay.
                            # Since we don't have direct team clearances in df_matches, let's sum them from player_logs.
                            # Fortunately, player_logs contains logs for all players of all matches.
                            t_logs = [log for log in player_logs if log.get('match_id') == m_id]
                            for log in t_logs:
                                if log.get('team') == team_name:
                                    team_total_clearances += log.get('CL', 0) if pd.notna(log.get('CL')) else 0
                                else:
                                    opponent_total_clearances += log.get('CL', 0) if pd.notna(log.get('CL')) else 0
                                    
                        if total_cl > 0 and (top_cl / total_cl) > 0.35 and team_total_clearances >= opponent_total_clearances:
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

        # Dynamic Cardiac Kids: Wins in last 5 matches >= 3 AND Count(Matches won where Q3_Margin < 0 and Q4_Margin > 0) >= 2
        cardiac_wins_count = 0
        for _, match_row in last_5.iterrows():
            # Check if team won
            if match_row['won']:
                # Get Q3 cumulative margin and Q4 cumulative margin
                # q3_margin is quarter-specific margin. Let's calculate cumulative margins
                # Cumulative Q3 margin = q1_margin + q2_margin + q3_margin
                # Cumulative Q4 margin = q1_margin + q2_margin + q3_margin + q4_margin (this matches team_margin)
                q1 = match_row['q1_margin']
                q2 = match_row['q2_margin']
                q3 = match_row['q3_margin']
                cumulative_q3 = q1 + q2 + q3
                if cumulative_q3 < 0: # team was trailing at 3QT but won at FT
                    cardiac_wins_count += 1
                    
        if recent_win_rate >= 0.6 and cardiac_wins_count >= 2:
            narrative_tags.append("The Cardiac Kids")

        # Dynamic Flat-Track Bullies: WR vs Top 8 Teams <= 0.20 AND WR vs Bottom 10 Teams >= 0.80
        # Wait, to know Top 8 and Bottom 10, we'll assign it in Pass 2 since we need the current ladder positions.
        # So we leave the default tag check out of Pass 1 and add it dynamically in Pass 2!

        if q3_power > 15 and q3_power > (q1_power + 10) and q3_power > (finishing_power + 10):
            narrative_tags.append("Premiership Quarter Specialists")
            
        if recent_win_rate < 0.3 and -15 < recent_avg_margin < 0:
            narrative_tags.append("Honourable Losses")
            
        if len(team_matches) >= 15 and recent_win_rate <= 0.2 and consecutive_losses >= 3:
            narrative_tags.append("September Teasers")

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
    sorted_by_clp = sorted(
        team_data_map.values(), 
        key=lambda x: (x.get("current_points", 0), x.get("current_percentage", 0)), 
        reverse=True
    )
    
    for i, t in enumerate(sorted_by_clp):
        t["current_ladder_position"] = i + 1

    # Map team name to its current ladder position for easy lookup
    team_ladder_ranks = {t["team"]: t["current_ladder_position"] for t in sorted_by_clp}

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
        t_name = team_data["team"]
        
        # Dynamic Flat-Track Bullies: WR vs Top 8 Teams <= 0.20 AND WR vs Bottom 10 Teams >= 0.80
        # Let's check team matches in 2026
        team_matches_all = df_all_matches[
            (df_all_matches['home_team'] == t_name) | 
            (df_all_matches['away_team'] == t_name)
        ].copy()
        team_matches_2026 = team_matches_all[(~team_matches_all['is_future']) & (team_matches_all['date'].dt.year == 2026)].copy()
        
        if len(team_matches_2026) >= 3:
            def get_opponent_and_won(row):
                opp = row['away_team'] if row['home_team'] == t_name else row['home_team']
                won = row['winner'] == t_name
                return pd.Series([opp, won])
                
            team_matches_2026[['opp', 'won']] = team_matches_2026.apply(get_opponent_and_won, axis=1)
            
            # Map opponent rank
            team_matches_2026['opp_rank'] = team_matches_2026['opp'].map(team_ladder_ranks).fillna(10)
            
            top_8_games = team_matches_2026[team_matches_2026['opp_rank'] <= 8]
            bottom_10_games = team_matches_2026[team_matches_2026['opp_rank'] > 8]
            
            wr_top_8 = top_8_games['won'].mean() if len(top_8_games) > 0 else 0.0
            wr_bottom_10 = bottom_10_games['won'].mean() if len(bottom_10_games) > 0 else 1.0
            
            if wr_top_8 <= 0.20 and wr_bottom_10 >= 0.80:
                if "Flat-Track Bullies" not in team_data["narrative_tags"]:
                    team_data["narrative_tags"].append("Flat-Track Bullies")

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

    # Sanitize NaNs before dumping to JSON
    def sanitize(obj):
        if isinstance(obj, float) and (pd.isna(obj) or obj != obj): # obj != obj is check for NaN
            return None
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [sanitize(v) for v in obj]
        return obj

    results = sanitize(results)

    # Save output
    output_path = metrics_dir / 'team_trends.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Successfully calculated trends for {len(results)} teams.")
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    calculate_team_trends()
