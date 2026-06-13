import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
import os

st.set_page_config(
    page_title="KickStats — WC 2026 Command Center",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;700;900&family=Barlow:wght@400;500;600&display=swap');

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.stApp {
  background-color: #0a1628;
  font-family: 'Barlow', sans-serif;
}

section[data-testid="stSidebar"] {
  background-color: #080f1e;
  border-right: 1px solid rgba(0,229,255,0.1);
}

.stTabs [data-baseweb="tab-list"] {
  background-color: #080f1e;
  border-bottom: 1px solid rgba(0,229,255,0.15);
  gap: 4px;
  padding: 0 8px;
}
.stTabs [data-baseweb="tab"] {
  font-family: 'Barlow Condensed', sans-serif;
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: #7a9bb5;
  background: transparent;
  border: none;
  padding: 10px 18px;
}
.stTabs [aria-selected="true"] {
  color: #00e5ff !important;
  border-bottom: 2px solid #00e5ff !important;
  background: transparent !important;
}

.stSelectbox > div > div {
  background-color: #0d1f3c !important;
  border: 1px solid rgba(0,229,255,0.2) !important;
  border-radius: 6px !important;
  color: #e8f4fd !important;
}

.stButton > button {
  background: linear-gradient(90deg, #00e5ff, #0097b2) !important;
  color: #000 !important;
  font-family: 'Barlow Condensed', sans-serif !important;
  font-weight: 800 !important;
  font-size: 14px !important;
  letter-spacing: 2px !important;
  text-transform: uppercase !important;
  border: none !important;
  border-radius: 4px !important;
  padding: 10px 24px !important;
  transition: all 0.2s ease !important;
}
.stButton > button:hover {
  box-shadow: 0 0 20px rgba(0,229,255,0.5) !important;
  transform: translateY(-1px) !important;
}
.stButton > button:disabled {
  background: #1a2f4a !important;
  color: #7a9bb5 !important;
  box-shadow: none !important;
  transform: none !important;
}

[data-testid="metric-container"] {
  background: #0d1f3c;
  border: 1px solid rgba(0,229,255,0.15);
  border-radius: 8px;
  padding: 12px;
}

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #080f1e; }
::-webkit-scrollbar-thumb { background: rgba(0,229,255,0.3); border-radius: 2px; }

.section-header {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 2px;
  color: #00e5ff;
  text-transform: uppercase;
  margin-bottom: 10px;
}

.lineup-counter-green {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 20px;
  font-weight: 900;
  color: #00ff87;
  letter-spacing: 1px;
}
.lineup-counter-gold {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 20px;
  font-weight: 900;
  color: #ffd700;
  letter-spacing: 1px;
}
.lineup-counter-red {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 20px;
  font-weight: 900;
  color: #ff4757;
  letter-spacing: 1px;
}

.formation-display {
  background: rgba(13,31,60,0.6);
  border: 1px solid rgba(0,229,255,0.2);
  border-radius: 8px;
  padding: 16px;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 13px;
  line-height: 1.8;
  backdrop-filter: blur(12px);
}

.validation-bar {
  background: rgba(13,31,60,0.6);
  border: 1px solid rgba(0,229,255,0.15);
  border-radius: 8px;
  padding: 14px 18px;
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 13px;
  backdrop-filter: blur(12px);
}
</style>
""", unsafe_allow_html=True)

# Inject KickStats Animated Backgrounds
st.markdown("""
<div class='pitch-bg-container'>
    <div class='pitch-grid'></div>
    <div class='stadium-light-1'></div>
    <div class='stadium-light-2'></div>
</div>
""", unsafe_allow_html=True)

# ── HELPERS ────────────────────────────────────────────────────────────────────
def format_money(val):
    try:
        v = float(val)
        if pd.isna(v): return "N/A"
        if v >= 1e6: return f"€{v/1e6:.1f}M"
        if v >= 1e3: return f"€{v/1e3:.0f}K"
        return f"€{int(v)}"
    except: return "N/A"

COUNTRY_FLAGS = {
    'Afghanistan': '🇦🇫', 'Albania': '🇦🇱', 'Algeria': '🇩🇿', 'Angola': '🇦🇴',
    'Argentina': '🇦🇷', 'Australia': '🇦🇺', 'Austria': '🇦🇹', 'Belgium': '🇧🇪',
    'Bolivia': '🇧🇴', 'Bosnia and Herzegovina': '🇧🇦', 'Brazil': '🇧🇷',
    'Cameroon': '🇨🇲', 'Canada': '🇨🇦', 'Cape Verde': '🇨🇻', 'Chile': '🇨🇱',
    'China PR': '🇨🇳', 'Colombia': '🇨🇴', 'Costa Rica': '🇨🇷', 'Croatia': '🇭🇷',
    'Czech Republic': '🇨🇿', 'DR Congo': '🇨🇩', 'Denmark': '🇩🇰', 'Ecuador': '🇪🇨',
    'Egypt': '🇪🇬', 'England': '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'France': '🇫🇷', 'Germany': '🇩🇪',
    'Ghana': '🇬🇭', 'Greece': '🇬🇷', 'Honduras': '🇭🇳', 'Iceland': '🇮🇸',
    'Indonesia': '🇮🇩', 'Iran': '🇮🇷', 'Iraq': '🇮🇶', 'Italy': '🇮🇹',
    'Ivory Coast': '🇨🇮', 'Japan': '🇯🇵', 'Jordan': '🇯🇴', 'Mexico': '🇲🇽',
    'Morocco': '🇲🇦', 'Netherlands': '🇳🇱', 'New Zealand': '🇳🇿', 'Nigeria': '🇳🇬',
    'Panama': '🇵🇦', 'Paraguay': '🇵🇾', 'Peru': '🇵🇪', 'Poland': '🇵🇱',
    'Portugal': '🇵🇹', 'Qatar': '🇶🇦', 'Romania': '🇷🇴', 'Russia': '🇷🇺',
    'Saudi Arabia': '🇸🇦', 'Scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿', 'Senegal': '🇸🇳',
    'Serbia': '🇷🇸', 'Slovakia': '🇸🇰', 'Slovenia': '🇸🇮', 'South Africa': '🇿🇦',
    'South Korea': '🇰🇷', 'Spain': '🇪🇸', 'Sweden': '🇸🇪', 'Switzerland': '🇨🇭',
    'Tunisia': '🇹🇳', 'Turkey': '🇹🇷', 'Ukraine': '🇺🇦', 'United States': '🇺🇸',
    'Uruguay': '🇺🇾', 'Bahrain': '🇧🇭',
    'Haiti': '🇭🇹', 'Norway': '🇳🇴', 'Curaçao': '🇨🇼', 'Uzbekistan': '🇺🇿',
}

def get_flag(country): return COUNTRY_FLAGS.get(country, '⚽')
def team_with_flag(c): return f"{get_flag(c)} {c}"

import plotly.io as pio
_t = pio.templates["plotly_dark"]
_t.layout.paper_bgcolor = "rgba(0,0,0,0)"
_t.layout.plot_bgcolor  = "rgba(0,0,0,0)"
_t.layout.font.color    = "#dce4e5"
_t.layout.xaxis.gridcolor = "rgba(0,218,243,0.1)"
_t.layout.yaxis.gridcolor = "rgba(0,218,243,0.1)"
pio.templates.default = _t

# ── DATA LOADING ───────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    results = pd.read_csv('data/results.csv') if os.path.exists('data/results.csv') else pd.DataFrame()
    if not results.empty:
        results['date'] = pd.to_datetime(results['date'])
    features = pd.read_csv('features.csv') if os.path.exists('features.csv') else pd.DataFrame()
    player_clustered = pd.read_csv('player_clustered.csv') if os.path.exists('player_clustered.csv') else pd.DataFrame()
    return results, features, player_clustered

@st.cache_data
def load_master_players():
    path = 'data/master_players.csv'
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    # Ensure 'name' column exists (used by Player Scout tab)
    if 'name' not in df.columns and 'player_name' in df.columns:
        df['name'] = df['player_name']
    # Ensure 'country_of_birth' exists
    if 'country_of_birth' not in df.columns and 'team' in df.columns:
        df['country_of_birth'] = df['team']
    # Ensure games_played column
    if 'games_played' not in df.columns:
        df['games_played'] = 0
    # Ensure total_minutes_played exists
    if 'total_minutes_played' not in df.columns and 'total_minutes' in df.columns:
        df['total_minutes_played'] = df['total_minutes']
    elif 'total_minutes_played' not in df.columns:
        df['total_minutes_played'] = 0
    # Ensure yellow_cards exists
    if 'yellow_cards' not in df.columns:
        df['yellow_cards'] = 0
    return df

@st.cache_resource
def load_model():
    if os.path.exists('model.pkl'):
        return joblib.load('model.pkl')
    return None

@st.cache_resource
def load_lineup_models():
    out_model = joblib.load('lineup_outcome_model.pkl') if os.path.exists('lineup_outcome_model.pkl') else None
    goals_model = joblib.load('lineup_goals_model.pkl') if os.path.exists('lineup_goals_model.pkl') else None
    return out_model, goals_model

def load_accuracy():
    if os.path.exists('model_accuracy.txt'):
        with open('model_accuracy.txt') as f:
            return float(f.read().strip())
    return None

def load_lineup_accuracy():
    if os.path.exists('lineup_model_accuracy.txt'):
        with open('lineup_model_accuracy.txt') as f:
            return float(f.read().strip())
    return None

results_df, features_df, players_df = load_data()
master_df = load_master_players()
model = load_model()
lineup_model, lineup_goals_model = load_lineup_models()
model_accuracy = load_accuracy()
lineup_model_accuracy = load_lineup_accuracy()

if results_df.empty or players_df.empty:
    st.warning("Data files not found. Please run the pipeline scripts first.")
    st.stop()

wc_results = results_df[results_df['tournament'].str.contains('FIFA World Cup', case=False, na=False)]
wc_finals  = wc_results[(wc_results['tournament'] == 'FIFA World Cup') & (wc_results['date'].dt.year >= 2000)]
wc_teams   = sorted(list(set(wc_finals['home_team'].unique()) | set(wc_finals['away_team'].unique())))

# WC2026 squad teams
squad_teams = sorted(master_df['team'].unique().tolist()) if not master_df.empty else wc_teams

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;gap:14px;padding:18px 0 8px;">
  <div style="font-family:'Barlow Condensed',sans-serif;font-size:36px;font-weight:900;
              color:#00e5ff;letter-spacing:-1px;text-shadow:0 0 20px rgba(0,229,255,0.4);">
    ⚽ KICKSTATS
  </div>
  <div style="font-family:'Barlow Condensed',sans-serif;font-size:14px;font-weight:700;
              color:#7a9bb5;letter-spacing:3px;text-transform:uppercase;padding-top:6px;">
    FIFA World Cup 2026 — Command Center
  </div>
</div>
<hr style="border:none;border-top:1px solid rgba(0,229,255,0.15);margin:0 0 16px;">
""", unsafe_allow_html=True)

# ── TABS ───────────────────────────────────────────────────────────────────────
tab_match, tab_lineup, tab_players, tab_cluster, tab_charts = st.tabs([
    "⚡ MATCH PREDICTOR",
    "🧩 LINEUP PREDICTOR",
    "🔍 PLAYER SCOUT",
    "🔬 CLUSTER ANALYSIS",
    "📊 TOP CHARTS",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — MATCH PREDICTOR
# ══════════════════════════════════════════════════════════════════════════════
with tab_match:
    st.markdown("<div class='scroll-section'>", unsafe_allow_html=True)

    if model_accuracy is not None:
        st.markdown(f"""
        <div style="display:flex;gap:16px;margin-bottom:20px;flex-wrap:wrap;">
          <div class='kpi-card' style="flex:1;min-width:140px;">
            <div class='kpi-value'>{model_accuracy*100:.1f}%</div>
            <div class='kpi-label'>Model Accuracy</div>
          </div>
          <div class='kpi-card' style="flex:1;min-width:140px;">
            <div class='kpi-value'>{len(wc_results)}</div>
            <div class='kpi-label'>WC Matches</div>
          </div>
          <div class='kpi-card' style="flex:1;min-width:140px;">
            <div class='kpi-value'>{len(wc_teams)}</div>
            <div class='kpi-label'>Teams in DB</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
    team_display = [team_with_flag(t) for t in wc_teams]
    col1, col2 = st.columns(2)
    with col1:
        home_sel = st.selectbox("🏠 Home Team", team_display, index=0, key="mp_home")
    with col2:
        away_sel = st.selectbox("✈️ Away Team", team_display, index=min(1, len(team_display)-1), key="mp_away")

    home_team = home_sel.split(' ', 1)[1] if ' ' in home_sel else home_sel
    away_team = away_sel.split(' ', 1)[1] if ' ' in away_sel else away_sel

    if home_team == away_team:
        st.error("⚠️ Home and Away teams must be different!")
    else:
        if st.button("⚡ SIMULATE MATCH", width='stretch', key="sim_btn"):
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

                        h2h = wc_results[
                            ((wc_results['home_team'] == home_team) & (wc_results['away_team'] == away_team)) |
                            ((wc_results['home_team'] == away_team) & (wc_results['away_team'] == home_team))
                        ]

                        if not h2h.empty:
                            home_wins = (
                                sum((h2h['home_team'] == home_team) & (h2h['home_score'] > h2h['away_score'])) +
                                sum((h2h['away_team'] == home_team) & (h2h['away_score'] > h2h['home_score']))
                            )
                            h2h_rate = home_wins / len(h2h)
                        else:
                            h2h_rate = features_df['head_to_head_home_win_rate'].mean()

                        input_data = pd.DataFrame([[h_win_rate, a_win_rate, h_gs, h_gc, a_gs, a_gc, h2h_rate]],
                                                  columns=['home_win_rate','away_win_rate','home_avg_goals_scored',
                                                           'home_avg_goals_conceded','away_avg_goals_scored',
                                                           'away_avg_goals_conceded','head_to_head_home_win_rate'])
                        pred  = model.predict(input_data)[0]
                        probs = model.predict_proba(input_data)[0]
                        classes = list(model.classes_)
                        p_away = probs[classes.index(0)] if 0 in classes else 0
                        p_draw = probs[classes.index(1)] if 1 in classes else 0
                        p_home = probs[classes.index(2)] if 2 in classes else 0

                        hf = get_flag(home_team); af = get_flag(away_team)
                        st.markdown(f"""
                        <div class='hero-vs'>
                          <div style='flex:1;'>
                            <div style='font-size:52px;margin-bottom:8px;'>{hf}</div>
                            <div class='team-name'>{home_team}</div>
                            <div class='team-subtitle'>Win Rate: {h_win_rate*100:.1f}%</div>
                          </div>
                          <div class='vs-badge'>VS</div>
                          <div style='flex:1;'>
                            <div style='font-size:52px;margin-bottom:8px;'>{af}</div>
                            <div class='team-name'>{away_team}</div>
                            <div class='team-subtitle'>Win Rate: {a_win_rate*100:.1f}%</div>
                          </div>
                        </div>
                        """, unsafe_allow_html=True)

                        outcome_map = {
                            2: (f"{home_team} WINS", "result-win"),
                            1: ("DRAW", "result-draw"),
                            0: (f"{away_team} WINS", "result-loss"),
                        }
                        text, cls = outcome_map[pred]
                        st.markdown(f"<div style='text-align:center;margin:12px 0;'><div class='prediction-result {cls}'>{text}</div></div>", unsafe_allow_html=True)

                        st.markdown(f"""
                        <div class='conf-container'>
                          <div class='conf-row'>
                            <div class='conf-label'>WIN</div>
                            <div class='conf-bar-bg'><div class='conf-bar-fill fill-win' style='width:{p_home*100:.1f}%'></div></div>
                            <div class='conf-pct'>{p_home*100:.1f}%</div>
                          </div>
                          <div class='conf-row'>
                            <div class='conf-label'>DRAW</div>
                            <div class='conf-bar-bg'><div class='conf-bar-fill fill-draw' style='width:{p_draw*100:.1f}%'></div></div>
                            <div class='conf-pct'>{p_draw*100:.1f}%</div>
                          </div>
                          <div class='conf-row'>
                            <div class='conf-label'>LOSS</div>
                            <div class='conf-bar-bg'><div class='conf-bar-fill fill-loss' style='width:{p_away*100:.1f}%'></div></div>
                            <div class='conf-pct'>{p_away*100:.1f}%</div>
                          </div>
                        </div>
                        """, unsafe_allow_html=True)

                        st.markdown("<h3>Head-to-Head History</h3>", unsafe_allow_html=True)
                        if h2h.empty:
                            st.info("No World Cup history between these teams.")
                        else:
                            h2h_s = h2h.sort_values('date', ascending=False).head(5)
                            tbl = "<table class='h2h-table'><tr><th>Date</th><th>Tournament</th><th>Home</th><th>Score</th><th>Away</th></tr>"
                            for _, r in h2h_s.iterrows():
                                if r['home_score'] > r['away_score']:
                                    hc = 'h2h-win' if r['home_team'] == home_team else 'h2h-loss'
                                    ac = 'h2h-loss' if r['home_team'] == home_team else 'h2h-win'
                                elif r['home_score'] < r['away_score']:
                                    hc = 'h2h-loss' if r['home_team'] == home_team else 'h2h-win'
                                    ac = 'h2h-win' if r['home_team'] == home_team else 'h2h-loss'
                                else:
                                    hc = ac = 'h2h-draw'
                                tbl += (f"<tr><td>{r['date'].strftime('%Y-%m-%d')}</td><td>{r['tournament']}</td>"
                                        f"<td class='{hc}'>{get_flag(r['home_team'])} {r['home_team']}</td>"
                                        f"<td><strong>{r['home_score']} – {r['away_score']}</strong></td>"
                                        f"<td class='{ac}'>{get_flag(r['away_team'])} {r['away_team']}</td></tr>")
                            tbl += "</table>"
                            st.markdown(tbl, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — LINEUP PREDICTOR (Player Card System)
# ══════════════════════════════════════════════════════════════════════════════
with tab_lineup:
    from player_cards import render_player_card, check_lineup_validity, get_position_group, format_market_value as fmt_val

    if master_df.empty:
        st.warning("⚠️ Master player data not found. Run `python build_profiles.py` first.")
    else:
        # ── Session state setup ────────────────────────────────────────────────
        if 'home_selected' not in st.session_state:
            st.session_state.home_selected = set()
        if 'away_selected' not in st.session_state:
            st.session_state.away_selected = set()
        if 'lineup_home_team' not in st.session_state:
            st.session_state.lineup_home_team = squad_teams[0] if squad_teams else ""
        if 'lineup_away_team' not in st.session_state:
            st.session_state.lineup_away_team = squad_teams[1] if len(squad_teams) > 1 else ""

        # ── Team selector ──────────────────────────────────────────────────────
        st.markdown("""
        <div style="font-family:'Barlow Condensed',sans-serif;font-size:28px;font-weight:900;
                    color:#00e5ff;letter-spacing:-0.5px;margin-bottom:6px;">
          🧩 LINEUP PREDICTOR
        </div>
        <p style="color:#7a9bb5;font-size:14px;margin-bottom:18px;">
          Select 11 players from each squad to build your lineup, then simulate the match outcome.
        </p>
        """, unsafe_allow_html=True)

        if lineup_model_accuracy is not None:
            st.markdown(f"""
            <div style="display:flex;gap:16px;margin-bottom:20px;flex-wrap:wrap;">
              <div class='kpi-card' style="flex:1;min-width:140px;">
                <div class='kpi-value'>{lineup_model_accuracy*100:.1f}%</div>
                <div class='kpi-label'>Lineup Model Accuracy</div>
              </div>
              <div class='kpi-card' style="flex:1;min-width:140px;">
                <div class='kpi-value'>{len(squad_teams)}</div>
                <div class='kpi-label'>WC Squads</div>
              </div>
              <div class='kpi-card' style="flex:1;min-width:140px;">
                <div class='kpi-value'>{len(master_df)}</div>
                <div class='kpi-label'>Total Squad Players</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        tc1, tc2 = st.columns(2)
        with tc1:
            home_opts = [team_with_flag(t) for t in squad_teams]
            prev_home_idx = squad_teams.index(st.session_state.lineup_home_team) if st.session_state.lineup_home_team in squad_teams else 0
            home_team_sel = st.selectbox("🏠 Home Team", home_opts, index=prev_home_idx, key="lu_home_team")
            lu_home = home_team_sel.split(' ', 1)[1] if ' ' in home_team_sel else home_team_sel
        with tc2:
            away_opts = [team_with_flag(t) for t in squad_teams]
            prev_away_idx = squad_teams.index(st.session_state.lineup_away_team) if st.session_state.lineup_away_team in squad_teams else min(1, len(squad_teams)-1)
            away_team_sel = st.selectbox("✈️ Away Team", away_opts, index=prev_away_idx, key="lu_away_team")
            lu_away = away_team_sel.split(' ', 1)[1] if ' ' in away_team_sel else away_team_sel

        # Reset selections when teams change
        if lu_home != st.session_state.lineup_home_team:
            st.session_state.lineup_home_team = lu_home
            st.session_state.home_selected = set()
        if lu_away != st.session_state.lineup_away_team:
            st.session_state.lineup_away_team = lu_away
            st.session_state.away_selected = set()

        if lu_home == lu_away:
            st.error("⚠️ Home and Away teams must be different!")
            st.stop()

        home_squad = master_df[master_df['team'] == lu_home].copy()
        away_squad = master_df[master_df['team'] == lu_away].copy()

        # Sort by overall DESC
        for sq in [home_squad, away_squad]:
            if 'overall' in sq.columns:
                sq.sort_values('overall', ascending=False, inplace=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Two-column squad card grids ────────────────────────────────────────
        left_col, right_col = st.columns(2)

        def render_squad_col(col, squad, selected_set_key, team_name):
            """Render a full squad column with position filters and player cards."""
            with col:
                selected = st.session_state[selected_set_key]
                n_sel = len(selected)

                # Counter
                if n_sel == 11:
                    counter_cls = "lineup-counter-green"
                elif n_sel > 11:
                    counter_cls = "lineup-counter-red"
                else:
                    counter_cls = "lineup-counter-gold"

                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            margin-bottom:12px;padding:10px 14px;
                            background:rgba(13,31,60,0.6);border:1px solid rgba(0,229,255,0.2);
                            border-radius:8px;backdrop-filter:blur(10px);">
                  <div style="font-family:'Barlow Condensed',sans-serif;font-size:20px;
                              font-weight:900;color:#fff;letter-spacing:1px;text-transform:uppercase;">
                    {get_flag(team_name)} {team_name}
                  </div>
                  <div class="{counter_cls}">{n_sel} / 11</div>
                </div>
                """, unsafe_allow_html=True)

                # Position filter
                pos_filter = st.radio(
                    "Filter by position",
                    ["ALL", "GK", "DEF", "MID", "FWD"],
                    horizontal=True,
                    key=f"pos_filter_{selected_set_key}",
                    label_visibility="collapsed",
                )

                if pos_filter != "ALL":
                    display_squad = squad[squad['position'] == pos_filter].copy()
                else:
                    display_squad = squad.copy()

                if display_squad.empty:
                    st.info("No players found for this filter.")
                    return

                # Render cards in 3-column grid
                card_cols = st.columns(3)
                for i, (_, player_row) in enumerate(display_squad.iterrows()):
                    pname = player_row['player_name']
                    is_sel = pname in selected
                    col_idx = i % 3

                    with card_cols[col_idx]:
                        card_html = render_player_card(player_row, is_selected=is_sel, card_id=f"{selected_set_key}_{i}")
                        st.markdown(card_html, unsafe_allow_html=True)

                        btn_label = "✓ SELECTED" if is_sel else "SELECT"
                        btn_key   = f"btn_{selected_set_key}_{pname.replace(' ','_')}_{i}"
                        if st.button(btn_label, key=btn_key, width='stretch'):
                            if is_sel:
                                st.session_state[selected_set_key].discard(pname)
                            elif len(st.session_state[selected_set_key]) < 11:
                                st.session_state[selected_set_key].add(pname)
                            else:
                                st.warning("Already 11 players selected! Deselect one first.")
                            st.rerun()

        render_squad_col(left_col,  home_squad, 'home_selected', lu_home)
        render_squad_col(right_col, away_squad, 'away_selected', lu_away)

        # ── Formation & Validation ─────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<hr style='border:none;border-top:1px solid rgba(0,229,255,0.15);'>", unsafe_allow_html=True)

        home_sel_names = list(st.session_state.home_selected)
        away_sel_names = list(st.session_state.away_selected)

        home_sel_players = [home_squad[home_squad['player_name'] == n].iloc[0].to_dict()
                            for n in home_sel_names if not home_squad[home_squad['player_name'] == n].empty]
        away_sel_players = [away_squad[away_squad['player_name'] == n].iloc[0].to_dict()
                            for n in away_sel_names if not away_squad[away_squad['player_name'] == n].empty]

        home_validity = check_lineup_validity(home_sel_players)
        away_validity = check_lineup_validity(away_sel_players)

        def format_lineup_text(players, team_name):
            groups = {'GK': [], 'DEF': [], 'MID': [], 'FWD': []}
            for p in players:
                g = get_position_group(p.get('position', ''))
                groups[g].append(p.get('player_name', '?'))
            lines = []
            for pos, plist in groups.items():
                if plist:
                    lines.append(f"<span style='color:#7a9bb5;font-size:11px;'>{pos}</span>  "
                                 f"<span style='color:#e8f4fd;'>{' · '.join(plist)}</span>")
            return "<br>".join(lines) if lines else "<span style='color:#7a9bb5;'>No players selected yet.</span>"

        fd1, fd2 = st.columns(2)
        with fd1:
            st.markdown(f"""
            <div class='formation-display'>
              <div style='font-family:"Barlow Condensed",sans-serif;font-size:13px;
                          font-weight:800;color:#00e5ff;letter-spacing:2px;
                          text-transform:uppercase;margin-bottom:10px;'>
                {get_flag(lu_home)} {lu_home} LINEUP
              </div>
              {format_lineup_text(home_sel_players, lu_home)}
            </div>
            """, unsafe_allow_html=True)
        with fd2:
            st.markdown(f"""
            <div class='formation-display'>
              <div style='font-family:"Barlow Condensed",sans-serif;font-size:13px;
                          font-weight:800;color:#00e5ff;letter-spacing:2px;
                          text-transform:uppercase;margin-bottom:10px;'>
                {get_flag(lu_away)} {lu_away} LINEUP
              </div>
              {format_lineup_text(away_sel_players, lu_away)}
            </div>
            """, unsafe_allow_html=True)

        # Validation bar
        def valid_icon(ok): return "✅" if ok else "❌"

        both_valid = home_validity['is_valid'] and away_validity['is_valid']

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class='validation-bar'>
          <div>
            <div style='color:#7a9bb5;font-size:10px;letter-spacing:1px;text-transform:uppercase;'>HOME LINEUP</div>
            <div style='color:#e8f4fd;margin-top:3px;'>
              {valid_icon(home_validity['is_valid'])} {home_validity['message']}
              &nbsp;|&nbsp; GK:{home_validity['gk_count']}
              DEF:{home_validity['def_count']}
              MID:{home_validity['mid_count']}
              FWD:{home_validity['fwd_count']}
            </div>
          </div>
          <div>
            <div style='color:#7a9bb5;font-size:10px;letter-spacing:1px;text-transform:uppercase;'>AWAY LINEUP</div>
            <div style='color:#e8f4fd;margin-top:3px;'>
              {valid_icon(away_validity['is_valid'])} {away_validity['message']}
              &nbsp;|&nbsp; GK:{away_validity['gk_count']}
              DEF:{away_validity['def_count']}
              MID:{away_validity['mid_count']}
              FWD:{away_validity['fwd_count']}
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Predict Button ─────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        predict_btn = st.button(
            "⚡ PREDICT WITH LINEUP",
            width='stretch',
            disabled=not both_valid,
            key="lineup_predict_btn",
        )

        if predict_btn and both_valid:
            with st.spinner("Running lineup-based prediction..."):
                # Compute average stats for each side
                def lineup_avg(players, col, default=70):
                    vals = [p.get(col, np.nan) for p in players]
                    vals = [v for v in vals if not (isinstance(v, float) and np.isnan(v))]
                    return float(np.mean(vals)) if vals else default

                h_ovr = lineup_avg(home_sel_players, 'overall')
                a_ovr = lineup_avg(away_sel_players, 'overall')
                h_atk = lineup_avg(home_sel_players, 'shooting')
                a_atk = lineup_avg(away_sel_players, 'shooting')
                h_def = lineup_avg(home_sel_players, 'defending')
                a_def = lineup_avg(away_sel_players, 'defending')
                h_pac = lineup_avg(home_sel_players, 'pace')
                a_pac = lineup_avg(away_sel_players, 'pace')
                h_pas = lineup_avg(home_sel_players, 'passing')
                a_pas = lineup_avg(away_sel_players, 'passing')
                h_phy = lineup_avg(home_sel_players, 'physic')
                a_phy = lineup_avg(away_sel_players, 'physic')

                # Compute win probability from lineup ratings
                h_star = float(max([p.get('overall', 70) for p in home_sel_players])) if home_sel_players else 70.0
                a_star = float(max([p.get('overall', 70) for p in away_sel_players])) if away_sel_players else 70.0
                
                h_gks = [p for p in home_sel_players if get_position_group(p.get('position', '')) == 'GK']
                h_gk = float(h_gks[0].get('overall', 70) if h_gks else 70)
                a_gks = [p for p in away_sel_players if get_position_group(p.get('position', '')) == 'GK']
                a_gk = float(a_gks[0].get('overall', 70) if a_gks else 70)

                # Get historical win rates for ML model input
                home_latest = features_df[(features_df['home_team'] == lu_home) | (features_df['away_team'] == lu_home)].tail(1)
                away_latest = features_df[(features_df['home_team'] == lu_away) | (features_df['away_team'] == lu_away)].tail(1)
                
                if not home_latest.empty:
                    if home_latest['home_team'].values[0] == lu_home:
                        h_win_rate = float(home_latest['home_win_rate'].values[0])
                    else:
                        h_win_rate = float(home_latest['away_win_rate'].values[0])
                else:
                    h_win_rate = 0.33
                    
                if not away_latest.empty:
                    if away_latest['home_team'].values[0] == lu_away:
                        a_win_rate = float(away_latest['home_win_rate'].values[0])
                    else:
                        a_win_rate = float(away_latest['away_win_rate'].values[0])
                else:
                    a_win_rate = 0.33

                if lineup_model is not None:
                    # Prepare input dataframe matching training features
                    input_data_lu = pd.DataFrame([[
                        h_ovr, h_atk, h_pas, h_def, h_pac, h_star, h_gk,
                        a_ovr, a_atk, a_pas, a_def, a_pac, a_star, a_gk,
                        h_win_rate, a_win_rate
                    ]], columns=[
                        'home_avg_overall', 'home_avg_shooting', 'home_avg_passing',
                        'home_avg_defending', 'home_avg_pace', 'home_star_rating', 'home_gk_rating',
                        'away_avg_overall', 'away_avg_shooting', 'away_avg_passing',
                        'away_avg_defending', 'away_avg_pace', 'away_star_rating', 'away_gk_rating',
                        'home_win_rate', 'away_win_rate'
                    ])
                    pred_lu = lineup_model.predict(input_data_lu)[0]
                    probs_lu = lineup_model.predict_proba(input_data_lu)[0]
                    classes_lu = list(lineup_model.classes_)
                    p_away_win = float(probs_lu[classes_lu.index(0)]) if 0 in classes_lu else 0.0
                    p_draw_lu  = float(probs_lu[classes_lu.index(1)]) if 1 in classes_lu else 0.0
                    p_home_win = float(probs_lu[classes_lu.index(2)]) if 2 in classes_lu else 0.0
                    
                    if pred_lu == 2:
                        result_text, result_cls = f"{lu_home} WINS", "result-win"
                    elif pred_lu == 0:
                        result_text, result_cls = f"{lu_away} WINS", "result-loss"
                    else:
                        result_text, result_cls = "DRAW", "result-draw"
                        
                    pred_goals = float(lineup_goals_model.predict(input_data_lu)[0]) if lineup_goals_model is not None else None
                else:
                    # Fallback to heuristic
                    home_strength = (h_ovr * 0.4 + h_atk * 0.3 + h_def * 0.2 + h_pac * 0.1)
                    away_strength = (a_ovr * 0.4 + a_atk * 0.3 + a_def * 0.2 + a_pac * 0.1)
                    total = home_strength + away_strength
                    draw_factor = 0.22
                    p_home_win = (home_strength / total) * (1 - draw_factor)
                    p_away_win = (away_strength / total) * (1 - draw_factor)
                    p_draw_lu  = draw_factor
                    pred_goals = None
                    
                    if p_home_win > p_away_win and p_home_win > p_draw_lu:
                        result_text, result_cls = f"{lu_home} WINS", "result-win"
                    elif p_away_win > p_home_win and p_away_win > p_draw_lu:
                        result_text, result_cls = f"{lu_away} WINS", "result-loss"
                    else:
                        result_text, result_cls = "DRAW", "result-draw"

                # Hero display
                st.markdown(f"""
                <div class='hero-vs'>
                  <div style='flex:1;'>
                    <div style='font-size:44px;margin-bottom:8px;'>{get_flag(lu_home)}</div>
                    <div class='team-name'>{lu_home}</div>
                    <div class='team-subtitle'>Avg OVR: {h_ovr:.0f}</div>
                  </div>
                  <div class='vs-badge'>VS</div>
                  <div style='flex:1;'>
                    <div style='font-size:44px;margin-bottom:8px;'>{get_flag(lu_away)}</div>
                    <div class='team-name'>{lu_away}</div>
                    <div class='team-subtitle'>Avg OVR: {a_ovr:.0f}</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:center;margin:10px 0;'><div class='prediction-result {result_cls}'>{result_text}</div></div>", unsafe_allow_html=True)
                
                if pred_goals is not None:
                    st.markdown(f"""
                    <div style='text-align:center; margin-bottom: 20px;'>
                      <span style='font-family:"Barlow Condensed",sans-serif; font-size:16px; font-weight:800; color:#ffd700; letter-spacing:1px; background:rgba(255,219,60,0.1); border: 1px solid rgba(255,219,60,0.3); padding:6px 16px; border-radius:4px;'>
                        ⚽ PREDICTED TOTAL GOALS: {pred_goals:.2f}
                      </span>
                    </div>
                    """, unsafe_allow_html=True)

                # Confidence bars
                st.markdown(f"""
                <div class='conf-container'>
                  <div class='conf-row'>
                    <div class='conf-label'>WIN</div>
                    <div class='conf-bar-bg'><div class='conf-bar-fill fill-win' style='width:{p_home_win*100:.1f}%'></div></div>
                    <div class='conf-pct'>{p_home_win*100:.1f}%</div>
                  </div>
                  <div class='conf-row'>
                    <div class='conf-label'>DRAW</div>
                    <div class='conf-bar-bg'><div class='conf-bar-fill fill-draw' style='width:{p_draw_lu*100:.1f}%'></div></div>
                    <div class='conf-pct'>{p_draw_lu*100:.1f}%</div>
                  </div>
                  <div class='conf-row'>
                    <div class='conf-label'>LOSS</div>
                    <div class='conf-bar-bg'><div class='conf-bar-fill fill-loss' style='width:{p_away_win*100:.1f}%'></div></div>
                    <div class='conf-pct'>{p_away_win*100:.1f}%</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # Radar comparison
                st.markdown("<h3 style='margin-top:24px;'>Lineup Radar Comparison</h3>", unsafe_allow_html=True)
                cats = ['Shooting', 'Passing', 'Defending', 'Pace', 'Physic', 'Shooting']
                fig_r = go.Figure()
                fig_r.add_trace(go.Scatterpolar(
                    r=[h_atk, h_pas, h_def, h_pac, h_phy, h_atk],
                    theta=cats, fill='toself', name=lu_home,
                    fillcolor='rgba(0,218,243,0.25)', line_color='#00daf3', line_width=2,
                ))
                fig_r.add_trace(go.Scatterpolar(
                    r=[a_atk, a_pas, a_def, a_pac, a_phy, a_atk],
                    theta=cats, fill='toself', name=lu_away,
                    fillcolor='rgba(255,219,60,0.2)', line_color='#ffdb3c', line_width=2,
                ))
                fig_r.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[40, 100],
                                              gridcolor='rgba(0,218,243,0.1)',
                                              tickfont=dict(color='#7a9bb5', size=10)),
                               bgcolor='rgba(0,0,0,0)'),
                    showlegend=True,
                    margin=dict(t=30, b=30, l=30, r=30),
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#dce4e5',
                    legend=dict(font=dict(family='Barlow Condensed', size=14)),
                )
                st.plotly_chart(fig_r, width='stretch')

                # Stat breakdown cards
                st.markdown("<h3>Lineup Stat Breakdown</h3>", unsafe_allow_html=True)
                sb1, sb2 = st.columns(2)
                def stat_card(team, flag, ovr, atk, pas, dfs, pac, phy):
                    return f"""
                    <div class='glow-card'>
                      <div style='font-family:"Barlow Condensed",sans-serif;font-size:18px;
                                  font-weight:900;color:#fff;margin-bottom:12px;text-transform:uppercase;'>
                        {flag} {team}
                      </div>
                      <div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;'>
                        <div class='cluster-stat-box'><div class='cluster-stat-val'>{ovr:.0f}</div><div class='cluster-stat-lbl'>Avg OVR</div></div>
                        <div class='cluster-stat-box'><div class='cluster-stat-val'>{atk:.0f}</div><div class='cluster-stat-lbl'>Shooting</div></div>
                        <div class='cluster-stat-box'><div class='cluster-stat-val'>{pas:.0f}</div><div class='cluster-stat-lbl'>Passing</div></div>
                        <div class='cluster-stat-box'><div class='cluster-stat-val'>{dfs:.0f}</div><div class='cluster-stat-lbl'>Defending</div></div>
                        <div class='cluster-stat-box'><div class='cluster-stat-val'>{pac:.0f}</div><div class='cluster-stat-lbl'>Pace</div></div>
                        <div class='cluster-stat-box'><div class='cluster-stat-val'>{phy:.0f}</div><div class='cluster-stat-lbl'>Physic</div></div>
                      </div>
                    </div>"""
                with sb1:
                    st.markdown(stat_card(lu_home, get_flag(lu_home), h_ovr, h_atk, h_pas, h_def, h_pac, h_phy), unsafe_allow_html=True)
                with sb2:
                    st.markdown(stat_card(lu_away, get_flag(lu_away), a_ovr, a_atk, a_pas, a_def, a_pac, a_phy), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — PLAYER SCOUT
# ══════════════════════════════════════════════════════════════════════════════
with tab_players:
    st.markdown("<h2>🔍 Player Scout</h2>", unsafe_allow_html=True)

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"<div class='kpi-card'><div class='kpi-value'>{len(players_df):,}</div><div class='kpi-label'>Total Profiles</div></div>", unsafe_allow_html=True)
    with kpi2:
        if 'avg_goals_per_game' in players_df.columns:
            st.markdown(f"<div class='kpi-card'><div class='kpi-value'>{players_df['avg_goals_per_game'].mean():.2f}</div><div class='kpi-label'>Avg Goals/Game</div></div>", unsafe_allow_html=True)
    with kpi3:
        if 'market_value_in_eur' in players_df.columns:
            st.markdown(f"<div class='kpi-card'><div class='kpi-value'>{format_money(players_df['market_value_in_eur'].mean())}</div><div class='kpi-label'>Avg Market Value</div></div>", unsafe_allow_html=True)
    with kpi4:
        if 'position' in players_df.columns:
            st.markdown(f"<div class='kpi-card'><div class='kpi-value'>{players_df['position'].mode()[0]}</div><div class='kpi-label'>Top Position</div></div>", unsafe_allow_html=True)

    st.markdown("<div class='glass-container' style='margin-top:20px;'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        colors = ['#00daf3', '#ffdb3c', '#ffb4ab', '#00ff87', '#a855f7']
        fig_pie = px.pie(players_df, names='position', hole=0.6, title="Position Distribution",
                         color_discrete_sequence=colors)
        fig_pie.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#0d1f3c', width=2)))
        st.plotly_chart(fig_pie, width='stretch')
    with c2:
        if 'market_value_in_eur' in players_df.columns:
            fig_hist = px.histogram(players_df, x='market_value_in_eur', log_y=True, nbins=50,
                                    title="Market Value Distribution", color_discrete_sequence=['#00daf3'])
            st.plotly_chart(fig_hist, width='stretch')
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<h3 style='margin-top:24px;'>Search a Player</h3>", unsafe_allow_html=True)
    search_term = st.text_input("Enter player name:", placeholder="E.g. Messi, Ronaldo", key="scout_search")
    if search_term:
        matches = players_df[players_df['name'].str.contains(search_term, case=False, na=False)]
        if matches.empty:
            st.warning("No players found matching that criteria.")
        else:
            selected_name = st.selectbox("Select a match:", matches['name'].tolist(), key="scout_sel")
            player_data   = matches[matches['name'] == selected_name].iloc[0]

            st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
            pc1, pc2 = st.columns([1, 2])
            with pc1:
                country = player_data.get('country_of_birth', 'N/A')
                pos     = player_data.get('position', 'N/A')
                mval    = format_money(player_data.get('market_value_in_eur', None))
                games   = player_data.get('games_played', 0)
                goals   = player_data.get('total_goals', 0)
                assists = player_data.get('total_assists', 0)
                minutes = player_data.get('total_minutes_played', 0)
                st.markdown(f"""
                <div class='player-card-header'>
                  <div>
                    <h2 class='player-name'>{player_data['name']}</h2>
                    <div style='color:#7a9bb5;font-weight:600;margin-top:5px;'>{country}</div>
                  </div>
                  <div class='pos-badge'>{pos}</div>
                </div>
                <h3 style='color:#00ff87;font-size:28px;margin-bottom:20px;'>{mval}</h3>
                <table style='width:100%;color:#e8f4fd;font-family:"Barlow Condensed",sans-serif;'>
                  <tr><td style='color:#7a9bb5;padding-bottom:8px;'>Games Played</td>
                      <td style='text-align:right;font-weight:700;font-size:22px;'>{int(games) if not pd.isna(games) else 'N/A'}</td></tr>
                  <tr><td style='color:#7a9bb5;padding-bottom:8px;'>Total Goals</td>
                      <td style='text-align:right;font-weight:700;font-size:22px;color:#00ff87;'>{int(goals) if not pd.isna(goals) else 'N/A'}</td></tr>
                  <tr><td style='color:#7a9bb5;padding-bottom:8px;'>Total Assists</td>
                      <td style='text-align:right;font-weight:700;font-size:22px;color:#00daf3;'>{int(assists) if not pd.isna(assists) else 'N/A'}</td></tr>
                  <tr><td style='color:#7a9bb5;padding-bottom:8px;'>Minutes Played</td>
                       <td style='text-align:right;font-weight:700;font-size:22px;'>{f"{int(minutes):,}" if not pd.isna(minutes) else 'N/A'}</td></tr>
                </table>
                """, unsafe_allow_html=True)
            with pc2:
                stats = ['total_goals', 'total_assists', 'total_minutes_played', 'yellow_cards', 'market_value_in_eur']
                stats = [s for s in stats if s in players_df.columns and s in player_data.index]
                pos_df = players_df[players_df['position'] == player_data['position']]
                p_vals, avg_vals = [], []
                for stat in stats:
                    max_v = pos_df[stat].max(); min_v = pos_df[stat].min()
                    if max_v == min_v:
                        p_vals.append(0); avg_vals.append(0)
                    else:
                        p_vals.append((player_data[stat] - min_v) / (max_v - min_v))
                        avg_vals.append((pos_df[stat].mean() - min_v) / (max_v - min_v))
                theta_labels = ['Goals', 'Assists', 'Minutes', 'Cards', 'Value'][:len(stats)]
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(r=p_vals, theta=theta_labels,
                    fill='toself', name=player_data['name'],
                    fillcolor='rgba(0,218,243,0.4)', line_color='#ffdb3c', line_width=2))
                fig_radar.add_trace(go.Scatterpolar(r=avg_vals, theta=theta_labels,
                    fill='toself', name=f"Avg {player_data['position']}",
                    fillcolor='rgba(132,147,150,0.2)', line_color='#849396', opacity=0.6))
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=False, range=[0,1]), bgcolor='rgba(0,0,0,0)'),
                    showlegend=True, margin=dict(t=20,b=20,l=20,r=20),
                    paper_bgcolor='rgba(0,0,0,0)', font_color='#e8f4fd',
                )
                st.plotly_chart(fig_radar, width='stretch')
            st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — CLUSTER ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tab_cluster:
    st.markdown("<h2>🔬 Cluster Analysis</h2>", unsafe_allow_html=True)
    st.markdown("""
    <div class='glass-container' style='margin-bottom:20px;'>
      <h3 style='color:#ffd700;'>How KMeans Clustering Works</h3>
      <p style='color:#e8f4fd;line-height:1.7;'>
        Players are grouped into distinct playstyle tiers using the KMeans algorithm applied to Goals, Assists, Minutes Played, and Market Value.
      </p>
      <ul style='color:#7a9bb5;line-height:1.8;'>
        <li><strong style='color:#dce4e5;'>Standardization:</strong> <code>StandardScaler</code> ensures all features contribute equally.</li>
        <li><strong style='color:#dce4e5;'>Centroids:</strong> The algorithm identifies the "average archetype" for each cluster.</li>
        <li><strong style='color:#dce4e5;'>Why k=4:</strong> Cleanly segments players into Elite, Regular, Squad, and Reserve tiers.</li>
      </ul>
    </div>
    """, unsafe_allow_html=True)

    if 'cluster_label' in players_df.columns:
        cluster_summary = players_df.groupby('cluster_label')[['total_goals','total_assists','total_minutes_played','market_value_in_eur']].mean().reset_index()
        total_players   = len(players_df)
        cluster_meta    = {
            "Clinical Striker": {"icon":"⭐","name":"Clinical Striker","desc":"High-efficiency goal scorers who convert chances at a premium rate. They are the primary offensive focal point.","insight":"Essential for winning tight games. Ensure they have service from playmakers."},
            "Playmaker": {"icon":"⚔️","name":"Playmaker","desc":"Creative engine room players with high assist rates. They excel at key passes and final-third creation.","insight":"Pair with clinical strikers to maximize offensive output."},
            "Workhorse": {"icon":"🛡️","name":"Workhorse","desc":"High-minute, high-durability players. They form the physical and structural spine of the team.","insight":"Excellent for maintaining stability and structural integrity over 90 minutes."},
            "Rotation Player": {"icon":"⏳","name":"Rotation Player","desc":"Valuable depth options with moderate output and minutes. Useful for squad rotation and load management.","insight":"Good for squad depth, but unlikely to carry the team on their own."},
        }
        for label in ["Clinical Striker", "Playmaker", "Workhorse", "Rotation Player"]:
            if label not in cluster_summary['cluster_label'].values: continue
            c_data  = cluster_summary[cluster_summary['cluster_label'] == label].iloc[0]
            c_count = len(players_df[players_df['cluster_label'] == label])
            c_pct   = (c_count / total_players) * 100
            meta    = cluster_meta.get(label, {"icon":"👤","name":label,"desc":"N/A","insight":"N/A"})
            st.markdown(f"""
            <div class='cluster-panel'>
              <div class='cluster-header'>
                <div class='cluster-icon'>{meta['icon']}</div>
                <h3 class='cluster-title'>{meta['name']}</h3>
                <div class='cluster-pct'>~{c_pct:.0f}% players</div>
              </div>
              <div class='cluster-desc'>{meta['desc']}</div>
              <div class='cluster-stats-grid'>
                <div class='cluster-stat-box'><div class='cluster-stat-val'>{c_data['total_goals']:.1f}</div><div class='cluster-stat-lbl'>Avg Goals</div></div>
                <div class='cluster-stat-box'><div class='cluster-stat-val'>{c_data['total_assists']:.1f}</div><div class='cluster-stat-lbl'>Avg Assists</div></div>
                <div class='cluster-stat-box'><div class='cluster-stat-val'>{c_data['total_minutes_played']:.0f}</div><div class='cluster-stat-lbl'>Avg Minutes</div></div>
                <div class='cluster-stat-box'><div class='cluster-stat-val'>{format_money(c_data['market_value_in_eur'])}</div><div class='cluster-stat-lbl'>Avg Value</div></div>
              </div>
              <div class='cluster-insight'><strong>💡 WHY THIS CLUSTER MATTERS:</strong><br>{meta['insight']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("Cluster data not found. Run `python cluster_players.py` first.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — TOP CHARTS
# ══════════════════════════════════════════════════════════════════════════════
with tab_charts:
    st.markdown("<h2>📊 Top Charts</h2>", unsafe_allow_html=True)
    st.markdown("<div class='glass-container'>", unsafe_allow_html=True)

    st.markdown("<h3>Goals vs Market Value</h3>", unsafe_allow_html=True)
    if 'cluster_label' in players_df.columns:
        players_df['cluster_str'] = players_df['cluster_label'].astype(str)
        fig_sc = px.scatter(players_df, x='market_value_in_eur', y='total_goals',
                            size='total_minutes_played', color='cluster_str',
                            hover_name='name', log_x=True,
                            color_discrete_sequence=['#00daf3','#ffdb3c','#ffb4ab','#00ff87'])
        fig_sc.update_layout(
            xaxis=dict(gridcolor="rgba(0,218,243,0.1)"),
            yaxis=dict(gridcolor="rgba(0,218,243,0.1)"),
            margin=dict(l=0,r=0,t=30,b=0), legend_title_text='Cluster')
        st.plotly_chart(fig_sc, width='stretch')

    st.markdown("<hr style='border:none;border-top:1px solid rgba(0,229,255,0.15);margin:24px 0;'>", unsafe_allow_html=True)

    st.markdown("<h3>Top 10 Most Valuable Players</h3>", unsafe_allow_html=True)
    top10 = players_df.nlargest(10, 'market_value_in_eur')
    fig_bar = px.bar(top10, x='name', y='market_value_in_eur', text_auto='.2s')
    fig_bar.update_traces(marker_color='#00daf3', textfont_color='#ffdb3c', textposition='outside')
    fig_bar.update_layout(
        xaxis_title="", yaxis_title="Market Value (€)",
        xaxis=dict(gridcolor="rgba(0,218,243,0.1)"),
        yaxis=dict(gridcolor="rgba(0,218,243,0.1)"),
        margin=dict(l=0,r=0,t=30,b=0))
    st.plotly_chart(fig_bar, width='stretch')

    st.markdown("<hr style='border:none;border-top:1px solid rgba(0,229,255,0.15);margin:24px 0;'>", unsafe_allow_html=True)

    # WC 2026 Team Strength chart from team_profiles
    tp_path = 'data/team_profiles.csv'
    if os.path.exists(tp_path):
        tp = pd.read_csv(tp_path).nlargest(20, 'team_avg_overall')
        st.markdown("<h3>WC 2026 Team Strength Rankings</h3>", unsafe_allow_html=True)
        fig_team = px.bar(tp, x='team_avg_overall', y='team',
                          orientation='h', text='team_avg_overall',
                          color='team_avg_overall',
                          color_continuous_scale=[[0,'#0d1f3c'],[0.5,'#00daf3'],[1,'#ffd700']])
        fig_team.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig_team.update_layout(
            xaxis=dict(range=[60,100], gridcolor="rgba(0,218,243,0.1)"),
            yaxis=dict(autorange='reversed'),
            margin=dict(l=0,r=60,t=20,b=0),
            showlegend=False, coloraxis_showscale=False,
        )
        st.plotly_chart(fig_team, width='stretch')

    st.markdown("</div>", unsafe_allow_html=True)
