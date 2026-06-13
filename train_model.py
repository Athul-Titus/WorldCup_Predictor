import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')


def train_match_model():
    print("Starting Phase 2: Match Outcome Model Training (XGBoost)...")

    features_path = 'features.csv'
    if not os.path.exists(features_path):
        print(f"Error: {features_path} not found. Please run data_prep.py first.")
        return

    df = pd.read_csv(features_path)
    df['date'] = pd.to_datetime(df['date'])

    # Features
    feature_cols = [
        'home_win_rate', 'away_win_rate',
        'home_avg_goals_scored', 'home_avg_goals_conceded',
        'away_avg_goals_scored', 'away_avg_goals_conceded',
        'head_to_head_home_win_rate',
        'home_form', 'away_form',
        'home_goal_diff', 'away_goal_diff',
    ]
    # Only use features that exist
    feature_cols = [c for c in feature_cols if c in df.columns]

    # Drop rows with NaN in features
    df_clean = df.dropna(subset=feature_cols + ['outcome'])

    X = df_clean[feature_cols]
    y = df_clean['outcome'].astype(int)
    weights = df_clean['sample_weight'].values if 'sample_weight' in df_clean.columns else None

    print(f"Training data: {len(X)} matches, {len(feature_cols)} features")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    if weights is not None:
        w_train = weights[X_train.index - X_train.index.min()] if hasattr(X_train, 'index') else None
        _, w_test_arr = train_test_split(weights, test_size=0.2, random_state=42)
        w_train_arr = weights[:len(X_train)]
    else:
        w_train_arr = None

    # Train XGBoost
    model = XGBClassifier(
        n_estimators=400,
        max_depth=6,
        learning_rate=0.08,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        random_state=42,
        use_label_encoder=False,
        eval_metric='mlogloss',
    )

    # Use sample weights in training
    if 'sample_weight' in df_clean.columns:
        w_train, w_test = train_test_split(
            df_clean['sample_weight'].values, test_size=0.2, random_state=42
        )
        model.fit(X_train, y_train, sample_weight=w_train)
    else:
        model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print(f"\nModel Accuracy: {acc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred,
                                target_names=['Away Win', 'Draw', 'Home Win'],
                                zero_division=0))

    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
    print(f"5-Fold CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    # Feature importance
    print("\nFeature Importance:")
    importances = sorted(zip(feature_cols, model.feature_importances_),
                         key=lambda x: x[1], reverse=True)
    for feat, imp in importances:
        print(f"  {feat}: {imp:.4f}")

    # Save
    joblib.dump(model, 'model.pkl')
    with open('model_accuracy.txt', 'w') as f:
        f.write(str(acc))
    print(f"\nPhase 2 Complete: model.pkl saved (accuracy: {acc*100:.1f}%)")


if __name__ == "__main__":
    train_match_model()
