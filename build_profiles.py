"""
build_profiles.py — Build master player profile data for WC 2026 squads.
Merges WC squad data with FC25 ratings and Transfermarkt stats.
Uses UI Avatars API for player images (always works, no broken images).
Outputs: data/master_players.csv
"""
import pandas as pd
import numpy as np
import os
import sys
import urllib.parse

sys.stdout.reconfigure(encoding='utf-8')


def build_photo_url(player_name, team):
    """Build a reliable avatar URL using UI Avatars API."""
    encoded_name = urllib.parse.quote(player_name)
    return (
        f"https://ui-avatars.com/api/?name={encoded_name}"
        f"&background=0d1f3c&color=00e5ff&size=120&bold=true&rounded=true"
    )


def build_profiles():
    print("Building master player profiles...")

    # ── LOAD WC2026 SQUADS ──────────────────────────────────────────────────
    squads = pd.read_csv('data/wc2026_squads.csv')
    print(f"  Loaded {len(squads)} squad entries for {squads['team'].nunique()} teams.")

    # ── PART A: LOAD FC25 DATA ──────────────────────────────────────────────
    fc25 = pd.read_csv('data/male_players.csv')
    fc25_cols = [c for c in [
        'long_name', 'short_name', 'overall', 'pace', 'shooting', 'passing',
        'dribbling', 'defending', 'physic', 'nationality_name', 'club_position'
    ] if c in fc25.columns]
    fc25 = fc25[fc25_cols].copy()

    # ── PART B: MATCH PLAYERS ────────────────────────────────────────────────
    # Since our FC25 data is generated to match squads 1:1 by long_name,
    # we can do a direct merge
    fc25_stat_cols = ['overall', 'pace', 'shooting', 'passing', 'dribbling', 'defending', 'physic']
    fc25_stat_cols = [c for c in fc25_stat_cols if c in fc25.columns]

    # Direct merge on name
    merged = squads.merge(fc25[['long_name'] + fc25_stat_cols],
                          left_on='player_name', right_on='long_name', how='left')
    merged = merged.drop(columns=['long_name'], errors='ignore')

    fc25_matched = merged['overall'].notna().sum()
    print(f"  Matched {fc25_matched}/{len(squads)} players with FC25 data.")

    # Cast to float to avoid int64/float type conflicts when filling NaN
    for col in fc25_stat_cols:
        merged[col] = merged[col].astype(float)

    # Fill missing FC25 stats with position-based medians
    for col in fc25_stat_cols:
        for pos in squads['position'].unique():
            pos_mask = (merged['position'] == pos) & merged[col].notna()
            median_val = merged.loc[pos_mask, col].median()
            if pd.notna(median_val):
                fill_mask = (merged['position'] == pos) & merged[col].isna()
                merged.loc[fill_mask, col] = median_val
        # If still NaN, fill with global median
        merged[col] = merged[col].fillna(merged[col].median())

    # ── PART C: TRANSFERMARKT STATS ──────────────────────────────────────────
    print("  Loading Transfermarkt appearances...")
    try:
        from rapidfuzz import process, fuzz
        USE_FUZZY = True
    except ImportError:
        USE_FUZZY = False
        print("  WARNING: rapidfuzz not installed. Using direct name matching only.")

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

    # Match squad to Transfermarkt
    tm_goals, tm_assists, tm_minutes, tm_games, tm_values = [], [], [], [], []

    for _, row in merged.iterrows():
        pname = row['player_name']

        # Direct match
        direct = tm[tm['name'] == pname]
        if not direct.empty:
            r = direct.iloc[0]
            tm_goals.append(r['total_goals'])
            tm_assists.append(r['total_assists'])
            tm_minutes.append(r['total_minutes'])
            tm_games.append(r['games_played'])
            tm_values.append(r.get('market_value_in_eur', np.nan))
            continue

        # Fuzzy match
        if USE_FUZZY:
            best = process.extractOne(pname, tm_names, scorer=fuzz.WRatio)
            if best and best[1] >= 78:
                idx = tm_names.index(best[0])
                r = tm.iloc[idx]
                tm_goals.append(r['total_goals'])
                tm_assists.append(r['total_assists'])
                tm_minutes.append(r['total_minutes'])
                tm_games.append(r['games_played'])
                tm_values.append(r.get('market_value_in_eur', np.nan))
                continue

        tm_goals.append(np.nan)
        tm_assists.append(np.nan)
        tm_minutes.append(np.nan)
        tm_games.append(np.nan)
        tm_values.append(np.nan)

    merged['total_goals'] = tm_goals
    merged['total_assists'] = tm_assists
    merged['total_minutes'] = tm_minutes
    merged['games_played'] = tm_games
    merged['market_value_in_eur'] = tm_values

    tm_matched = sum(1 for v in tm_values if not pd.isna(v))
    print(f"  Matched {tm_matched}/{len(merged)} players with Transfermarkt data.")

    # ── PART D: PHOTO URLS ──────────────────────────────────────────────────
    merged['photo_url'] = merged.apply(
        lambda r: build_photo_url(r['player_name'], r['team']), axis=1
    )
    merged['preferred_foot'] = 'Right'

    # ── PART E: SAVE OUTPUT ─────────────────────────────────────────────────
    output_cols = [
        'team', 'player_name', 'position', 'caps', 'club',
        'overall', 'pace', 'shooting', 'passing',
        'dribbling', 'defending', 'physic', 'preferred_foot',
        'total_goals', 'total_assists', 'total_minutes',
        'market_value_in_eur', 'photo_url'
    ]
    output_cols = [c for c in output_cols if c in merged.columns]
    master = merged[output_cols].copy()

    os.makedirs('data', exist_ok=True)
    master.to_csv('data/master_players.csv', index=False)

    print(f"\n{'='*50}")
    print(f"Total WC players: {len(master)}")
    print(f"Matched with FC25: {fc25_matched}")
    print(f"Matched with Transfermarkt: {tm_matched}")
    print(f"All players have avatar URLs: {master['photo_url'].notna().all()}")
    print(f"Saved: data/master_players.csv")
    return master


if __name__ == '__main__':
    build_profiles()
