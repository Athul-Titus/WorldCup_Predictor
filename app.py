import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt
import joblib
import os

st.set_page_config(page_title="World Cup Data App", layout="wide", initial_sidebar_state="expanded")

# Inject custom CSS for Glassmorphism
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")

# Helper formatting
def format_money(val):
    if pd.isna(val):
        return "N/A"
    return f"€{val / 1e6:.1f}M"

# Setup transparent plotly template
import plotly.io as pio
transparent_template = pio.templates["plotly_dark"]
transparent_template.layout.paper_bgcolor = "rgba(0,0,0,0)"
transparent_template.layout.plot_bgcolor = "rgba(0,0,0,0)"
pio.templates.default = transparent_template

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

if results_df.empty or players_df.empty:
    st.warning("Data files not found. Please place Kaggle datasets in the `data/` folder and run the pipeline scripts.")
    st.stop()

# ── SIDEBAR (Navigation & Meta) ──
st.sidebar.markdown("<h1>⚽ WC Predictor</h1>", unsafe_allow_html=True)
st.sidebar.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

st.sidebar.markdown("### Navigation")
st.sidebar.markdown("""
- [Match Predictor](#match-predictor)
- [Player Overview](#player-overview)
- [Player Search](#player-search)
- [Cluster Analysis](#cluster-analysis)
""")

st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
st.sidebar.markdown("### Model Stats")
if model_accuracy:
    st.sidebar.metric("Accuracy", f"{model_accuracy*100:.1f}%")
    
wc_results = results_df[results_df['tournament'].str.contains('FIFA World Cup', case=False, na=False)]
st.sidebar.metric("Total WC Matches", len(wc_results))
st.sidebar.caption(f"{wc_results['date'].min().strftime('%Y')} - {wc_results['date'].max().strftime('%Y')}")

# ── HERO SECTION: MATCH PREDICTOR ──
st.markdown("<div id='match-predictor' class='scroll-section'>", unsafe_allow_html=True)
st.markdown("<h1>AI Match Predictor</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.2rem; color: #cbd5e1;'>Forecast the outcome of any matchup based on 100+ years of historical data.</p>", unsafe_allow_html=True)

st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
teams = sorted(list(set(wc_results['home_team'].unique()) | set(wc_results['away_team'].unique())))

with col1:
    home_team = st.selectbox("Select Home Team", teams, index=0)
with col2:
    away_team = st.selectbox("Select Away Team", teams, index=1 if len(teams) > 1 else 0)
    
if home_team == away_team:
    st.error("Home and Away teams must be different!")
else:
    if st.button("Simulate Match ⚡", use_container_width=True):
        if model is None or features_df.empty:
            st.error("Model or features not found.")
        else:
            with st.spinner("Analyzing data..."):
                home_latest = features_df[(features_df['home_team'] == home_team) | (features_df['away_team'] == home_team)].tail(1)
                away_latest = features_df[(features_df['home_team'] == away_team) | (features_df['away_team'] == away_team)].tail(1)
                
                if home_latest.empty or away_latest.empty:
                    st.warning("Insufficient historical data for selected teams.")
                else:
                    if home_latest['home_team'].values[0] == home_team:
                        h_win_rate, h_gs, h_gc = home_latest['home_win_rate'].values[0], home_latest['home_avg_goals_scored'].values[0], home_latest['home_avg_goals_conceded'].values[0]
                    else:
                        h_win_rate, h_gs, h_gc = home_latest['away_win_rate'].values[0], home_latest['away_avg_goals_scored'].values[0], home_latest['away_avg_goals_conceded'].values[0]
                        
                    if away_latest['home_team'].values[0] == away_team:
                        a_win_rate, a_gs, a_gc = away_latest['home_win_rate'].values[0], away_latest['home_avg_goals_scored'].values[0], away_latest['home_avg_goals_conceded'].values[0]
                    else:
                        a_win_rate, a_gs, a_gc = away_latest['away_win_rate'].values[0], away_latest['away_avg_goals_scored'].values[0], away_latest['away_avg_goals_conceded'].values[0]
                        
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
                    
                    outcome_map = {2: (f"{home_team} WINS", "#10b981"), 
                                   1: ("DRAW", "#94a3b8"), 
                                   0: (f"{away_team} WINS", "#ef4444")}
                    
                    text, color = outcome_map[pred]
                    st.markdown(f"<h2 style='text-align: center; color: {color}; margin-top: 20px; font-size: 3rem;'>{text}</h2>", unsafe_allow_html=True)
                    
                    classes = list(model.classes_)
                    prob_dict = {
                        'Outcome': ['Away Win', 'Draw', 'Home Win'],
                        'Probability': [probs[classes.index(0)] if 0 in classes else 0,
                                        probs[classes.index(1)] if 1 in classes else 0,
                                        probs[classes.index(2)] if 2 in classes else 0]
                    }
                    fig = px.bar(pd.DataFrame(prob_dict), x='Outcome', y='Probability', color='Outcome',
                                 color_discrete_map={'Home Win':'#10b981', 'Draw':'#94a3b8', 'Away Win':'#ef4444'})
                    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=300)
                    st.plotly_chart(fig, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 50px 0;'>", unsafe_allow_html=True)

# ── SCROLL SECTION: PLAYER OVERVIEW ──
st.markdown("<div id='player-overview' class='scroll-section'>", unsafe_allow_html=True)
st.markdown("<h1>Player Demographics</h1>", unsafe_allow_html=True)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Profiles", f"{len(players_df):,}")
kpi2.metric("Avg Goals/Game", f"{players_df['avg_goals_per_game'].mean():.2f}")
kpi3.metric("Avg Market Value", format_money(players_df['market_value_in_eur'].mean()))
kpi4.metric("Top Position", players_df['position'].mode()[0])

st.markdown("<div class='glass-container' style='margin-top: 20px;'>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    fig_pie = px.pie(players_df, names='position', hole=0.6, title="Position Distribution")
    fig_pie.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#000000', width=0)))
    st.plotly_chart(fig_pie, use_container_width=True)
with c2:
    fig_hist = px.histogram(players_df, x='market_value_in_eur', log_y=True, nbins=50,
                            title="Market Value Distribution", color_discrete_sequence=['#a855f7'])
    st.plotly_chart(fig_hist, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 50px 0;'>", unsafe_allow_html=True)

# ── SCROLL SECTION: PLAYER SEARCH ──
st.markdown("<div id='player-search' class='scroll-section'>", unsafe_allow_html=True)
st.markdown("<h1>Scout a Player</h1>", unsafe_allow_html=True)

search_term = st.text_input("Enter player name (e.g. Messi, Ronaldo):", placeholder="Start typing...")
if search_term:
    matches = players_df[players_df['name'].str.contains(search_term, case=False, na=False)]
    if matches.empty:
        st.warning("No players found matching that criteria.")
    else:
        selected_name = st.selectbox("Select a match:", matches['name'].tolist())
        player_data = matches[matches['name'] == selected_name].iloc[0]
        
        st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
        pc1, pc2 = st.columns([1, 2])
        
        with pc1:
            st.markdown(f"<h2>{player_data['name']}</h2>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: #94a3b8; font-size: 1.1rem;'>{player_data['position']} &bull; {player_data['country_of_birth']}</p>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='color: #10b981;'>{format_money(player_data['market_value_in_eur'])}</h3>", unsafe_allow_html=True)
            
            st.markdown("<br><b>Career Stats</b>", unsafe_allow_html=True)
            st.write(f"Games: {player_data['games_played']}")
            st.write(f"Goals: {player_data['total_goals']}")
            st.write(f"Assists: {player_data['total_assists']}")
            st.write(f"Minutes: {player_data['total_minutes_played']:,}")
            
        with pc2:
            stats = ['total_goals', 'total_assists', 'total_minutes_played', 'yellow_cards', 'market_value_in_eur']
            pos_df = players_df[players_df['position'] == player_data['position']]
            
            p_vals = []
            avg_vals = []
            for stat in stats:
                max_val = pos_df[stat].max()
                min_val = pos_df[stat].min()
                if max_val == min_val:
                    p_vals.append(0)
                    avg_vals.append(0)
                else:
                    p_vals.append((player_data[stat] - min_val) / (max_val - min_val))
                    avg_vals.append((pos_df[stat].mean() - min_val) / (max_val - min_val))
                    
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=p_vals, theta=['Goals', 'Assists', 'Minutes', 'Cards', 'Value'],
                fill='toself', name=player_data['name'], line_color='#3b82f6'
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=avg_vals, theta=['Goals', 'Assists', 'Minutes', 'Cards', 'Value'],
                fill='toself', name=f"Avg {player_data['position']}", line_color='#94a3b8', opacity=0.5
            ))
            
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 1]), bgcolor='rgba(0,0,0,0)'),
                                    showlegend=True, margin=dict(t=20, b=20, l=20, r=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_radar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 50px 0;'>", unsafe_allow_html=True)

# ── SCROLL SECTION: CLUSTERING ──
st.markdown("<div id='cluster-analysis' class='scroll-section'>", unsafe_allow_html=True)
st.markdown("<h1>AI Clustering Analysis</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #cbd5e1;'>Players are categorized into 4 distinct playstyles using KMeans clustering.</p>", unsafe_allow_html=True)

st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
tab1, tab2 = st.tabs(["3D Scatter", "Cluster Averages"])

with tab1:
    fig_scatter3d = px.scatter_3d(players_df, x='total_goals', y='total_assists', z='total_minutes_played',
                                  color='cluster_label', hover_data=['name'],
                                  color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_scatter3d.update_layout(scene=dict(bgcolor='rgba(0,0,0,0)'), margin=dict(l=0, r=0, b=0, t=0))
    st.plotly_chart(fig_scatter3d, use_container_width=True, height=600)
    
with tab2:
    cluster_summary = players_df.groupby('cluster_label')[['total_goals', 'total_assists', 'total_minutes_played', 'market_value_in_eur']].mean().reset_index()
    
    # Format the table nicely
    styled_df = cluster_summary.style.format({
        'total_goals': '{:.1f}',
        'total_assists': '{:.1f}',
        'total_minutes_played': '{:.0f}',
        'market_value_in_eur': lambda x: format_money(x)
    }).background_gradient(cmap='Blues', subset=['total_goals', 'total_assists'])
    
    st.dataframe(styled_df, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
