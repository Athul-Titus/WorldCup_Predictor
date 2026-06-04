import pandas as pd, os, numpy as np

files = {
    'data/results.csv': 'Match results',
    'data/wc2026_squads.csv': 'WC2026 squads',
    'data/master_players.csv': 'Master players',
    'data/team_profiles.csv': 'Team profiles',
    'features.csv': 'ML features',
    'player_clustered.csv': 'Clustered players',
    'model.pkl': 'ML model',
    'model_accuracy.txt': 'Model accuracy',
    'style.css': 'CSS file',
    'player_cards.py': 'Player cards module',
}
print('=== DATA FILE AUDIT ===')
for f, desc in files.items():
    exists = os.path.exists(f)
    if exists:
        size = os.path.getsize(f)
        print(f'  [OK] {desc}: {f} ({size:,} bytes)')
    else:
        print(f'  [MISSING] {desc}: {f}')

print()
print('=== MASTER_PLAYERS SCHEMA ===')
mp = pd.read_csv('data/master_players.csv')
teams = sorted(mp['team'].unique().tolist())
print(f'  Rows: {len(mp)}')
print(f'  Teams: {mp["team"].nunique()}')
print(f'  Columns: {list(mp.columns)}')
print(f'  NaN photo_url: {mp["photo_url"].isna().sum()}')
print(f'  NaN overall: {mp["overall"].isna().sum()}')
print(f'  NaN market_value: {mp["market_value_in_eur"].isna().sum()}')
print(f'  Teams list: {teams}')

print()
print('=== PLAYER_CLUSTERED SCHEMA ===')
pc = pd.read_csv('player_clustered.csv')
print(f'  Rows: {len(pc)}')
print(f'  Columns (first 12): {list(pc.columns[:12])}')
if 'cluster_label' in pc.columns:
    print(f'  Cluster counts: {pc["cluster_label"].value_counts().to_dict()}')

print()
print('=== MODEL ACCURACY ===')
with open('model_accuracy.txt') as f:
    print(f'  {f.read().strip()}')
