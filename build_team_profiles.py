"""
build_team_profiles.py — Build aggregate team profiles from master_players.csv.
Outputs: data/team_profiles.csv (one row per WC 2026 team)
"""
import pandas as pd
import numpy as np
import os

def build_profiles():
    print("Building team profiles...")
    
    master = pd.read_csv('data/master_players.csv')
    print(f"  Loaded {len(master)} players from {master['team'].nunique()} teams.")

    profiles = []
    for team, group in master.groupby('team'):
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
            'team_total_career_goals': group['total_goals'].sum() if 'total_goals' in group.columns else 0,
            'team_avg_market_value': group['market_value_in_eur'].mean() if 'market_value_in_eur' in group.columns else 0,
            'team_gk_rating': gk_players['overall'].mean() if len(gk_players) > 0 else group['overall'].mean(),
            'team_depth_score': group['overall'].std(),
        }
        profiles.append(profile)
    
    profiles_df = pd.DataFrame(profiles)
    os.makedirs('data', exist_ok=True)
    profiles_df.to_csv('data/team_profiles.csv', index=False)
    print(f"  Team profiles built for {len(profiles_df)} teams")
    print(f"\nTop 10 teams by avg overall:")
    print(profiles_df.nlargest(10, 'team_avg_overall')[['team', 'team_avg_overall', 'team_star_rating']].to_string(index=False))
    return profiles_df


if __name__ == '__main__':
    build_profiles()
