"""
lineup_model.py — Train lineup-aware prediction models.
1. XGBClassifier for match outcome (Win/Draw/Loss)
2. GradientBoostingRegressor for total goals

Uses ALL international matches from 2010+ (not just WC) for much more training data.
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, mean_absolute_error
from xgboost import XGBClassifier
from sklearn.ensemble import GradientBoostingRegressor
from imblearn.over_sampling import SMOTE
import joblib
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')


def build_training_data():
    """Build training data from ALL international matches (2010+), not just WC."""
    print("Building lineup training data...")

    results = pd.read_csv('data/results.csv')
    results['date'] = pd.to_datetime(results['date'])

    # Use ALL international matches from 2010+ for much more training data
    matches = results[results['date'].dt.year >= 2010].copy()
    matches = matches.dropna(subset=['home_score', 'away_score'])
    print(f"  Total matches 2010+: {len(matches)}")

    # Load team profiles
    profiles = pd.read_csv('data/team_profiles.csv')

    # Load features for historical win rates
    features_path = 'features.csv'
    if os.path.exists(features_path):
        features = pd.read_csv(features_path)
    else:
        features = pd.DataFrame()

    # Create outcome and total goals
    conditions = [
        (matches['home_score'] > matches['away_score']),
        (matches['home_score'] == matches['away_score']),
        (matches['home_score'] < matches['away_score'])
    ]
    matches['outcome'] = np.select(conditions, [2, 1, 0], default=1)
    matches['total_goals'] = matches['home_score'] + matches['away_score']

    # Merge with team profiles
    # Merge with team profiles for Home Team
    matches = matches.merge(profiles, left_on='home_team', right_on='team', how='left')
    rename_home = {c: c.replace('team_', 'home_') for c in profiles.columns if c != 'team'}
    matches = matches.rename(columns=rename_home)
    matches = matches.drop(columns=['team'], errors='ignore')

    # Merge with team profiles for Away Team
    matches = matches.merge(profiles, left_on='away_team', right_on='team', how='left')
    rename_away = {c: c.replace('team_', 'away_') for c in profiles.columns if c != 'team'}
    matches = matches.rename(columns=rename_away)
    matches = matches.drop(columns=['team'], errors='ignore')

    # Add difference features
    for stat in ['avg_overall', 'avg_shooting', 'avg_passing', 'avg_defending', 'avg_pace']:
        h_col = f'home_{stat}'
        a_col = f'away_{stat}'
        if h_col in matches.columns and a_col in matches.columns:
            matches[f'diff_{stat}'] = matches[h_col] - matches[a_col]

    # Add historical win rates from features
    matches['home_win_rate'] = 0.33
    matches['away_win_rate'] = 0.33

    if not features.empty and 'home_win_rate' in features.columns:
        feat_latest = features.sort_values('date').drop_duplicates(
            subset=['home_team', 'away_team'], keep='last'
        )
        for idx, row in matches.iterrows():
            match_feat = feat_latest[
                (feat_latest['home_team'] == row['home_team']) &
                (feat_latest['away_team'] == row['away_team'])
            ]
            if not match_feat.empty:
                matches.at[idx, 'home_win_rate'] = match_feat['home_win_rate'].values[0]
                matches.at[idx, 'away_win_rate'] = match_feat['away_win_rate'].values[0]

    # Fill NaN with defaults
    stat_cols = [c for c in matches.columns if any(
        s in c for s in ['avg_overall', 'avg_shooting', 'avg_passing',
                         'avg_defending', 'avg_pace', 'star_rating', 'gk_rating']
    )]
    for col in stat_cols:
        matches[col] = matches[col].fillna(75)

    matches['home_win_rate'] = matches['home_win_rate'].fillna(0.33)
    matches['away_win_rate'] = matches['away_win_rate'].fillna(0.33)

    # Fill diff features
    diff_cols = [c for c in matches.columns if c.startswith('diff_')]
    for col in diff_cols:
        matches[col] = matches[col].fillna(0)

    return matches


def train_models():
    """Train XGBClassifier and GradientBoostingRegressor."""
    matches = build_training_data()

    feature_cols = [
        'home_avg_overall', 'home_avg_shooting', 'home_avg_passing',
        'home_avg_defending', 'home_avg_pace', 'home_star_rating', 'home_gk_rating',
        'away_avg_overall', 'away_avg_shooting', 'away_avg_passing',
        'away_avg_defending', 'away_avg_pace', 'away_star_rating', 'away_gk_rating',
        'home_win_rate', 'away_win_rate',
    ]
    # Add difference features if available
    diff_cols = [c for c in matches.columns if c.startswith('diff_')]
    feature_cols.extend(diff_cols)
    feature_cols = [c for c in feature_cols if c in matches.columns]

    # Drop rows with NaN
    clean = matches[feature_cols + ['outcome', 'total_goals']].dropna()
    X = clean[feature_cols]
    y_outcome = clean['outcome'].astype(int)
    y_goals = clean['total_goals']

    print(f"\nTraining data size: {len(X)} matches, {len(feature_cols)} features")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y_outcome, test_size=0.2, random_state=42)
    _, _, yg_train, yg_test = train_test_split(X, y_goals, test_size=0.2, random_state=42)

    # 1. Outcome classifier (XGBoost)
    print("\n--- Outcome Classifier (XGBoost) ---")
    xgb_model = XGBClassifier(
        n_estimators=400, max_depth=6, learning_rate=0.08,
        subsample=0.85, colsample_bytree=0.85,
        min_child_weight=3,
        random_state=42, use_label_encoder=False, eval_metric='mlogloss'
    )
    
    print("  Balancing classes with SMOTE...")
    smote = SMOTE(random_state=42)
    X_train_sm, y_train_sm = smote.fit_resample(X_train, y_train)
    print(f"    Before SMOTE: {np.bincount(y_train)}")
    print(f"    After SMOTE:  {np.bincount(y_train_sm)}")
    
    xgb_model.fit(X_train_sm, y_train_sm)
    y_pred = xgb_model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {acc:.4f}")
    print(classification_report(y_test, y_pred,
                                target_names=['Away Win', 'Draw', 'Home Win'],
                                zero_division=0))

    # 2. Goals regressor
    print("--- Goals Regressor (GBR) ---")
    gbr_model = GradientBoostingRegressor(
        n_estimators=300, max_depth=4, learning_rate=0.08, random_state=42
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
    print(f"Lineup model accuracy: {acc * 100:.1f}%")

    return xgb_model, gbr_model, feature_cols


if __name__ == '__main__':
    train_models()
