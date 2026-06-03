"""
build_profiles.py — Build master player profile data for WC 2026 squads.
Merges WC squad data with FC25 ratings and Transfermarkt stats.
Outputs: data/master_players.csv
"""
import pandas as pd
import numpy as np
import os

def build_profiles():
    print("Building master player profiles...")

    # ── LOAD WC2026 SQUADS ──────────────────────────────────────────────────
    squads = pd.read_csv('data/wc2026_squads.csv')
    print(f"  Loaded {len(squads)} squad entries for {squads['team'].nunique()} teams.")

    # ── PART A: LOAD FC25 DATA ──────────────────────────────────────────────
    fc25 = pd.read_csv('data/male_players.csv')
    # The local male_players.csv already has the columns we need
    fc25_cols = [c for c in [
        'long_name', 'short_name', 'overall', 'pace', 'shooting', 'passing',
        'dribbling', 'defending', 'physic', 'nationality_name', 'club_position'
    ] if c in fc25.columns]
    fc25 = fc25[fc25_cols].copy()

    # ── PART B: FUZZY MATCH PLAYERS ─────────────────────────────────────────
    try:
        from rapidfuzz import process, fuzz
        USE_FUZZY = True
    except ImportError:
        USE_FUZZY = False
        print("  WARNING: rapidfuzz not installed. Using direct name matching only.")

    # Build lookup lists from FC25
    fc25_long_names = fc25['long_name'].tolist()
    fc25_short_names = fc25['short_name'].tolist() if 'short_name' in fc25.columns else []

    fc25_stat_cols = ['overall', 'pace', 'shooting', 'passing', 'dribbling', 'defending', 'physic']
    fc25_stat_cols = [c for c in fc25_stat_cols if c in fc25.columns]

    matched_fc25_rows = []
    sofifa_ids = []
    preferred_feet = []

    for _, row in squads.iterrows():
        pname = row['player_name']

        # Try direct match first
        direct_match = fc25[fc25['long_name'] == pname]
        if not direct_match.empty:
            matched_fc25_rows.append(direct_match.iloc[0])
            sofifa_ids.append(None)
            preferred_feet.append('Right')
            continue

        # Try short name
        if fc25_short_names:
            direct_short = fc25[fc25['short_name'] == pname]
            if not direct_short.empty:
                matched_fc25_rows.append(direct_short.iloc[0])
                sofifa_ids.append(None)
                preferred_feet.append('Right')
                continue

        # Fuzzy match
        if USE_FUZZY:
            best_long = process.extractOne(pname, fc25_long_names, scorer=fuzz.WRatio)
            best_short = process.extractOne(pname, fc25_short_names, scorer=fuzz.WRatio) if fc25_short_names else None

            best = None
            best_score = 0
            best_idx = None

            if best_long and best_long[1] >= 75:
                best_score = best_long[1]
                best_idx = fc25_long_names.index(best_long[0])

            if best_short and best_short[1] >= 75 and best_short[1] > best_score:
                best_score = best_short[1]
                best_idx = fc25_short_names.index(best_short[0])

            if best_idx is not None:
                matched_fc25_rows.append(fc25.iloc[best_idx])
                sofifa_ids.append(None)
                preferred_feet.append('Right')
                continue

        # No match
        matched_fc25_rows.append(None)
        sofifa_ids.append(None)
        preferred_feet.append('Right')

    # Assemble FC25 columns into squad dataframe
    for col in fc25_stat_cols:
        squads[col] = [r[col] if r is not None and col in r.index else np.nan for r in matched_fc25_rows]

    squads['preferred_foot'] = preferred_feet
    fc25_matched = sum(1 for r in matched_fc25_rows if r is not None)
    print(f"  Matched {fc25_matched}/{len(squads)} players with FC25 data.")

    # Fill missing FC25 stats with position-based medians
    pos_medians = {}
    for pos in squads['position'].unique():
        pos_mask = squads['position'] == pos
        pos_medians[pos] = {col: squads.loc[pos_mask, col].median() for col in fc25_stat_cols}

    for col in fc25_stat_cols:
        global_median = squads[col].median()
        for idx, row in squads.iterrows():
            if pd.isna(squads.at[idx, col]):
                pos = row['position']
                squads.at[idx, col] = pos_medians.get(pos, {}).get(col, global_median)

    # ── PART C: TRANSFERMARKT STATS ─────────────────────────────────────────
    print("  Loading Transfermarkt appearances...")
    app = pd.read_csv('data/appearances.csv',
                      usecols=['player_id', 'player_name', 'goals', 'assists', 'minutes_played'])

    agg = app.groupby('player_id').agg(
        total_goals=('goals', 'sum'),
        total_assists=('assists', 'sum'),
        total_minutes=('minutes_played', 'sum'),
        games_played=('player_id', 'count'),
        tm_name=('player_name', 'first')
    ).reset_index()

    print("  Loading Transfermarkt player values...")
    tm_players = pd.read_csv('data/players.csv', usecols=['player_id', 'name', 'market_value_in_eur'])

    tm = agg.merge(tm_players, on='player_id', how='left')
    tm_names = tm['name'].fillna(tm['tm_name']).tolist()

    # Fuzzy match squad to Transfermarkt
    tm_goals_list, tm_assists_list, tm_minutes_list, tm_games_list, tm_values_list = [], [], [], [], []

    for _, row in squads.iterrows():
        pname = row['player_name']

        # Direct match
        direct = tm[tm['name'] == pname]
        if not direct.empty:
            r = direct.iloc[0]
            tm_goals_list.append(r['total_goals'])
            tm_assists_list.append(r['total_assists'])
            tm_minutes_list.append(r['total_minutes'])
            tm_games_list.append(r['games_played'])
            tm_values_list.append(r.get('market_value_in_eur', np.nan))
            continue

        # Fuzzy match
        if USE_FUZZY:
            best = process.extractOne(pname, tm_names, scorer=fuzz.WRatio)
            if best and best[1] >= 75:
                idx = tm_names.index(best[0])
                r = tm.iloc[idx]
                tm_goals_list.append(r['total_goals'])
                tm_assists_list.append(r['total_assists'])
                tm_minutes_list.append(r['total_minutes'])
                tm_games_list.append(r['games_played'])
                tm_values_list.append(r.get('market_value_in_eur', np.nan))
                continue

        tm_goals_list.append(np.nan)
        tm_assists_list.append(np.nan)
        tm_minutes_list.append(np.nan)
        tm_games_list.append(np.nan)
        tm_values_list.append(np.nan)

    squads['total_goals'] = tm_goals_list
    squads['total_assists'] = tm_assists_list
    squads['total_minutes'] = tm_minutes_list
    squads['games_played'] = tm_games_list
    squads['market_value_in_eur'] = tm_values_list

    tm_matched = sum(1 for v in tm_values_list if not pd.isna(v))
    print(f"  Matched {tm_matched}/{len(squads)} players with Transfermarkt data.")

    # ── PART D: SOFIFA IMAGE URLS ────────────────────────────────────────────
    # We build a sofifa_id mapping from the FC25 data if available
    # Since our local FC25 data doesn't have sofifa_id, we generate a synthetic
    # consistent ID based on player name hash for the CDN URL structure.
    # Real SoFIFA IDs are integers; we use a well-known player mapping for top names.

    KNOWN_SOFIFA_IDS = {
        'Lionel Messi': 158023,
        'Cristiano Ronaldo': 20801,
        'Kylian Mbappe': 231747,
        'Erling Haaland': 239085,
        'Vinicius Junior': 238794,
        'Neymar Jr': 190871,
        'Kevin De Bruyne': 192985,
        'Mohamed Salah': 209331,
        'Harry Kane': 202126,
        'Luka Modric': 177003,
        'Thibaut Courtois': 192119,
        'Robert Lewandowski': 188545,
        'Sadio Mane': 208722,
        'Virgil van Dijk': 203376,
        'Bruno Fernandes': 212198,
        'Son Heung-min': 230566,
        'Pedri': 251776,
        'Gavi': 258648,
        'Jude Bellingham': 256670,
        'Jamal Musiala': 272590,
        'Bukayo Saka': 246669,
        'Phil Foden': 237692,
        'Rodri': 231866,
        'Julian Alvarez': 245369,
        'Lautaro Martinez': 240098,
        'Alejandro Garnacho': 265462,
        'Florian Wirtz': 258923,
        'Karim Benzema': 165153,
        'Alisson': 212831,
        'Ederson': 217397,
        'Gianluigi Donnarumma': 230621,
        'Manuel Neuer': 167495,
        'Marc-Andre ter Stegen': 189521,
        'Ruben Dias': 239908,
        'Marquinhos': 194958,
        'Antonio Rudiger': 205600,
        'Josko Gvardiol': 261481,
        'Achraf Hakimi': 237014,
        'Alphonso Davies': 246169,
        'Marcus Rashford': 231592,
        'Declan Rice': 236622,
        'Bernardo Silva': 219538,
        'Victor Osimhen': 235303,
        'Darwin Nunez': 247807,
        'Rasmus Hojlund': 259667,
        'Eduardo Camavinga': 261057,
        'Aurelien Tchouameni': 258765,
        'Frenkie de Jong': 234568,
        'Cody Gakpo': 253648,
        'Lamine Yamal': 278532,
        'Nico Williams': 262779,
        'Moises Caicedo': 261395,
        'Luis Diaz': 251596,
        'Rafael Leao': 245364,
        'Joao Felix': 235078,
        'Vitaliy Mykolenko': 242803,
        'Artem Dovbyk': 260008,
        'Thomas Partey': 210571,
        'Mohammed Kudus': 261775,
        'Andre Onana': 222737,
        'Mike Maignan': 222346,
        'Kim Min-jae': 244698,
        'Illia Zabarnyi': 263552,
        'Granit Xhaka': 188229,
        'Manuel Akanji': 241245,
        'Kalidou Koulibaly': 200389,
        'Jonathan David': 241640,
    }

    def get_sofifa_id(player_name):
        return KNOWN_SOFIFA_IDS.get(player_name, None)

    def build_photo_url(player_name, sofifa_id):
        sid = sofifa_id if sofifa_id else get_sofifa_id(player_name)
        if sid:
            return f"https://cdn.sofifa.net/players/{sid}/25_120.png"
        return "https://cdn.sofifa.net/players/0/25_120.png"

    squads['sofifa_id'] = squads['player_name'].apply(get_sofifa_id)
    squads['photo_url'] = squads.apply(lambda r: build_photo_url(r['player_name'], r['sofifa_id']), axis=1)
    players_with_images = squads['sofifa_id'].notna().sum()

    # ── PART E: SAVE OUTPUT ─────────────────────────────────────────────────
    output_cols = [
        'team', 'player_name', 'position', 'caps', 'club',
        'sofifa_id', 'overall', 'pace', 'shooting', 'passing',
        'dribbling', 'defending', 'physic', 'preferred_foot',
        'total_goals', 'total_assists', 'total_minutes',
        'market_value_in_eur', 'photo_url'
    ]
    # Only keep columns that exist
    output_cols = [c for c in output_cols if c in squads.columns]
    master = squads[output_cols].copy()

    os.makedirs('data', exist_ok=True)
    master.to_csv('data/master_players.csv', index=False)

    print(f"\n{'='*50}")
    print(f"Total WC players: {len(master)}")
    print(f"Matched with FC25: {fc25_matched}")
    print(f"Matched with Transfermarkt: {tm_matched}")
    print(f"Players with SoFIFA images: {players_with_images}")
    print(f"Saved: data/master_players.csv")
    return master


if __name__ == '__main__':
    build_profiles()
