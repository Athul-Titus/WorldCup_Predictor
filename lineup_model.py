"""
lineup_model.py — Train lineup-aware prediction models.
1. XGBClassifier for match outcome (Win/Draw/Loss)
2. GradientBoostingRegressor for total goals
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, mean_absolute_error
from xgboost import XGBClassifier
from sklearn.ensemble import GradientBoostingRegressor
import joblib
import os


def build_training_data():
    """Build training data by combining historical match results with team profiles."""
    print("Building training data...")
    
    # Load historical match data
    results = pd.read_csv('data/results.csv')
    results['date'] = pd.to_datetime(results['date'])
    
    # Filter to FIFA World Cup matches (actual tournaments, not qualifiers)
    wc = results[results['tournament'] == 'FIFA World Cup'].copy()
    wc = wc[wc['date'].dt.year >= 2000]  # Modern era
    
    # Load team profiles
    profiles = pd.read_csv('team_profiles.csv')
    
    # Load the features.csv for historical win rates
    features = pd.read_csv('features.csv')
    
    # Create outcome
    conditions = [
        (wc['home_score'] > wc['away_score']),
        (wc['home_score'] == wc['away_score']),
        (wc['home_score'] < wc['away_score'])
    ]
    wc['outcome'] = np.select(conditions, [2, 1, 0], default=1)
    wc['total_goals'] = wc['home_score'] + wc['away_score']
    
    # Merge with team profiles
    wc = wc.merge(profiles, left_on='home_team', right_on='team', how='left', suffixes=('', '_home'))
    wc = wc.rename(columns={
        'team_avg_overall': 'home_avg_overall',
        'team_avg_shooting': 'home_avg_shooting',
        'team_avg_passing': 'home_avg_passing',
        'team_avg_defending': 'home_avg_defending',
        'team_avg_pace': 'home_avg_pace',
        'team_star_rating': 'home_star_rating',
        'team_gk_rating': 'home_gk_rating',
    })
    wc = wc.drop(columns=['team', 'squad_size', 'team_avg_dribbling', 'team_avg_physic', 'team_depth_score'], errors='ignore')
    
    wc = wc.merge(profiles, left_on='away_team', right_on='team', how='left', suffixes=('', '_away'))
    wc = wc.rename(columns={
        'team_avg_overall': 'away_avg_overall',
        'team_avg_shooting': 'away_avg_shooting',
        'team_avg_passing': 'away_avg_passing',
        'team_avg_defending': 'away_avg_defending',
        'team_avg_pace': 'away_avg_pace',
        'team_star_rating': 'away_star_rating',
        'team_gk_rating': 'away_gk_rating',
    })
    wc = wc.drop(columns=['team', 'squad_size', 'team_avg_dribbling', 'team_avg_physic', 'team_depth_score'], errors='ignore')
    
    # Merge historical win rates from features.csv
    # Get the latest stats for each team
    for idx, row in wc.iterrows():
        home_feat = features[
            ((features['home_team'] == row['home_team']) | (features['away_team'] == row['home_team'])) &
            (features['date'] < str(row['date']))
        ].tail(1)
        
        away_feat = features[
            ((features['home_team'] == row['away_team']) | (features['away_team'] == row['away_team'])) &
            (features['date'] < str(row['date']))
        ].tail(1)
        
        if not home_feat.empty:
            if home_feat['home_team'].values[0] == row['home_team']:
                wc.at[idx, 'home_win_rate'] = home_feat['home_win_rate'].values[0]
            else:
                wc.at[idx, 'home_win_rate'] = home_feat['away_win_rate'].values[0]
        
        if not away_feat.empty:
            if away_feat['home_team'].values[0] == row['away_team']:
                wc.at[idx, 'away_win_rate'] = away_feat['home_win_rate'].values[0]
            else:
                wc.at[idx, 'away_win_rate'] = away_feat['away_win_rate'].values[0]
    
    # Fill missing values with reasonable defaults
    for col in ['home_avg_overall', 'away_avg_overall', 'home_avg_shooting', 'away_avg_shooting',
                'home_avg_passing', 'away_avg_passing', 'home_avg_defending', 'away_avg_defending',
                'home_avg_pace', 'away_avg_pace', 'home_star_rating', 'away_star_rating',
                'home_gk_rating', 'away_gk_rating']:
        wc[col] = wc[col].fillna(75)  # Generic average
    
    wc['home_win_rate'] = wc['home_win_rate'].fillna(0.33)
    wc['away_win_rate'] = wc['away_win_rate'].fillna(0.33)
    
    return wc


def train_models():
    """Train XGBClassifier and GradientBoostingRegressor."""
    wc = build_training_data()
    
    feature_cols = [
        'home_avg_overall', 'home_avg_shooting', 'home_avg_passing',
        'home_avg_defending', 'home_avg_pace', 'home_star_rating', 'home_gk_rating',
        'away_avg_overall', 'away_avg_shooting', 'away_avg_passing',
        'away_avg_defending', 'away_avg_pace', 'away_star_rating', 'away_gk_rating',
        'home_win_rate', 'away_win_rate',
    ]
    
    # Drop rows with NaN in features or targets
    wc_clean = wc[feature_cols + ['outcome', 'total_goals']].dropna()
    X = wc_clean[feature_cols].copy()
    y_outcome = wc_clean['outcome']
    y_goals = wc_clean['total_goals']
    
    print(f"\nTraining data size: {len(X)} matches")
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y_outcome, test_size=0.2, random_state=42)
    _, _, yg_train, yg_test = train_test_split(X, y_goals, test_size=0.2, random_state=42)
    
    # 1. Outcome classifier (XGBoost)
    print("\n--- Outcome Classifier (XGBoost) ---")
    xgb_model = XGBClassifier(
        n_estimators=300, max_depth=5, learning_rate=0.1,
        random_state=42, use_label_encoder=False, eval_metric='mlogloss'
    )
    xgb_model.fit(X_train, y_train)
    y_pred = xgb_model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {acc:.4f}")
    print(classification_report(y_test, y_pred, target_names=['Away Win', 'Draw', 'Home Win'], zero_division=0))
    
    # 2. Goals regressor
    print("--- Goals Regressor (GBR) ---")
    gbr_model = GradientBoostingRegressor(
        n_estimators=200, max_depth=4, learning_rate=0.1, random_state=42
    )
    gbr_model.fit(X_train, yg_train)
    yg_pred = gbr_model.predict(X_test)
    mae = mean_absolute_error(yg_test, yg_pred)
    print(f"MAE: {mae:.4f}")
    
    # Save
    joblib.dump(xgb_model, 'lineup_outcome_model.pkl')
    joblib.dump(gbr_model, 'lineup_goals_model.pkl')
    
    with open('lineup_model_accuracy.txt', 'w') as f:
        f.write(f"{acc:.4f}")
    
    print(f"\nModels saved: lineup_outcome_model.pkl, lineup_goals_model.pkl")
    print(f"Lineup model accuracy: {acc*100:.1f}%")
    
    return xgb_model, gbr_model, feature_cols


if __name__ == '__main__':
    train_models()
