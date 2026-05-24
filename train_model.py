import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

def train_match_model():
    print("Starting Phase 2: Match Outcome Model Training...")
    
    features_path = 'features.csv'
    if not os.path.exists(features_path):
        print(f"Error: {features_path} not found. Please run data_prep.py first.")
        return
        
    df = pd.read_csv(features_path)
    
    # Target and Features
    # Features: home_win_rate, away_win_rate, home_avg_goals_scored,
    # home_avg_goals_conceded, away_avg_goals_scored, away_avg_goals_conceded,
    # head_to_head_home_win_rate
    
    feature_cols = ['home_win_rate', 'away_win_rate', 'home_avg_goals_scored',
                    'home_avg_goals_conceded', 'away_avg_goals_scored', 
                    'away_avg_goals_conceded', 'head_to_head_home_win_rate']
                    
    X = df[feature_cols]
    y = df['outcome']
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train
    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    
    print(f"Model Accuracy: {acc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save model and accuracy
    joblib.dump(model, 'model.pkl')
    with open('model_accuracy.txt', 'w') as f:
        f.write(str(acc))
    print("Phase 2 Complete: model.pkl and model_accuracy.txt saved successfully.")

if __name__ == "__main__":
    train_match_model()
