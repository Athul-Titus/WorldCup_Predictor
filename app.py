import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
import os

st.set_page_config(page_title="World Cup Data App", layout="wide", initial_sidebar_state="expanded")

def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")

def format_money(val):
    if pd.isna(val):
        return "N/A"
    return f"€{val / 1e6:.1f}M"

import plotly.io as pio
transparent_template = pio.templates["plotly_dark"]
transparent_template.layout.paper_bgcolor = "#0a1628"
transparent_template.layout.plot_bgcolor = "#0d1f3c"
transparent_template.layout.font.color = "#e8f4fd"
transparent_template.layout.xaxis.gridcolor = "rgba(0,229,255,0.08)"
transparent_template.layout.yaxis.gridcolor = "rgba(0,229,255,0.08)"
pio.templates.default = transparent_template

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

# ── SIDEBAR ──
st.sidebar.markdown("<h1>⚽ WC Predictor</h1>", unsafe_allow_html=True)
st.sidebar.markdown("<hr style='border-color: rgba(0,229,255,0.15);'>", unsafe_allow_html=True)

st.sidebar.markdown("### Navigation")
st.sidebar.markdown("""
- [Match Predictor](#match-predictor)
- [Player Overview](#player-overview)
- [Player Search](#player-search)
- [Cluster Analysis](#cluster-analysis)
- [Top Charts](#top-charts)
""")

st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
st.sidebar.markdown("### Model Stats")
if model_accuracy is not None:
    st.sidebar.markdown(f"""
    <div class='sidebar-stat'>
        <div class='sidebar-stat-label'>Model Accuracy</div>
        <div class='sidebar-stat-val'>{model_accuracy*100:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)
    
wc_results = results_df[results_df['tournament'].str.contains('FIFA World Cup', case=False, na=False)]
st.sidebar.markdown(f"""
<div class='sidebar-stat'>
    <div class='sidebar-stat-label'>Total WC Matches</div>
    <div class='sidebar-stat-val'>{len(wc_results)}</div>
</div>
""", unsafe_allow_html=True)

last_match = wc_results['date'].max().strftime('%Y-%m-%d') if not wc_results.empty else "N/A"
st.sidebar.markdown(f"""
<div class='sidebar-stat'>
    <div class='sidebar-stat-label'>Last Match Date</div>
    <div class='sidebar-stat-val'>{last_match}</div>
</div>
""", unsafe_allow_html=True)


# ── MATCH PREDICTOR ──
st.markdown("<div id='match-predictor' class='scroll-section'>", unsafe_allow_html=True)
st.markdown("<h1>Match Predictor</h1>", unsafe_allow_html=True)

st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
teams = sorted(list(set(wc_results['home_team'].unique()) | set(wc_results['away_team'].unique())))
col1, col2 = st.columns(2)
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
            with st.spinner("Analyzing match data..."):
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
                    classes = list(model.classes_)
                    p_away = probs[classes.index(0)] if 0 in classes else 0
                    p_draw = probs[classes.index(1)] if 1 in classes else 0
                    p_home = probs[classes.index(2)] if 2 in classes else 0
                    
                    # Layout Hero
                    st.markdown(f"""
                    <div class='hero-vs'>
                        <div style='flex:1;'>
                            <div class='team-name'>{home_team}</div>
                            <div class='team-subtitle'>Win Rate: {h_win_rate*100:.1f}%</div>
                        </div>
                        <div class='vs-badge'>VS</div>
                        <div style='flex:1;'>
                            <div class='team-name'>{away_team}</div>
                            <div class='team-subtitle'>Win Rate: {a_win_rate*100:.1f}%</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    outcome_map = {2: (f"{home_team} WINS", "result-win"), 
                                   1: ("DRAW", "result-draw"), 
                                   0: (f"{away_team} WINS", "result-loss")}
                    text, cls = outcome_map[pred]
                    st.markdown(f"<div class='prediction-result {cls}'>{text}</div>", unsafe_allow_html=True)
                    
                    # Confidence Bars
                    st.markdown(f"""
                    <div class='conf-container'>
                        <div class='conf-row'>
                            <div class='conf-label'>Win</div>
                            <div class='conf-bar-bg'><div class='conf-bar-fill fill-win' style='width:{p_home*100}%'></div></div>
                            <div class='conf-pct'>{p_home*100:.1f}%</div>
                        </div>
                        <div class='conf-row'>
                            <div class='conf-label'>Draw</div>
                            <div class='conf-bar-bg'><div class='conf-bar-fill fill-draw' style='width:{p_draw*100}%'></div></div>
                            <div class='conf-pct'>{p_draw*100:.1f}%</div>
                        </div>
                        <div class='conf-row'>
                            <div class='conf-label'>Loss</div>
                            <div class='conf-bar-bg'><div class='conf-bar-fill fill-loss' style='width:{p_away*100}%'></div></div>
                            <div class='conf-pct'>{p_away*100:.1f}%</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # H2H Table
                    st.markdown("<h3>Head-to-Head History</h3>", unsafe_allow_html=True)
                    if h2h.empty:
                        st.write("No World Cup history between these teams.")
                    else:
                        h2h_sorted = h2h.sort_values('date', ascending=False).head(5)
                        table_html = "<table class='h2h-table'><tr><th>Date</th><th>Tournament</th><th>Home</th><th>Score</th><th>Away</th></tr>"
                        for _, row in h2h_sorted.iterrows():
                            # Determine color from home team's perspective in this UI, but generally just highlight the winner
                            if row['home_score'] > row['away_score']:
                                hc = 'h2h-win' if row['home_team'] == home_team else 'h2h-loss'
                                ac = 'h2h-loss' if row['home_team'] == home_team else 'h2h-win'
                            elif row['home_score'] < row['away_score']:
                                hc = 'h2h-loss' if row['home_team'] == home_team else 'h2h-win'
                                ac = 'h2h-win' if row['home_team'] == home_team else 'h2h-loss'
                            else:
                                hc = ac = 'h2h-draw'
                                
                            table_html += f"<tr><td>{row['date'].strftime('%Y-%m-%d')}</td><td>{row['tournament']}</td>"
                            table_html += f"<td class='{hc}'>{row['home_team']}</td>"
                            table_html += f"<td>{row['home_score']} - {row['away_score']}</td>"
                            table_html += f"<td class='{ac}'>{row['away_team']}</td></tr>"
                        table_html += "</table>"
                        st.markdown(table_html, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)


# ── PLAYER OVERVIEW ──
st.markdown("<div id='player-overview' class='scroll-section'>", unsafe_allow_html=True)
st.markdown("<h1>Player Overview</h1>", unsafe_allow_html=True)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.markdown(f"<div class='kpi-card'><div class='kpi-value'>{len(players_df):,}</div><div class='kpi-label'>Total Profiles</div></div>", unsafe_allow_html=True)
with kpi2:
    st.markdown(f"<div class='kpi-card'><div class='kpi-value'>{players_df['avg_goals_per_game'].mean():.2f}</div><div class='kpi-label'>Avg Goals/Game</div></div>", unsafe_allow_html=True)
with kpi3:
    st.markdown(f"<div class='kpi-card'><div class='kpi-value'>{format_money(players_df['market_value_in_eur'].mean())}</div><div class='kpi-label'>Avg Market Value</div></div>", unsafe_allow_html=True)
with kpi4:
    st.markdown(f"<div class='kpi-card'><div class='kpi-value'>{players_df['position'].mode()[0]}</div><div class='kpi-label'>Top Position</div></div>", unsafe_allow_html=True)

st.markdown("<div class='glass-container' style='margin-top: 20px;'>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    # Custom colors: cyan, gold, red, win green
    colors = ['#00e5ff', '#ffd700', '#ff4757', '#00ff87', '#a855f7']
    fig_pie = px.pie(players_df, names='position', hole=0.6, title="Position Distribution",
                     color_discrete_sequence=colors)
    fig_pie.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#0d1f3c', width=2)))
    st.plotly_chart(fig_pie, use_container_width=True)
with c2:
    fig_hist = px.histogram(players_df, x='market_value_in_eur', log_y=True, nbins=50,
                            title="Market Value Distribution", color_discrete_sequence=['#00e5ff'])
    st.plotly_chart(fig_hist, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)


# ── PLAYER SEARCH ──
st.markdown("<div id='player-search' class='scroll-section'>", unsafe_allow_html=True)
st.markdown("<h1>Scout a Player</h1>", unsafe_allow_html=True)

search_term = st.text_input("Enter player name:", placeholder="E.g. Messi, Ronaldo")
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
            st.markdown(f"""
            <div class='player-card-header'>
                <div>
                    <h2 class='player-name'>{player_data['name']}</h2>
                    <div style='color: #7a9bb5; font-weight: 600; margin-top: 5px;'>{player_data['country_of_birth']}</div>
                </div>
                <div class='pos-badge'>{player_data['position']}</div>
            </div>
            <h3 style='color: #00ff87; font-size: 28px; margin-bottom: 20px;'>{format_money(player_data['market_value_in_eur'])}</h3>
            
            <table style='width: 100%; color: #e8f4fd;'>
                <tr><td style='color: #7a9bb5; padding-bottom: 8px;'>Games Played</td><td style='text-align: right; font-weight: 700; font-family: "Barlow Condensed", sans-serif; font-size: 20px;'>{player_data['games_played']}</td></tr>
                <tr><td style='color: #7a9bb5; padding-bottom: 8px;'>Total Goals</td><td style='text-align: right; font-weight: 700; font-family: "Barlow Condensed", sans-serif; font-size: 20px;'>{player_data['total_goals']}</td></tr>
                <tr><td style='color: #7a9bb5; padding-bottom: 8px;'>Total Assists</td><td style='text-align: right; font-weight: 700; font-family: "Barlow Condensed", sans-serif; font-size: 20px;'>{player_data['total_assists']}</td></tr>
                <tr><td style='color: #7a9bb5; padding-bottom: 8px;'>Minutes</td><td style='text-align: right; font-weight: 700; font-family: "Barlow Condensed", sans-serif; font-size: 20px;'>{player_data['total_minutes_played']:,}</td></tr>
            </table>
            """, unsafe_allow_html=True)
            
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
                fill='toself', name=player_data['name'], 
                fillcolor='rgba(0, 229, 255, 0.5)', line_color='#ffd700'
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=avg_vals, theta=['Goals', 'Assists', 'Minutes', 'Cards', 'Value'],
                fill='toself', name=f"Avg {player_data['position']}", 
                fillcolor='rgba(122, 155, 181, 0.2)', line_color='#7a9bb5', opacity=0.5
            ))
            
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 1]), bgcolor='rgba(0,0,0,0)'),
                                    showlegend=True, margin=dict(t=20, b=20, l=20, r=20), 
                                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                    font_color='#e8f4fd')
            st.plotly_chart(fig_radar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)


# ── CLUSTER ANALYSIS ──
st.markdown("<div id='cluster-analysis' class='scroll-section'>", unsafe_allow_html=True)
st.markdown("<h1>Cluster Analysis</h1>", unsafe_allow_html=True)

# KMeans Explanation
st.markdown("""
<div class='glass-container' style='margin-bottom: 20px;'>
    <h3 style='color: #ffd700;'>How KMeans Clustering Works</h3>
    <p style='color: #e8f4fd; line-height: 1.6;'>
        Players are grouped into distinct playstyles using the KMeans algorithm.
    </p>
    <ul style='color: #7a9bb5; line-height: 1.6;'>
        <li><strong>Features Used:</strong> Goals, Assists, Minutes Played, and Market Value.</li>
        <li><strong>Standardization:</strong> <code>StandardScaler</code> is applied so that metrics with large scales (like Market Value or Minutes) do not overshadow smaller scale metrics (like Goals).</li>
        <li><strong>Centroids:</strong> The algorithm identifies the center (centroid) of each cluster, representing the "average" archetype for that group.</li>
        <li><strong>Why k=4:</strong> We chose 4 clusters to cleanly segment players into universally recognized tiers (e.g., Elites, Regulars, Squad Players, and Reserves).</li>
    </ul>
</div>
""", unsafe_allow_html=True)

if 'cluster_label' in players_df.columns:
    cluster_summary = players_df.groupby('cluster_label')[['total_goals', 'total_assists', 'total_minutes_played', 'market_value_in_eur']].mean().reset_index()
    total_players = len(players_df)
    
    # Define cluster specifics
    cluster_meta = {
        0: {
            "icon": "⭐", "name": "Elite Superstars",
            "desc": "The highest-performing and most valuable players in the database. They consistently play high minutes, score goals, and have premium market values.",
            "insight": "Target these players as marquee signings. They guarantee output but require massive transfer budgets."
        },
        1: {
            "icon": "⚔️", "name": "First-Team Regulars",
            "desc": "Dependable starters who play significant minutes. While their raw output might not rival the elites, they form the backbone of the squad.",
            "insight": "These are high-value targets for building squad depth and maintaining consistent performance across a long season."
        },
        2: {
            "icon": "🛡️", "name": "Squad Players",
            "desc": "Players with moderate minutes and lower market values. Often younger prospects, rotational options, or players returning from injury.",
            "insight": "Scout this group for hidden gems. There is high potential for return on investment if they can break into the starting XI."
        },
        3: {
            "icon": "⏳", "name": "Fringe/Reserves",
            "desc": "Players with minimal minutes, low output, and low market value. Typically youth academy products or deep reserves.",
            "insight": "Useful for filling out tournament rosters, but unlikely to make an immediate impact on the pitch."
        }
    }
    
    for i in range(4):
        # Fallback if there are fewer than 4 clusters in data
        if i not in cluster_summary['cluster_label'].values:
            continue
            
        c_data = cluster_summary[cluster_summary['cluster_label'] == i].iloc[0]
        c_count = len(players_df[players_df['cluster_label'] == i])
        c_pct = (c_count / total_players) * 100
        
        meta = cluster_meta.get(i, {"icon": "👤", "name": f"Cluster {i}", "desc": "N/A", "insight": "N/A"})
        
        st.markdown(f"""
        <div class='cluster-panel'>
            <div class='cluster-header'>
                <div class='cluster-icon'>{meta['icon']}</div>
                <h3 class='cluster-title'>{meta['name']}</h3>
                <div class='cluster-pct'>~{c_pct:.0f}% players</div>
            </div>
            
            <div class='cluster-desc'>{meta['desc']}</div>
            
            <div class='cluster-stats-grid'>
                <div class='cluster-stat-box'>
                    <div class='cluster-stat-val'>{c_data['total_goals']:.1f}</div>
                    <div class='cluster-stat-lbl'>Avg Goals</div>
                </div>
                <div class='cluster-stat-box'>
                    <div class='cluster-stat-val'>{c_data['total_assists']:.1f}</div>
                    <div class='cluster-stat-lbl'>Avg Assists</div>
                </div>
                <div class='cluster-stat-box'>
                    <div class='cluster-stat-val'>{c_data['total_minutes_played']:.0f}</div>
                    <div class='cluster-stat-lbl'>Avg Minutes</div>
                </div>
                <div class='cluster-stat-box'>
                    <div class='cluster-stat-val'>{format_money(c_data['market_value_in_eur'])}</div>
                    <div class='cluster-stat-lbl'>Avg Value</div>
                </div>
            </div>
            
            <div class='cluster-insight'>
                <strong>💡 WHY THIS CLUSTER MATTERS:</strong><br>
                {meta['insight']}
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.warning("Cluster data not found.")
st.markdown("</div>", unsafe_allow_html=True)


# ── TOP CHARTS ──
st.markdown("<div id='top-charts' class='scroll-section'>", unsafe_allow_html=True)
st.markdown("<h1>Top Charts</h1>", unsafe_allow_html=True)

st.markdown("<div class='glass-container'>", unsafe_allow_html=True)

# Scatter Plot: Goals vs Market Value
st.markdown("<h3>Goals vs Market Value</h3>", unsafe_allow_html=True)
if 'cluster_label' in players_df.columns:
    players_df['cluster_str'] = players_df['cluster_label'].astype(str)
    fig_scatter = px.scatter(players_df, x='market_value_in_eur', y='total_goals', 
                             size='total_minutes_played', color='cluster_str',
                             hover_name='name', log_x=True,
                             color_discrete_sequence=['#00e5ff', '#ffd700', '#ff4757', '#00ff87'])
    
    fig_scatter.update_layout(
        xaxis=dict(gridcolor="rgba(0,229,255,0.2)"),
        yaxis=dict(gridcolor="rgba(0,229,255,0.2)"),
        margin=dict(l=0, r=0, t=30, b=0),
        legend_title_text='Cluster'
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    
st.markdown("<hr style='border-color: rgba(0,229,255,0.15); margin: 30px 0;'>", unsafe_allow_html=True)

# Top 10 Valued Players Bar Chart
st.markdown("<h3>Top 10 Most Valuable Players</h3>", unsafe_allow_html=True)
top10_val = players_df.nlargest(10, 'market_value_in_eur')
fig_bar = px.bar(top10_val, x='name', y='market_value_in_eur', text_auto='.2s')

fig_bar.update_traces(marker_color='#00e5ff', textfont_color='#ffd700', textposition='outside')
fig_bar.update_layout(
    xaxis_title="", 
    yaxis_title="Market Value (€)",
    xaxis=dict(gridcolor="rgba(0,229,255,0.08)"),
    yaxis=dict(gridcolor="rgba(0,229,255,0.08)"),
    margin=dict(l=0, r=0, t=30, b=0)
)
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
