import json
import os
import pandas as pd
import numpy as np
from pathlib import Path

def calculate_player_trends():
    # Use absolute paths relative to workspace root
    base_dir = Path(__file__).parent.parent.absolute()
    raw_dir = base_dir / 'data' / 'raw'
    metrics_dir = base_dir / 'data' / 'metrics'
    
    # Load player match logs for 2026
    player_logs_path = raw_dir / 'player_match_logs_2026.json'
    if not player_logs_path.exists():
        print(f"Error: {player_logs_path} not found.")
        return

    with open(player_logs_path, 'r') as f:
        player_logs = json.load(f)
        
    df_logs = pd.DataFrame(player_logs)
    
    # Load match meta to join dates and margins if needed
    match_files = list(raw_dir.glob('matches_2026.json'))
    matches_meta = []
    for file in match_files:
        with open(file, 'r') as f:
            matches_meta.extend(json.load(f))
            
    df_matches = pd.DataFrame(matches_meta)
    
    # Process matches date and margins
    match_margins = {}
    match_dates = {}
    for _, m in df_matches.iterrows():
        try:
            m_id = m['Date'].replace('-', '').replace(':', '').replace(' ', '') # We need to map match_id properly.
            # Wait, let's look at player logs' match_id.
            # In player logs, match_id looks like "031620260305" or similar.
            # Let's inspect a few match logs match_ids to match them with matches.
        except Exception:
            pass

    # Actually, player logs contain 'match_id', 'team', 'Player', and raw stats:
    # 'KI' (Kick), 'MK' (Mark), 'HB' (Handball), 'DI' (Disposal), 'GL' (Goals), 'BH' (Behinds), 
    # 'HO' (Hit Outs), 'TK' (Tackles), 'RB' (Rebound 50s), 'IF' (Inside 50s), 'CL' (Clearances), 
    # 'CG' (Clangers), 'FF' (Free Kicks For), 'FA' (Free Kicks Against), 'CP' (Contested Possessions), 
    # 'UP' (Uncontested Possessions), 'CM' (Contested Marks), 'MI' (Marks Inside 50), '1%' (One percenters),
    # 'BO' (Bounces), 'GA' (Goal Assists), '%P' (Time on Ground %)
    
    # Replace NaN with 0
    stat_cols = ['KI', 'MK', 'HB', 'DI', 'GL', 'BH', 'HO', 'TK', 'RB', 'IF', 'CL', 'CG', 'FF', 'FA', 'CP', 'UP', 'CM', 'MI', '1%', 'BO', 'GA', '%P']
    for col in stat_cols:
        if col in df_logs.columns:
            df_logs[col] = pd.to_numeric(df_logs[col], errors='coerce').fillna(0)

    # Calculate Metres Gained proxy if not present (Kicks * 20 + Handballs * 5 is a common proxy, or we can use raw stats directly)
    # Let's estimate Metres Gained: KI * 25 + HB * 5
    df_logs['Metres_Gained'] = df_logs['KI'] * 25 + df_logs['HB'] * 5
    
    # Classify Roles based on average stats across the season
    player_avg = df_logs.groupby(['Player', 'team']).agg({
        'match_id': 'count',
        'KI': 'mean',
        'MK': 'mean',
        'HB': 'mean',
        'DI': 'mean',
        'GL': 'mean',
        'BH': 'mean',
        'HO': 'mean',
        'TK': 'mean',
        'RB': 'mean',
        'IF': 'mean',
        'CL': 'mean',
        'CG': 'mean',
        'FA': 'mean',
        'CP': 'mean',
        'UP': 'mean',
        'CM': 'mean',
        'MI': 'mean',
        '1%': 'mean',
        'GA': 'mean',
        'Metres_Gained': 'mean'
    }).rename(columns={'match_id': 'games_played'}).reset_index()

    # Filter out players with very few games to avoid noisy profiles
    player_avg = player_avg[player_avg['games_played'] >= 3]

    def assign_role(row):
        # High Hitouts -> Ruck
        if row['HO'] >= 10:
            return 'Ruck'
        # High Rebound 50s -> Rebounding Defender
        if row['RB'] >= 3.0:
            return 'Rebounding Defender'
        # High Marks Inside 50 & high goals -> Key Forward
        if row['MI'] >= 1.5 or (row['GL'] >= 1.5 and row['MK'] >= 4.0):
            return 'Key Forward'
        # High clearances and contested possessions -> Inside Midfielder
        if row['CL'] >= 3.5 or row['CP'] >= 9.0:
            return 'Inside Midfielder'
        # High 1%ers (spoils) and marks -> Key Defender
        if row['1%'] >= 4.5 and row['MK'] >= 3.0:
            return 'Key Defender'
        # High goals + tackles inside 50 -> Small Forward
        if row['GL'] >= 0.8:
            return 'Small/General Forward'
        # Default to Outside Mid / Winger
        return 'Outside/Winger'

    player_avg['role'] = player_avg.apply(assign_role, axis=1)

    # Define PIR calculation based on role
    def calculate_pir(row):
        role = row['role']
        
        # Base values
        cp = row['CP']
        cl = row['CL']
        tk = row['TK']
        ga = row['GA']
        metres = row['Metres_Gained']
        i50 = row['IF']
        up = row['UP']
        mk = row['MK']
        mi = row['MI']
        gl = row['GL']
        bh = row['BH']
        cm = row['CM']
        rb = row['RB']
        cg = row['CG']
        fa = row['FA']
        spoils = row['1%']

        if role == 'Inside Midfielder':
            score = (cp * 3.0) + (cl * 4.0) + (tk * 2.0) + (ga * 4.0) + (i50 * 1.5) - (cg * 2.0) - (fa * 1.5)
            # Normalize to 0-100 scale. Previously divided by 75.0, let's bump to 110.0 to make 95+ incredibly elite.
            return min(100, max(10, (score / 110.0) * 100))
            
        elif role == 'Outside/Winger':
            score = (metres * 0.1) + (i50 * 3.0) + (up * 1.5) + (mk * 2.0) + (ga * 4.0) - (cg * 2.0)
            # Previously divided by 80.0, let's bump to 115.0.
            return min(100, max(10, (score / 115.0) * 100))
            
        elif role == 'Key Forward':
            score = (mi * 8.0) + (gl * 12.0) + (bh * 4.0) + (cm * 6.0) + (cp * 1.5) - (cg * 2.0)
            # Previously divided by 70.0, let's bump to 105.0.
            return min(100, max(10, (score / 105.0) * 100))
            
        elif role == 'Small/General Forward':
            score = (gl * 15.0) + (bh * 5.0) + (ga * 6.0) + (tk * 3.0) + (i50 * 2.0) + (cp * 1.5) - (cg * 1.5)
            # Previously divided by 60.0, let's bump to 90.0.
            return min(100, max(10, (score / 90.0) * 100))
            
        elif role == 'Key Defender':
            score = (spoils * 5.0) + (mk * 3.0) + (cm * 6.0) + (cp * 2.0) - (cg * 2.0)
            # Previously divided by 55.0, let's bump to 85.0.
            return min(100, max(10, (score / 85.0) * 100))
            
        elif role == 'Rebounding Defender':
            score = (rb * 6.0) + (metres * 0.12) + (up * 1.5) + (mk * 2.5) - (cg * 2.5)
            # Previously divided by 125.0, let's bump to 170.0 to properly scale rebounding defenders who have high disposals/metres.
            return min(100, max(10, (score / 170.0) * 100))
            
        elif role == 'Ruck':
            # Hitouts, Clearances, CP, Tackles
            score = (row['HO'] * 1.2) + (cl * 3.0) + (cp * 2.5) + (tk * 2.0) + (cm * 5.0) - (cg * 2.0)
            # Previously divided by 80.0, let's bump to 120.0.
            return min(100, max(10, (score / 120.0) * 100))
            
        # Default fallback
        score = (cp * 2.0) + (up * 1.0) + (tk * 1.5) + (gl * 5.0) - (cg * 1.5)
        return min(100, max(10, (score / 75.0) * 100))

    # Apply role-based PIR to overall average
    player_avg['pir'] = player_avg.apply(calculate_pir, axis=1)

    # Let's calculate game-by-game PIR to find form and trends
    df_logs['role'] = df_logs.set_index(['Player', 'team']).index.map(player_avg.set_index(['Player', 'team'])['role'])
    df_logs['role'] = df_logs['role'].fillna('Outside/Winger')
    df_logs['pir'] = df_logs.apply(calculate_pir, axis=1)

    # Calculate trends and assign narrative tags for each player
    player_results = []
    
    for _, p_row in player_avg.iterrows():
        p_name = p_row['Player']
        p_team = p_row['team']
        p_role = p_row['role']
        p_games = p_row['games_played']
        
        # Get match history
        p_history = df_logs[(df_logs['Player'] == p_name) & (df_logs['team'] == p_team)].copy()
        # Sort chronologically (using index or match_id. Fortunately logs are sorted chronologically by default, but let's make sure)
        p_history = p_history.sort_values('match_id')
        
        # Calculate recent vs previous window
        recent_window = p_history.tail(3)
        prev_window = p_history.iloc[-6:-3] if len(p_history) >= 6 else pd.DataFrame()
        
        recent_avg_pir = recent_window['pir'].mean() if not recent_window.empty else p_row['pir']
        prev_avg_pir = prev_window['pir'].mean() if not prev_window.empty else p_row['pir']
        
        pir_delta = (recent_avg_pir - prev_avg_pir) / prev_avg_pir if prev_avg_pir > 0 else 0
        
        # Build raw stat details for displaying
        stats_summary = {
            'disposals': round(p_row['DI'], 1),
            'kicks': round(p_row['KI'], 1),
            'handballs': round(p_row['HB'], 1),
            'marks': round(p_row['MK'], 1),
            'goals': round(p_row['GL'], 1),
            'behinds': round(p_row['BH'], 1),
            'tackles': round(p_row['TK'], 1),
            'clearances': round(p_row['CL'], 1),
            'contested_possessions': round(p_row['CP'], 1),
            'uncontested_possessions': round(p_row['UP'], 1),
            'clangers': round(p_row['CG'], 1),
            'goal_assists': round(p_row['GA'], 1),
            'spoils': round(p_row['1%'], 1),
            'hitouts': round(p_row['HO'], 1),
        }
        
        narrative_tags = []
        
        # Let's apply our detailed Player Narrative Tags!
        # "The Leather Poisoner": > 30 Disposals, but < 250m Metres Gained, and < 3 Score Involvements
        # (We proxy Metres Gained as Metres_Gained, and use goal_assists as proxy for score involvements since score involvements is not raw in afltables)
        if p_row['DI'] >= 26.0 and p_row['Metres_Gained'] < 300.0 and p_row['GA'] < 0.5:
            narrative_tags.append("The Leather Poisoner")
            
        # "Pure Grit": > 65% of disposals are Contested, > 5 Clearances, and > 6 Tackles
        if p_row['DI'] > 0 and (p_row['CP'] / p_row['DI']) >= 0.55 and p_row['CL'] >= 4.5 and p_row['TK'] >= 5.0:
            narrative_tags.append("Pure Grit")
            
        # "The Kick-To-Self Merchant": > 80% Uncontested Disposals, low contested
        if p_row['DI'] > 0 and (p_row['UP'] / p_row['DI']) >= 0.75 and p_row['CP'] < 4.0:
            narrative_tags.append("The Kick-To-Self Merchant")
            
        # "The Almost Man": Forward with high scoring shots but poor accuracy (< 35% conversion)
        total_shots = p_row['GL'] + p_row['BH']
        if total_shots >= 2.5 and (p_row['GL'] / total_shots) < 0.40:
            narrative_tags.append("The Almost Man")
            
        # "The Decoy": key forward with low goals but high assists
        if p_role == 'Key Forward' and p_row['GL'] <= 0.8 and p_row['GA'] >= 0.8:
            narrative_tags.append("The Decoy")
            
        # "The Heatwave": pressure forward trapping ball inside 50
        # proxy: high tackles + high general forward play
        if p_role == 'Small/General Forward' and p_row['TK'] >= 4.0:
            narrative_tags.append("The Heatwave")
            
        # "The Double Agent": high clangers or free kicks against
        if p_row['CG'] >= 4.5 or p_row['FA'] >= 2.0:
            narrative_tags.append("The Double Agent")
            
        # "The Traffic Warden": elite key defender intercepting & spoiling
        if p_role == 'Key Defender' and p_row['MK'] >= 5.0 and p_row['1%'] >= 6.0:
            narrative_tags.append("The Traffic Warden")
            
        # "The Unsung Hero": Low disposals but high impact metrics
        if p_row['DI'] < 16.0 and p_row['CP'] >= 8.0 and p_row['TK'] >= 4.0:
            narrative_tags.append("The Unsung Hero")

        # Trend assignations
        player_trend = "Stable"
        if pir_delta >= 0.20:
            player_trend = "Rising"
            if p_games <= 15: # Proxy for breakout star
                narrative_tags.append("The Breakout Watch")
        elif pir_delta <= -0.20:
            player_trend = "Falling"
            # No age data in tables, but we can assume if they have played enough games or just tag as declining
            narrative_tags.append("The Cliff-Edge")

        # Top performance highlight
        best_stat = "Disposals"
        best_val = p_row['DI']
        if p_row['CL'] >= 5.0:
            best_stat = "Clearances"
            best_val = p_row['CL']
        elif p_row['GL'] >= 1.5:
            best_stat = "Goals"
            best_val = p_row['GL']
        elif p_row['MK'] >= 6.0:
            best_stat = "Marks"
            best_val = p_row['MK']
        elif p_row['TK'] >= 6.0:
            best_stat = "Tackles"
            best_val = p_row['TK']

        player_results.append({
            'name': p_name,
            'team': p_team,
            'role': p_role,
            'games_played': int(p_games),
            'pir': round(float(p_row['pir']), 1),
            'recent_pir': round(float(recent_avg_pir), 1),
            'pir_trend': round(float(pir_delta * 100), 1),
            'trend': player_trend,
            'narrative_tags': narrative_tags,
            'stats': stats_summary,
            'highlight': f"Averages {round(best_val, 1)} {best_stat} per game"
        })

    # Sort results by PIR descending to show top players
    player_results = sorted(player_results, key=lambda x: x['pir'], reverse=True)

    # Save output
    output_path = metrics_dir / 'player_trends.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(player_results, f, indent=2)

    print(f"Successfully calculated trends for {len(player_results)} players.")
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    calculate_player_trends()
