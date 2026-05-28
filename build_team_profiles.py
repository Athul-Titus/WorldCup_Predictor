"""
build_team_profiles.py — Build aggregate team profiles from FC25 ratings and squad data.
Outputs: team_profiles.csv (one row per WC 2026 team)
"""
import pandas as pd
import numpy as np
import os

def build_profiles():
    print("Building team profiles...")
    
    squads = pd.read_csv('data/wc2026_squads.csv')
    fc25 = pd.read_csv('data/male_players.csv')
    
    # Join squads with FC25 ratings on player name
    # Since names already match (generated from same source), direct merge works
    merged = squads.merge(fc25, left_on='player_name', right_on='long_name', how='left')
    
    # Fill any missing ratings with position-based defaults
    for col in ['overall', 'pace', 'shooting', 'passing', 'defending', 'physic', 'dribbling']:
        merged[col] = merged[col].fillna(merged[col].median())
    
    profiles = []
    for team, group in merged.groupby('team'):
        gk_players = group[group['position'] == 'GK']
        
        profile = {
            'team': team,
            'squad_size': len(group),
            'team_avg_overall': group['overall'].mean(),
            'team_avg_shooting': group['shooting'].mean(),
            'team_avg_passing': group['passing'].mean(),
            'team_avg_defending': group['defending'].mean(),
            'team_avg_pace': group['pace'].mean(),
            'team_avg_dribbling': group['dribbling'].mean(),
            'team_avg_physic': group['physic'].mean(),
            'team_star_rating': group['overall'].max(),
            'team_gk_rating': gk_players['overall'].mean() if len(gk_players) > 0 else group['overall'].mean(),
            'team_depth_score': group['overall'].std(),  # lower = more balanced squad
        }
        profiles.append(profile)
    
    profiles_df = pd.DataFrame(profiles)
    profiles_df.to_csv('team_profiles.csv', index=False)
    print(f"Saved team_profiles.csv with {len(profiles_df)} teams")
    print(f"\nTop 10 teams by avg overall:")
    print(profiles_df.nlargest(10, 'team_avg_overall')[['team', 'team_avg_overall', 'team_star_rating']].to_string(index=False))
    return profiles_df


if __name__ == '__main__':
    build_profiles()
