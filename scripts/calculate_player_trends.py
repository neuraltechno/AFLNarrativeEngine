import json
import os
import pandas as pd
import numpy as np
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from utils.fetch_raw_data import get_data

def calculate_player_trends():
    # Use absolute paths relative to workspace root
    base_dir = Path(__file__).parent.parent.absolute()
    metrics_dir = base_dir / 'data' / 'metrics'
    
    # Load player logs from Fryzigg data
    df_logs = get_data() # Assuming this returns a dataframe with logs
    
    # Rename columns to match new schema
    rename_map = {
        'KI': 'kicks',
        'MK': 'marks',
        'HB': 'handballs',
        'DI': 'disposals',
        'GL': 'goals',
        'BH': 'behinds',
        'HO': 'hitouts',
        'TK': 'tackles',
        'RB': 'rebounds',
        'IF': 'inside_50s',
        'CL': 'clearances',
        'CG': 'clangers',
        'FF': 'frees_for',
        'FA': 'frees_against',
        'CP': 'contested_possessions',
        'UP': 'uncontested_possessions',
        'CM': 'contested_marks',
        'MI': 'marks_inside_50',
        '1%': 'one_percenters',
        'BO': 'bounces',
        'GA': 'goal_assists',
        '%P': 'percentage_played',
        'Player': 'player_name'
    }
    df_logs = df_logs.rename(columns=rename_map)
    
    # Assuming Fryzigg data needs filtering for 2026 if necessary, 
    # but for now, we use the whole dataset as a proxy
    if 'year' in df_logs.columns:
        df_logs = df_logs[df_logs['year'] == 2026]

    # Replace NaN with 0
    stat_cols = ['kicks', 'marks', 'handballs', 'disposals', 'goals', 'behinds', 'hitouts', 'tackles', 'rebounds', 'inside_50s', 'clearances', 'clangers', 'frees_for', 'frees_against', 'contested_possessions', 'uncontested_possessions', 'contested_marks', 'marks_inside_50', 'one_percenters', 'bounces', 'goal_assists', 'percentage_played']
    for col in stat_cols:
        if col in df_logs.columns:
            df_logs[col] = pd.to_numeric(df_logs[col], errors='coerce').fillna(0)


    # Rename columns to standardized names for the rest of the script
    rename_map = {
        'Player': 'player_name',
        'KI': 'kicks',
        'MK': 'marks',
        'HB': 'handballs',
        'DI': 'disposals',
        'GL': 'goals',
        'BH': 'behinds',
        'HO': 'hitouts',
        'TK': 'tackles',
        'RB': 'rebounds',
        'IF': 'inside_50s',
        'CL': 'clearances',
        'CG': 'clangers',
        'FA': 'frees_against',
        'CP': 'contested_possessions',
        'UP': 'uncontested_possessions',
        'CM': 'contested_marks',
        'MI': 'marks_inside_50',
        '1%': 'one_percenters',
        'GA': 'goal_assists'
    }
    df_logs = df_logs.rename(columns=rename_map)

    # Calculate upgraded Metres Gained proxy with territorial multipliers
    df_logs['Metres_Gained'] = (df_logs['kicks'] * 22) + (df_logs['handballs'] * 4) + (df_logs['inside_50s'] * 30) + (df_logs['rebounds'] * 35)

    
    # Classify Roles based on average stats across the season
    # The stats files contain rows like '30 players used', which should be filtered out
    df_logs = df_logs[~df_logs['player_name'].str.contains('players used', case=False)]
    
    # Ensure GM is numeric for counting games
    df_logs['GM'] = pd.to_numeric(df_logs['GM'], errors='coerce')
    
    player_avg = df_logs.groupby(['player_name', 'team']).agg({
        'GM': 'max',
        'kicks': 'mean',
        'marks': 'mean',
        'handballs': 'mean',
        'disposals': 'mean',
        'goals': 'mean',
        'behinds': 'mean',
        'hitouts': 'mean',
        'tackles': 'mean',
        'rebounds': 'mean',
        'inside_50s': 'mean',
        'clearances': 'mean',
        'clangers': 'mean',
        'frees_against': 'mean',
        'contested_possessions': 'mean',
        'uncontested_possessions': 'mean',
        'contested_marks': 'mean',
        'marks_inside_50': 'mean',
        'one_percenters': 'mean',
        'goal_assists': 'mean',
        'Metres_Gained': 'mean'
    }).rename(columns={'GM': 'games_played'}).reset_index()


    # Filter out players with very few games to avoid noisy profiles
    print(f"DEBUG: player_avg: {player_avg.head()}")
    player_avg = player_avg[player_avg['games_played'] >= 3]
    print(f"DEBUG: players after filtering: {len(player_avg)}")

    def assign_role(row):
        # Strict hierarchy exclusive queue
        # 1. Ruck
        if row['hitouts'] >= 10:
            return 'Ruck'
        # 2. Key Defender
        if row['one_percenters'] >= 4.5 and row['marks'] >= 3.0:
            return 'Key Defender'
        # 3. Key Forward
        if row['marks_inside_50'] >= 1.5 or (row['goals'] >= 1.5 and row['marks'] >= 4.0):
            return 'Key Forward'
        # 4. Inside Midfielder
        if row['clearances'] >= 3.5 or row['contested_possessions'] >= 9.0:
            return 'Inside Midfielder'
        # 5. Rebounding Defender
        if row['rebounds'] >= 3.0:
            return 'Rebounding Defender'
        # 6. Small/General Forward
        if row['goals'] >= 0.8:
            return 'Small/General Forward'
        # 7. Outside/Winger (Fallback)
        return 'Outside/Winger'


    player_avg['role'] = player_avg.apply(assign_role, axis=1)

    # Define PIR calculation based on role with Volume Protection scaling
    def calculate_pir(row):
        role = row['role']
        
        # Base values from row
        cp = row['contested_possessions']
        cl = row['clearances']
        tk = row['tackles']
        ga = row['goal_assists']
        metres = row['Metres_Gained']
        i50 = row['inside_50s']
        up = row['uncontested_possessions']
        mk = row['marks']
        mi = row['marks_inside_50']
        gl = row['goals']
        bh = row['behinds']
        cm = row['contested_marks']
        rb = row['rebounds']
        cg = row['clangers']
        fa = row['frees_against']
        spoils = row['one_percenters']
        di = row['disposals']

        # Select formula and baseline floor for volume protection
        if role == 'Inside Midfielder':
            score = (cp * 3.5) + (cl * 5.0) + (tk * 2.0) + (ga * 4.0) + (i50 * 1.5) - (cg * 1.5) - (fa * 1.5)
            pir = max(10, (score / 120.0) * 100)
            if di < 12:
                pir = pir * (di / 12)
            return max(10, pir)
            
        elif role == 'Outside/Winger':
            score = (metres * 0.1) + (i50 * 3.0) + (up * 1.5) + (mk * 2.0) + (ga * 4.0) - (cg * 2.0)
            pir = max(10, (score / 115.0) * 100)
            if di < 12:
                pir = pir * (di / 12)
            return max(10, pir)
            
        elif role == 'Key Forward':
            score = (mi * 8.0) + (gl * 12.0) + (bh * 4.0) + (cm * 6.0) + (cp * 1.5) - (cg * 2.0)
            pir = max(10, (score / 105.0) * 100)
            if di < 6:
                pir = pir * (di / 6)
            return max(10, pir)
            
        elif role == 'Small/General Forward':
            score = (gl * 15.0) + (bh * 5.0) + (ga * 6.0) + (tk * 3.0) + (i50 * 2.0) + (cp * 1.5) - (cg * 1.5)
            pir = max(10, (score / 90.0) * 100)
            if di < 8:
                pir = pir * (di / 8)
            return max(10, pir)
            
        elif role == 'Key Defender':
            score = (spoils * 5.0) + (mk * 1.5) + (cm * 6.0) + (cp * 2.0) - (cg * 2.0)
            pir = max(10, (score / 75.0) * 100)
            if di < 6:
                pir = pir * (di / 6)
            return max(10, pir)
            
        elif role == 'Rebounding Defender':
            score = (rb * 6.0) + (metres * 0.1) + (up * 0.8) + (mk * 1.2) - (cg * 2.5)
            pir = max(10, (score / 140.0) * 100)
            if di < 10:
                pir = pir * (di / 10)
            return max(10, pir)
            
        elif role == 'Ruck':
            score = (row['hitouts'] * 1.2) + (cl * 3.0) + (cp * 2.5) + (tk * 2.0) + (cm * 5.0) - (cg * 2.0)
            pir = max(10, (score / 120.0) * 100)
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
    df_logs['role'] = df_logs.set_index(['player_name', 'team']).index.map(player_avg.set_index(['player_name', 'team'])['role'])
    df_logs['role'] = df_logs['role'].fillna('Outside/Winger')
    df_logs['pir'] = df_logs.apply(calculate_pir, axis=1)

    # Load player career games cache if exists
    # Need to get raw_dir
    raw_dir = Path(__file__).parent.parent.absolute() / 'data' / 'raw'
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
        p_name = p_row['player_name']
        p_team = p_row['team']
        p_role = p_row['role']
        p_games = p_row['games_played']
        
        # Get total historical matches (using current games as proxy)
        if p_name in career_games_cache:
            total_career_games = career_games_cache[p_name]
        else:
            total_career_games = p_games
            career_games_cache[p_name] = total_career_games
        
        # Get match history
        p_history = df_logs[(df_logs['player_name'] == p_name) & (df_logs['team'] == p_team)].copy()
        p_history = p_history.sort_values('GM') # Assuming GM is match order
        
        # Calculate recent vs previous window
        recent_window = p_history.tail(3)
        prev_window = p_history.iloc[-6:-3] if len(p_history) >= 6 else pd.DataFrame()
        
        recent_avg_pir = recent_window['pir'].mean() if not recent_window.empty else p_row['pir']
        prev_avg_pir = prev_window['pir'].mean() if not prev_window.empty else p_row['pir']
        
        pir_delta = (recent_avg_pir - prev_avg_pir) / prev_avg_pir if prev_avg_pir > 0 else 0
        
        # Build raw stat details for displaying
        stats_summary = {
            'disposals': round(p_row['disposals'], 1),
            'kicks': round(p_row['kicks'], 1),
            'handballs': round(p_row['handballs'], 1),
            'marks': round(p_row['marks'], 1),
            'goals': round(p_row['goals'], 1),
            'behinds': round(p_row['behinds'], 1),
            'tackles': round(p_row['tackles'], 1),
            'clearances': round(p_row['clearances'], 1),
            'contested_possessions': round(p_row['contested_possessions'], 1),
            'uncontested_possessions': round(p_row['uncontested_possessions'], 1),
            'clangers': round(p_row['clangers'], 1),
            'goal_assists': round(p_row['goal_assists'], 1),
            'spoils': round(p_row['one_percenters'], 1),
            'hitouts': round(p_row['hitouts'], 1),
        }

        
        narrative_tags = []
        
        # Player Narrative Tags Trigger logic
        if p_row['disposals'] >= 26.0 and p_row['Metres_Gained'] < 300.0 and p_row['goal_assists'] < 0.5:
            narrative_tags.append("The Leather Poisoner")
            
        if p_row['disposals'] > 0 and (p_row['contested_possessions'] / p_row['disposals']) >= 0.55 and p_row['clearances'] >= 4.5 and p_row['tackles'] >= 5.0:
            narrative_tags.append("Pure Grit")
            
        if p_row['disposals'] > 0 and (p_row['uncontested_possessions'] / p_row['disposals']) >= 0.75 and p_row['contested_possessions'] < 4.0:
            narrative_tags.append("The Kick-To-Self Merchant")
            
        total_shots = p_row['goals'] + p_row['behinds']
        if total_shots >= 2.5 and (p_row['goals'] / total_shots) < 0.40:
            narrative_tags.append("The Almost Man")
            
        if p_role == 'Key Forward' and p_row['goals'] <= 0.8 and p_row['goal_assists'] >= 0.8:
            narrative_tags.append("The Decoy")
            
        if p_role == 'Small/General Forward' and p_row['tackles'] >= 4.0:
            narrative_tags.append("The Heatwave")
            
        if p_row['clangers'] >= 4.5 or p_row['frees_against'] >= 2.0:
            narrative_tags.append("The Double Agent")
            
        if p_role == 'Key Defender' and p_row['marks'] >= 5.0 and p_row['one_percenters'] >= 6.0:
            narrative_tags.append("The Traffic Warden")
            
        if p_row['disposals'] < 16.0 and p_row['contested_possessions'] >= 8.0 and p_row['tackles'] >= 4.0:
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
        best_val = p_row['disposals']
        if p_row['clearances'] >= 5.0:
            best_stat = "Clearances"
            best_val = p_row['clearances']
        elif p_row['goals'] >= 1.5:
            best_stat = "Goals"
            best_val = p_row['goals']
        elif p_row['marks'] >= 6.0:
            best_stat = "Marks"
            best_val = p_row['marks']
        elif p_row['tackles'] >= 6.0:
            best_stat = "Tackles"
            best_val = p_row['tackles']

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
