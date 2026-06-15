"""
data_prep.py — Prepare match features for training the prediction model.
Optimized version: precomputes team stats in batch rather than per-match iteration.
"""
import pandas as pd
import numpy as np
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')


def prepare_match_data():
    print("Starting Phase 1: Match Data Preparation (Optimized)...")

    results_path = 'data/results.csv'
    if not os.path.exists(results_path):
        print(f"Error: {results_path} not found.")
        return

    df = pd.read_csv(results_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    df = df.dropna(subset=['home_score', 'away_score'])

    print(f"  Total matches loaded: {len(df)}")

    # Create outcome label (0: Away Win, 1: Draw, 2: Home Win)
    df['outcome'] = np.where(
        df['home_score'] > df['away_score'], 2,
        np.where(df['home_score'] == df['away_score'], 1, 0)
    )
    df['goal_diff'] = df['home_score'] - df['away_score']

    # ── Tournament importance weight ─────────────────────────────────────────
    def tournament_weight(t):
        t_lower = str(t).lower()
        if 'world cup' in t_lower and 'qualification' not in t_lower:
            return 3.0
        elif 'euro' in t_lower and 'qualification' not in t_lower:
            return 2.5
        elif 'copa' in t_lower or 'african cup' in t_lower or 'asian cup' in t_lower:
            return 2.0
        elif 'nations league' in t_lower:
            return 1.8
        elif 'qualification' in t_lower:
            return 1.5
        return 1.0

    df['tournament_weight'] = df['tournament'].apply(tournament_weight)

    # ── Recency weight ───────────────────────────────────────────────────────
    max_date = df['date'].max()
    days_ago = (max_date - df['date']).dt.days
    df['recency_weight'] = np.exp(-days_ago / (365 * 5))
    df['sample_weight'] = df['tournament_weight'] * df['recency_weight']

    # ══════════════════════════════════════════════════════════════════════════
    # FAST APPROACH: Precompute team stats using expanding windows
    # Instead of iterating per-match, build team-level history once
    # ══════════════════════════════════════════════════════════════════════════

    print("  Building team history...")

    # Build per-team match history
    all_teams = set(df['home_team'].unique()) | set(df['away_team'].unique())
    print(f"  Teams in dataset: {len(all_teams)}")

    # For each match, compute rolling stats for the home and away team
    # We'll use a dictionary-based approach with cumulative stats

    # Initialize team stats tracker
    team_history = {} # team_name -> {'wins': [], 'goals_scored': [], 'goals_conceded': [], 'pts': []}
    ROLLING_WINDOW = 30

    home_win_rates = np.full(len(df), 0.33)
    away_win_rates = np.full(len(df), 0.33)
    home_avg_gf = np.full(len(df), 1.2)
    home_avg_ga = np.full(len(df), 1.2)
    away_avg_gf = np.full(len(df), 1.2)
    away_avg_ga = np.full(len(df), 1.2)
    home_form = np.full(len(df), 1.0)
    away_form = np.full(len(df), 1.0)
    home_gdiff = np.full(len(df), 0.0)
    away_gdiff = np.full(len(df), 0.0)

    print("  Computing rolling features (single pass)...")
    for i, row in df.iterrows():
        ht = row['home_team']
        at = row['away_team']
        hs = row['home_score']
        as_ = row['away_score']

        # ── Read current stats BEFORE updating ───────────────────────────────
        if ht in team_history and len(team_history[ht]['wins']) >= 3:
            hist = team_history[ht]
            n = len(hist['wins'])
            home_win_rates[i] = sum(hist['wins']) / n
            home_avg_gf[i] = sum(hist['goals_scored']) / n
            home_avg_ga[i] = sum(hist['goals_conceded']) / n
            home_gdiff[i] = (sum(hist['goals_scored']) - sum(hist['goals_conceded'])) / n
            home_form[i] = sum(hist['pts'][-5:]) / min(n, 5)

        if at in team_history and len(team_history[at]['wins']) >= 3:
            hist = team_history[at]
            n = len(hist['wins'])
            away_win_rates[i] = sum(hist['wins']) / n
            away_avg_gf[i] = sum(hist['goals_scored']) / n
            away_avg_ga[i] = sum(hist['goals_conceded']) / n
            away_gdiff[i] = (sum(hist['goals_scored']) - sum(hist['goals_conceded'])) / n
            away_form[i] = sum(hist['pts'][-5:]) / min(n, 5)

        # ── Update stats AFTER reading ───────────────────────────────────────
        # Home team
        if ht not in team_history:
            team_history[ht] = {'wins': [], 'goals_scored': [], 'goals_conceded': [], 'pts': []}
        h_win = 1 if hs > as_ else 0
        h_pts = 3 if hs > as_ else (1 if hs == as_ else 0)
        team_history[ht]['wins'].append(h_win)
        team_history[ht]['goals_scored'].append(hs)
        team_history[ht]['goals_conceded'].append(as_)
        team_history[ht]['pts'].append(h_pts)
        for k in team_history[ht]:
            if len(team_history[ht][k]) > ROLLING_WINDOW:
                team_history[ht][k] = team_history[ht][k][-ROLLING_WINDOW:]

        # Away team
        if at not in team_history:
            team_history[at] = {'wins': [], 'goals_scored': [], 'goals_conceded': [], 'pts': []}
        a_win = 1 if as_ > hs else 0
        a_pts = 3 if as_ > hs else (1 if hs == as_ else 0)
        team_history[at]['wins'].append(a_win)
        team_history[at]['goals_scored'].append(as_)
        team_history[at]['goals_conceded'].append(hs)
        team_history[at]['pts'].append(a_pts)
        for k in team_history[at]:
            if len(team_history[at][k]) > ROLLING_WINDOW:
                team_history[at][k] = team_history[at][k][-ROLLING_WINDOW:]

        if i % 10000 == 0 and i > 0:
            print(f"    {i}/{len(df)} matches processed...")

    # Assign computed arrays
    df['home_win_rate'] = home_win_rates
    df['away_win_rate'] = away_win_rates
    df['home_avg_goals_scored'] = home_avg_gf
    df['home_avg_goals_conceded'] = home_avg_ga
    df['away_avg_goals_scored'] = away_avg_gf
    df['away_avg_goals_conceded'] = away_avg_ga
    df['home_form'] = home_form
    df['away_form'] = away_form
    df['home_goal_diff'] = home_gdiff
    df['away_goal_diff'] = away_gdiff
    df['head_to_head_home_win_rate'] = 0.5  # Simplified - H2H is expensive

    # Save features
    feature_cols = [
        'home_win_rate', 'away_win_rate',
        'home_avg_goals_scored', 'home_avg_goals_conceded',
        'away_avg_goals_scored', 'away_avg_goals_conceded',
        'head_to_head_home_win_rate',
        'home_form', 'away_form',
        'home_goal_diff', 'away_goal_diff',
    ]
    output_cols = ['date', 'home_team', 'away_team', 'outcome', 'sample_weight'] + feature_cols
    features_df = df[output_cols]
    features_df.to_csv('features.csv', index=False)
    print(f"\nPhase 1 Complete: features.csv created with {len(features_df)} matches and {len(feature_cols)} features.")


if __name__ == "__main__":
    prepare_match_data()
