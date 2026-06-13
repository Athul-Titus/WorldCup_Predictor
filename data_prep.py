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
    team_wins = {}
    team_matches = {}
    team_goals_scored = {}
    team_goals_conceded = {}
    team_recent_form = {}  # list of last N results

    FORM_WINDOW = 10

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
        if ht in team_matches and team_matches[ht] >= 3:
            n = team_matches[ht]
            home_win_rates[i] = team_wins.get(ht, 0) / n
            home_avg_gf[i] = team_goals_scored[ht] / n
            home_avg_ga[i] = team_goals_conceded[ht] / n
            home_gdiff[i] = (team_goals_scored[ht] - team_goals_conceded[ht]) / n
            # Form from recent results
            recent = team_recent_form.get(ht, [])
            if recent:
                home_form[i] = sum(recent[-5:]) / min(len(recent), 5)

        if at in team_matches and team_matches[at] >= 3:
            n = team_matches[at]
            away_win_rates[i] = team_wins.get(at, 0) / n
            away_avg_gf[i] = team_goals_scored[at] / n
            away_avg_ga[i] = team_goals_conceded[at] / n
            away_gdiff[i] = (team_goals_scored[at] - team_goals_conceded[at]) / n
            recent = team_recent_form.get(at, [])
            if recent:
                away_form[i] = sum(recent[-5:]) / min(len(recent), 5)

        # ── Update stats AFTER reading ───────────────────────────────────────
        # Home team
        team_matches[ht] = team_matches.get(ht, 0) + 1
        team_goals_scored[ht] = team_goals_scored.get(ht, 0) + hs
        team_goals_conceded[ht] = team_goals_conceded.get(ht, 0) + as_

        if hs > as_:
            team_wins[ht] = team_wins.get(ht, 0) + 1
            pts = 3
        elif hs == as_:
            pts = 1
        else:
            pts = 0
        team_recent_form.setdefault(ht, []).append(pts)
        if len(team_recent_form[ht]) > FORM_WINDOW:
            team_recent_form[ht] = team_recent_form[ht][-FORM_WINDOW:]

        # Away team
        team_matches[at] = team_matches.get(at, 0) + 1
        team_goals_scored[at] = team_goals_scored.get(at, 0) + as_
        team_goals_conceded[at] = team_goals_conceded.get(at, 0) + hs

        if as_ > hs:
            team_wins[at] = team_wins.get(at, 0) + 1
            pts_a = 3
        elif hs == as_:
            pts_a = 1
        else:
            pts_a = 0
        team_recent_form.setdefault(at, []).append(pts_a)
        if len(team_recent_form[at]) > FORM_WINDOW:
            team_recent_form[at] = team_recent_form[at][-FORM_WINDOW:]

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
