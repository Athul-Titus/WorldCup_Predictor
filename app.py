import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt
import joblib
import os

st.set_page_config(page_title="World Cup Data App", layout="wide")

# Helper formatting
def format_money(val):
    if pd.isna(val):
        return "N/A"
    return f"€{val / 1e6:.1f}M"

# Load data
@st.cache_data
def load_data():
    results = pd.read_csv('data/results.csv') if os.path.exists('data/results.csv') else pd.DataFrame()
    if not results.empty:
        results['date'] = pd.to_datetime(results['date'])
        
    features = pd.read_csv('features.csv') if os.path.exists('features.csv') else pd.DataFrame()
    player_clustered = pd.read_csv('player_clustered.csv') if os.path.exists('player_clustered.csv') else pd.DataFrame()
    
    return results, features, player_clustered

@st.cache_resource
def load_model():
    if os.path.exists('model.pkl'):
        return joblib.load('model.pkl')
    return None

def load_accuracy():
    if os.path.exists('model_accuracy.txt'):
        with open('model_accuracy.txt', 'r') as f:
            return float(f.read().strip())
    return None

results_df, features_df, players_df = load_data()
model = load_model()
model_accuracy = load_accuracy()

st.title("⚽ World Cup Data Science App")

if results_df.empty or players_df.empty:
    st.warning("Data files not found. Please place Kaggle datasets in the `data/` folder and run the pipeline scripts.")
    st.stop()

tab1, tab2 = st.tabs(["⚽ Match Predictor", "📊 Player Dashboard"])

# ── TAB 1: Match Predictor ──
with tab1:
    st.sidebar.header("Dataset Info")
    if model_accuracy:
        st.sidebar.metric("Model Accuracy", f"{model_accuracy*100:.1f}%")
    
    wc_results = results_df[results_df['tournament'].str.contains('FIFA World Cup', case=False, na=False)]
    st.sidebar.metric("Total WC Matches", len(wc_results))
    st.sidebar.text(f"Date Range:\n{wc_results['date'].min().strftime('%Y-%m-%d')} to {wc_results['date'].max().strftime('%Y-%m-%d')}")
    
    col1, col2 = st.columns(2)
    teams = sorted(list(set(wc_results['home_team'].unique()) | set(wc_results['away_team'].unique())))
    
    with col1:
        home_team = st.selectbox("Select Home Team", teams, index=0)
    with col2:
        away_team = st.selectbox("Select Away Team", teams, index=1 if len(teams) > 1 else 0)
        
    if home_team == away_team:
        st.error("Home and Away teams must be different!")
    else:
        if st.button("Predict Outcome"):
            if model is None or features_df.empty:
                st.error("Model or features not found. Please run data_prep.py and train_model.py.")
            else:
                with st.spinner("Predicting..."):
                    # Get latest team stats from features_df
                    home_latest = features_df[(features_df['home_team'] == home_team) | (features_df['away_team'] == home_team)].tail(1)
                    away_latest = features_df[(features_df['home_team'] == away_team) | (features_df['away_team'] == away_team)].tail(1)
                    
                    if home_latest.empty or away_latest.empty:
                        st.warning("Insufficient historical data for selected teams.")
                    else:
                        # Extract features
                        # Determine if team was home or away in their latest match
                        if home_latest['home_team'].values[0] == home_team:
                            h_win_rate = home_latest['home_win_rate'].values[0]
                            h_gs = home_latest['home_avg_goals_scored'].values[0]
                            h_gc = home_latest['home_avg_goals_conceded'].values[0]
                        else:
                            h_win_rate = home_latest['away_win_rate'].values[0]
                            h_gs = home_latest['away_avg_goals_scored'].values[0]
                            h_gc = home_latest['away_avg_goals_conceded'].values[0]
                            
                        if away_latest['home_team'].values[0] == away_team:
                            a_win_rate = away_latest['home_win_rate'].values[0]
                            a_gs = away_latest['home_avg_goals_scored'].values[0]
                            a_gc = away_latest['home_avg_goals_conceded'].values[0]
                        else:
                            a_win_rate = away_latest['away_win_rate'].values[0]
                            a_gs = away_latest['away_avg_goals_scored'].values[0]
                            a_gc = away_latest['away_avg_goals_conceded'].values[0]
                            
                        # Head to head
                        h2h = wc_results[((wc_results['home_team'] == home_team) & (wc_results['away_team'] == away_team)) |
                                         ((wc_results['home_team'] == away_team) & (wc_results['away_team'] == home_team))]
                                         
                        if not h2h.empty:
                            home_wins = sum((h2h['home_team'] == home_team) & (h2h['home_score'] > h2h['away_score'])) + \
                                        sum((h2h['away_team'] == home_team) & (h2h['away_score'] > h2h['home_score']))
                            h2h_rate = home_wins / len(h2h)
                        else:
                            h2h_rate = features_df['head_to_head_home_win_rate'].mean()
                            
                        input_data = pd.DataFrame([[h_win_rate, a_win_rate, h_gs, h_gc, a_gs, a_gc, h2h_rate]],
                                                  columns=['home_win_rate', 'away_win_rate', 'home_avg_goals_scored',
                                                           'home_avg_goals_conceded', 'away_avg_goals_scored', 
                                                           'away_avg_goals_conceded', 'head_to_head_home_win_rate'])
                                                           
                        pred = model.predict(input_data)[0]
                        probs = model.predict_proba(input_data)[0]
                        
                        outcome_map = {2: (f"{home_team} WIN", "green"), 
                                       1: ("DRAW", "gray"), 
                                       0: (f"{away_team} WIN", "red")}
                        
                        text, color = outcome_map[pred]
                        st.markdown(f"<h1 style='text-align: center; color: {color};'>{text}</h1>", unsafe_allow_html=True)
                        
                        # Probabilities
                        classes = list(model.classes_)
                        
                        prob_dict = {
                            'Outcome': ['Away Win', 'Draw', 'Home Win'],
                            'Probability': [probs[classes.index(0)] if 0 in classes else 0,
                                            probs[classes.index(1)] if 1 in classes else 0,
                                            probs[classes.index(2)] if 2 in classes else 0]
                        }
                        prob_df = pd.DataFrame(prob_dict)
                        fig = px.bar(prob_df, x='Outcome', y='Probability', color='Outcome',
                                     color_discrete_map={'Home Win':'green', 'Draw':'gray', 'Away Win':'red'},
                                     template='plotly_dark', title="Prediction Confidence")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # H2H Table
                        st.subheader("Last 10 Meetings")
                        if not h2h.empty:
                            st.dataframe(h2h.sort_values('date', ascending=False).head(10)[['date', 'tournament', 'home_team', 'away_team', 'home_score', 'away_score']])
                        else:
                            st.info("No historical matches found between these two teams.")

# ── TAB 2: Player Dashboard ──
with tab2:
    if players_df.empty:
        st.warning("Player data not found.")
    else:
        dash_tabs = st.tabs(["Overview", "Player Search", "Cluster Analysis", "Top Charts"])
        
        # Nested Tab A — Overview
        with dash_tabs[0]:
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("Total Players", len(players_df))
            kpi2.metric("Avg Goals per Game", f"{players_df['avg_goals_per_game'].mean():.2f}")
            kpi3.metric("Avg Market Value", format_money(players_df['market_value_in_eur'].mean()))
            kpi4.metric("Most Common Position", players_df['position'].mode()[0])
            
            col1, col2 = st.columns(2)
            with col1:
                fig_pie = px.pie(players_df, names='position', title="Player Distribution by Position", template="plotly_dark")
                st.plotly_chart(fig_pie, use_container_width=True)
            with col2:
                fig_hist = px.histogram(players_df, x='market_value_in_eur', log_y=True, 
                                        title="Market Value Distribution (Log Scale)", template="plotly_dark")
                st.plotly_chart(fig_hist, use_container_width=True)

        # Nested Tab B — Player Search
        with dash_tabs[1]:
            search_term = st.text_input("Search Player by Name (Case-insensitive):")
            if search_term:
                matches = players_df[players_df['name'].str.contains(search_term, case=False, na=False)]
                if matches.empty:
                    st.warning("No players found.")
                else:
                    selected_name = st.selectbox("Select a player", matches['name'].tolist())
                    player_data = matches[matches['name'] == selected_name].iloc[0]
                    
                    st.subheader(f"Card: {player_data['name']}")
                    st.write(f"**Position:** {player_data['position']} | **Nationality:** {player_data['country_of_birth']} | **Market Value:** {format_money(player_data['market_value_in_eur'])}")
                    st.write(f"**Games:** {player_data['games_played']} | **Goals:** {player_data['total_goals']} | **Assists:** {player_data['total_assists']}")
                    
                    # Radar chart
                    stats = ['total_goals', 'total_assists', 'total_minutes_played', 'yellow_cards', 'market_value_in_eur']
                    pos_df = players_df[players_df['position'] == player_data['position']]
                    
                    p_vals = []
                    for stat in stats:
                        max_val = pos_df[stat].max()
                        min_val = pos_df[stat].min()
                        if max_val == min_val:
                            p_vals.append(0)
                        else:
                            p_vals.append((player_data[stat] - min_val) / (max_val - min_val))
                            
                    fig_radar = go.Figure()
                    fig_radar.add_trace(go.Scatterpolar(
                        r=p_vals,
                        theta=['Goals', 'Assists', 'Minutes', 'Yellow Cards', 'Market Value'],
                        fill='toself',
                        name=player_data['name']
                    ))
                    
                    avg_vals = []
                    for stat in stats:
                        max_val = pos_df[stat].max()
                        min_val = pos_df[stat].min()
                        avg = pos_df[stat].mean()
                        if max_val == min_val:
                            avg_vals.append(0)
                        else:
                            avg_vals.append((avg - min_val) / (max_val - min_val))
                            
                    fig_radar.add_trace(go.Scatterpolar(
                        r=avg_vals,
                        theta=['Goals', 'Assists', 'Minutes', 'Yellow Cards', 'Market Value'],
                        fill='toself',
                        name=f"Avg {player_data['position']}"
                    ))
                    
                    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                                            showlegend=True, template="plotly_dark", title=f"{player_data['name']} vs Position Average")
                    st.plotly_chart(fig_radar, use_container_width=True)

        # Nested Tab C — Cluster Analysis
        with dash_tabs[2]:
            st.subheader("Cluster Analysis")
            
            fig_scatter2d = px.scatter(players_df, x='total_goals', y='total_assists', color='cluster_label',
                                       hover_data=['name', 'position'], title="Goals vs Assists", template="plotly_dark")
            st.plotly_chart(fig_scatter2d, use_container_width=True)
            
            fig_scatter3d = px.scatter_3d(players_df, x='total_goals', y='total_assists', z='total_minutes_played',
                                          color='cluster_label', hover_data=['name'], title="3D Scatter", template="plotly_dark")
            st.plotly_chart(fig_scatter3d, use_container_width=True)
            
            st.write("Cluster Summary (Averages)")
            cluster_summary = players_df.groupby('cluster_label')[['total_goals', 'total_assists', 'total_minutes_played', 'avg_goals_per_game', 'avg_assists_per_game']].mean().reset_index()
            st.dataframe(cluster_summary)
            
            st.write("Correlation Heatmap")
            numeric_cols = ['total_goals', 'total_assists', 'total_minutes_played', 'avg_goals_per_game', 'avg_assists_per_game', 'market_value_in_eur', 'yellow_cards', 'red_cards', 'games_played']
            corr = players_df[numeric_cols].corr()
            fig_heatmap = plt.figure(figsize=(10, 8))
            
            # Use dark theme for heatmap
            plt.style.use('dark_background')
            sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
            
            st.pyplot(fig_heatmap)

        # Nested Tab D — Top Charts
        with dash_tabs[3]:
            st.subheader("Top Charts")
            
            col1, col2 = st.columns(2)
            with col1:
                top_goals = players_df.nlargest(10, 'total_goals')
                fig1 = px.bar(top_goals, x='name', y='total_goals', title="Top 10 Players by Goals", template="plotly_dark")
                st.plotly_chart(fig1, use_container_width=True)
                
            with col2:
                top_assists = players_df.nlargest(10, 'total_assists')
                fig2 = px.bar(top_assists, x='name', y='total_assists', title="Top 10 Players by Assists", template="plotly_dark")
                st.plotly_chart(fig2, use_container_width=True)
                
            top_value = players_df.nlargest(10, 'market_value_in_eur')
            fig3 = px.bar(top_value, y='name', x='market_value_in_eur', orientation='h', title="Top 10 Players by Market Value", template="plotly_dark")
            fig3.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig3, use_container_width=True)
            
            fig4 = px.scatter(players_df, x='market_value_in_eur', y='total_goals', color='position',
                              hover_data=['name'], title="Goals vs Market Value by Position", template="plotly_dark")
            st.plotly_chart(fig4, use_container_width=True)
