import json
import os
import pandas as pd
import numpy as np
from pathlib import Path
from pyAFL.players.models import Player

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
            m_id = m['Date'].replace('-', '').replace(':', '').replace(' ', '')
        except Exception:
            pass

    # Replace NaN with 0
    stat_cols = ['KI', 'MK', 'HB', 'DI', 'GL', 'BH', 'HO', 'TK', 'RB', 'IF', 'CL', 'CG', 'FF', 'FA', 'CP', 'UP', 'CM', 'MI', '1%', 'BO', 'GA', '%P']
    for col in stat_cols:
        if col in df_logs.columns:
            df_logs[col] = pd.to_numeric(df_logs[col], errors='coerce').fillna(0)

    # Calculate upgraded Metres Gained proxy with territorial multipliers
    df_logs['Metres_Gained'] = (df_logs['KI'] * 22) + (df_logs['HB'] * 4) + (df_logs['IF'] * 30) + (df_logs['RB'] * 35)
    
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
        # Strict hierarchy exclusive queue
        # 1. Ruck
        if row['HO'] >= 10:
            return 'Ruck'
        # 2. Key Defender
        if row['1%'] >= 4.5 and row['MK'] >= 3.0:
            return 'Key Defender'
        # 3. Key Forward
        if row['MI'] >= 1.5 or (row['GL'] >= 1.5 and row['MK'] >= 4.0):
            return 'Key Forward'
        # 4. Inside Midfielder
        if row['CL'] >= 3.5 or row['CP'] >= 9.0:
            return 'Inside Midfielder'
        # 5. Rebounding Defender
        if row['RB'] >= 3.0:
            return 'Rebounding Defender'
        # 6. Small/General Forward
        if row['GL'] >= 0.8:
            return 'Small/General Forward'
        # 7. Outside/Winger (Fallback)
        return 'Outside/Winger'

    player_avg['role'] = player_avg.apply(assign_role, axis=1)

    # Define PIR calculation based on role with Volume Protection scaling
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
        di = row['DI']

        # Select formula and baseline floor for volume protection
        if role == 'Inside Midfielder':
            score = (cp * 3.5) + (cl * 5.0) + (tk * 2.0) + (ga * 4.0) + (i50 * 1.5) - (cg * 1.5) - (fa * 1.5)
            pir = max(10, (score / 120.0) * 100)
            # Volume protection: if Disposals < 12, scale down
            if di < 12:
                pir = pir * (di / 12)
            return max(10, pir)
            
        elif role == 'Outside/Winger':
            score = (metres * 0.1) + (i50 * 3.0) + (up * 1.5) + (mk * 2.0) + (ga * 4.0) - (cg * 2.0)
            pir = max(10, (score / 115.0) * 100)
            # Volume protection: if Disposals < 12, scale down
            if di < 12:
                pir = pir * (di / 12)
            return max(10, pir)
            
        elif role == 'Key Forward':
            score = (mi * 8.0) + (gl * 12.0) + (bh * 4.0) + (cm * 6.0) + (cp * 1.5) - (cg * 2.0)
            pir = max(10, (score / 105.0) * 100)
            # Volume protection: if Disposals < 6, scale down
            if di < 6:
                pir = pir * (di / 6)
            return max(10, pir)
            
        elif role == 'Small/General Forward':
            score = (gl * 15.0) + (bh * 5.0) + (ga * 6.0) + (tk * 3.0) + (i50 * 2.0) + (cp * 1.5) - (cg * 1.5)
            pir = max(10, (score / 90.0) * 100)
            # Volume protection: if Disposals < 8, scale down
            if di < 8:
                pir = pir * (di / 8)
            return max(10, pir)
            
        elif role == 'Key Defender':
            score = (spoils * 5.0) + (mk * 1.5) + (cm * 6.0) + (cp * 2.0) - (cg * 2.0)
            pir = max(10, (score / 75.0) * 100)
            # Volume protection: if Disposals < 6, scale down
            if di < 6:
                pir = pir * (di / 6)
            return max(10, pir)
            
        elif role == 'Rebounding Defender':
            score = (rb * 6.0) + (metres * 0.1) + (up * 0.8) + (mk * 1.2) - (cg * 2.5)
            pir = max(10, (score / 140.0) * 100)
            # Volume protection: if Disposals < 10, scale down
            if di < 10:
                pir = pir * (di / 10)
            return max(10, pir)
            
        elif role == 'Ruck':
            score = (row['HO'] * 1.2) + (cl * 3.0) + (cp * 2.5) + (tk * 2.0) + (cm * 5.0) - (cg * 2.0)
            pir = max(10, (score / 120.0) * 100)
            # Volume protection: if Disposals < 6, scale down
            if di < 6:
                pir = pir * (di / 6)
            return max(10, pir)
            
        # Default fallback
        score = (cp * 2.0) + (up * 1.0) + (tk * 1.5) + (gl * 5.0) - (cg * 1.5)
        pir = max(10, (score / 75.0) * 100)
        if di < 8:
            pir = pir * (di / 8)
        return max(10, pir)

    # Apply role-based PIR to overall average
    player_avg['pir'] = player_avg.apply(calculate_pir, axis=1)

    # Let's calculate game-by-game PIR to find form and trends
    df_logs['role'] = df_logs.set_index(['Player', 'team']).index.map(player_avg.set_index(['Player', 'team'])['role'])
    df_logs['role'] = df_logs['role'].fillna('Outside/Winger')
    df_logs['pir'] = df_logs.apply(calculate_pir, axis=1)

    # Load player career games cache if exists to speed up calculations and avoid redundant lookups
    cache_path = raw_dir / 'player_career_games_cache.json'
    career_games_cache = {}
    if cache_path.exists():
        try:
            with open(cache_path, 'r') as f:
                career_games_cache = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load cache from {cache_path}: {e}")

    # Calculate trends and assign narrative tags for each player
    player_results = []
    
    for _, p_row in player_avg.iterrows():
        p_name = p_row['Player']
        p_team = p_row['team']
        p_role = p_row['role']
        p_games = p_row['games_played']
        
        # Get total historical matches directly via pyAFL Player stats
        if p_name in career_games_cache:
            total_career_games = career_games_cache[p_name]
        else:
            reformatted_name = ' '.join(reversed([part.strip() for part in p_name.split(',')])) if ',' in p_name else p_name
            try:
                p_obj = Player(reformatted_name)
                p_stats = p_obj.get_player_stats()
                df_totals = p_stats.season_stats_total
                totals_row = df_totals[df_totals['Year'] == 'Totals']
                if not totals_row.empty:
                    total_career_games = int(float(totals_row['GM'].values[0]))
                else:
                    total_career_games = p_games
            except Exception as e:
                # Fallback to current season games if lookup fails
                total_career_games = p_games
            
            career_games_cache[p_name] = total_career_games
        
        # Get match history
        p_history = df_logs[(df_logs['Player'] == p_name) & (df_logs['team'] == p_team)].copy()
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
        
        # Player Narrative Tags Trigger logic
        if p_row['DI'] >= 26.0 and p_row['Metres_Gained'] < 300.0 and p_row['GA'] < 0.5:
            narrative_tags.append("The Leather Poisoner")
            
        if p_row['DI'] > 0 and (p_row['CP'] / p_row['DI']) >= 0.55 and p_row['CL'] >= 4.5 and p_row['TK'] >= 5.0:
            narrative_tags.append("Pure Grit")
            
        if p_row['DI'] > 0 and (p_row['UP'] / p_row['DI']) >= 0.75 and p_row['CP'] < 4.0:
            narrative_tags.append("The Kick-To-Self Merchant")
            
        total_shots = p_row['GL'] + p_row['BH']
        if total_shots >= 2.5 and (p_row['GL'] / total_shots) < 0.40:
            narrative_tags.append("The Almost Man")
            
        if p_role == 'Key Forward' and p_row['GL'] <= 0.8 and p_row['GA'] >= 0.8:
            narrative_tags.append("The Decoy")
            
        if p_role == 'Small/General Forward' and p_row['TK'] >= 4.0:
            narrative_tags.append("The Heatwave")
            
        if p_row['CG'] >= 4.5 or p_row['FA'] >= 2.0:
            narrative_tags.append("The Double Agent")
            
        if p_role == 'Key Defender' and p_row['MK'] >= 5.0 and p_row['1%'] >= 6.0:
            narrative_tags.append("The Traffic Warden")
            
        if p_row['DI'] < 16.0 and p_row['CP'] >= 8.0 and p_row['TK'] >= 4.0:
            narrative_tags.append("The Unsung Hero")

        # Trend assignations
        player_trend = "Stable"
        if pir_delta >= 0.20:
            player_trend = "Rising"
            # Breakout Watch: young players with less than 2 full seasons (approx 40 games)
            if total_career_games <= 40:
                narrative_tags.append("The Breakout Watch")
        elif pir_delta <= -0.20:
            player_trend = "Falling"
            # Cliff-Edge: only for veterans/experienced players (>= 50 career games)
            if total_career_games >= 50:
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
            'career_games': int(total_career_games),
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

    # Save player career games cache
    try:
        with open(cache_path, 'w') as f:
            json.dump(career_games_cache, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save cache to {cache_path}: {e}")

    # Save output
    output_path = metrics_dir / 'player_trends.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(player_results, f, indent=2)

    print(f"Successfully calculated trends for {len(player_results)} players.")
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    calculate_player_trends()
