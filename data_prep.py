import pandas as pd
import numpy as np
import os

def prepare_match_data():
    print("Starting Phase 1: Match Data Preparation...")
    
    # Load dataset
    results_path = 'data/results.csv'
    if not os.path.exists(results_path):
        print(f"Error: {results_path} not found. Please place the dataset in the data/ folder.")
        return
        
    df = pd.read_csv(results_path)
    
    # Filter for FIFA World Cup
    df = df[df['tournament'].str.contains('FIFA World Cup', na=False, case=False)].copy()
    
    # Parse dates
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # Create outcome label (0: Away Win, 1: Draw, 2: Home Win)
    conditions = [
        (df['home_score'] > df['away_score']),
        (df['home_score'] == df['away_score']),
        (df['home_score'] < df['away_score'])
    ]
    choices = [2, 1, 0]
    df['outcome'] = np.select(conditions, choices, default=1)
    
    # Initialize rolling feature columns
    features = ['home_win_rate', 'away_win_rate', 
                'home_avg_goals_scored', 'home_avg_goals_conceded',
                'away_avg_goals_scored', 'away_avg_goals_conceded',
                'head_to_head_home_win_rate']
    
    for feat in features:
        df[feat] = np.nan
        
    # Helper to calculate team stats from last N matches
    def get_last_n_stats(team, current_date, n=10):
        # All historical matches for the team before current_date
        past_matches = df[(df['date'] < current_date) & 
                          ((df['home_team'] == team) | (df['away_team'] == team))]
        past_matches = past_matches.sort_values('date', ascending=False).head(n)
        
        if len(past_matches) == 0:
            return None
        
        wins = 0
        goals_scored = 0
        goals_conceded = 0
        
        for _, match in past_matches.iterrows():
            if match['home_team'] == team:
                if match['home_score'] > match['away_score']: wins += 1
                goals_scored += match['home_score']
                goals_conceded += match['away_score']
            else:
                if match['away_score'] > match['home_score']: wins += 1
                goals_scored += match['away_score']
                goals_conceded += match['home_score']
                
        return {
            'win_rate': wins / len(past_matches),
            'avg_goals_scored': goals_scored / len(past_matches),
            'avg_goals_conceded': goals_conceded / len(past_matches),
            'history_count': len(past_matches)
        }
        
    def get_h2h_stats(home_team, away_team, current_date):
        past_matches = df[(df['date'] < current_date) & 
                          (((df['home_team'] == home_team) & (df['away_team'] == away_team)) |
                           ((df['home_team'] == away_team) & (df['away_team'] == home_team)))]
        
        if len(past_matches) == 0:
            return None
            
        home_wins = 0
        for _, match in past_matches.iterrows():
            if match['home_team'] == home_team and match['home_score'] > match['away_score']:
                home_wins += 1
            elif match['away_team'] == home_team and match['away_score'] > match['home_score']:
                home_wins += 1
                
        return home_wins / len(past_matches)

    # Process each match
    for idx, row in df.iterrows():
        home_team = row['home_team']
        away_team = row['away_team']
        match_date = row['date']
        
        home_stats = get_last_n_stats(home_team, match_date)
        away_stats = get_last_n_stats(away_team, match_date)
        h2h_win_rate = get_h2h_stats(home_team, away_team, match_date)
        
        # Only populate if they have at least 3 historical matches
        if home_stats and home_stats['history_count'] >= 3:
            df.at[idx, 'home_win_rate'] = home_stats['win_rate']
            df.at[idx, 'home_avg_goals_scored'] = home_stats['avg_goals_scored']
            df.at[idx, 'home_avg_goals_conceded'] = home_stats['avg_goals_conceded']
            
        if away_stats and away_stats['history_count'] >= 3:
            df.at[idx, 'away_win_rate'] = away_stats['win_rate']
            df.at[idx, 'away_avg_goals_scored'] = away_stats['avg_goals_scored']
            df.at[idx, 'away_avg_goals_conceded'] = away_stats['avg_goals_conceded']
            
        if h2h_win_rate is not None:
            df.at[idx, 'head_to_head_home_win_rate'] = h2h_win_rate
            
    # Fill missing values with global averages (calculated over entire dataset for simplicity/robustness)
    # Average win rate across all matches is roughly ~38-40% per team, roughly 33% draw.
    # We use column means where available
    for feat in features:
        df[feat] = df[feat].fillna(df[feat].mean())
        # If mean is NaN (e.g., very early matches), fill with generic defaults
        if pd.isna(df[feat].mean()):
            if 'win_rate' in feat:
                df[feat] = df[feat].fillna(0.33)
            else:
                df[feat] = df[feat].fillna(1.0)
                
    # Save features.csv
    features_df = df[['date', 'home_team', 'away_team', 'outcome'] + features]
    features_df.to_csv('features.csv', index=False)
    print("Phase 1 Complete: features.csv created successfully.")

if __name__ == "__main__":
    prepare_match_data()
