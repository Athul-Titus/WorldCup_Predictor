import pandas as pd
import os

def prepare_player_data():
    print("Starting Phase 3: Player Data Pipeline...")
    
    app_path = 'data/appearances.csv'
    players_path = 'data/players.csv'
    
    if not os.path.exists(app_path) or not os.path.exists(players_path):
        print("Error: appearances.csv or players.csv not found in data/ folder.")
        return
        
    appearances = pd.read_csv(app_path)
    players = pd.read_csv(players_path)
    
    # Aggregate per player
    # appearances.csv - player_id, game_id, goals, assists, minutes_played, yellow_cards, red_cards
    player_agg = appearances.groupby('player_id').agg(
        total_goals=('goals', 'sum'),
        total_assists=('assists', 'sum'),
        total_minutes_played=('minutes_played', 'sum'),
        yellow_cards=('yellow_cards', 'sum'),
        red_cards=('red_cards', 'sum'),
        games_played=('game_id', 'count')
    ).reset_index()
    
    # Filter players with >10 career appearances
    player_agg = player_agg[player_agg['games_played'] > 10]
    
    # Calculate derived stats
    player_agg['avg_goals_per_game'] = player_agg['total_goals'] / player_agg['games_played']
    player_agg['avg_assists_per_game'] = player_agg['total_assists'] / player_agg['games_played']
    player_agg['yellow_card_rate'] = player_agg['yellow_cards'] / player_agg['games_played']
    player_agg['red_card_rate'] = player_agg['red_cards'] / player_agg['games_played']
    
    # Merge with player demographics
    merged = pd.merge(player_agg, players[['player_id', 'name', 'position', 'market_value_in_eur', 'country_of_birth', 'date_of_birth']], on='player_id', how='left')
    
    # Drop rows with null position or market value
    merged = merged.dropna(subset=['position', 'market_value_in_eur'])
    
    # Save player_features.csv
    merged.to_csv('player_features.csv', index=False)
    print("Phase 3 Complete: player_features.csv created successfully.")

if __name__ == "__main__":
    prepare_player_data()
