"""
player_cards.py — Reusable player card components for the WC 2026 Lineup Predictor.
Contains ONLY helper functions. No Streamlit pages.
"""
import pandas as pd
import numpy as np
import urllib.parse


# ── POSITION HELPERS ─────────────────────────────────────────────────────────

def get_position_group(position_str: str) -> str:
    """Map raw position string to display group label."""
    if not position_str or pd.isna(position_str):
        return "MID"
    pos = str(position_str).upper().strip()
    if pos in ("GK",):
        return "GK"
    if pos in ("CB", "LB", "RB", "LWB", "RWB", "DEF"):
        return "DEF"
    if pos in ("CM", "CDM", "CAM", "LM", "RM", "MID", "DM", "AM"):
        return "MID"
    if pos in ("ST", "CF", "LW", "RW", "FWD", "ATT", "SS"):
        return "FWD"
    # default to MID
    return "MID"


def format_market_value(value) -> str:
    """Format a raw market value number into a readable string."""
    try:
        v = float(value)
        if pd.isna(v):
            return "N/A"
        if v >= 1_000_000:
            return f"€{v / 1_000_000:.1f}M"
        if v >= 1_000:
            return f"€{v / 1_000:.0f}K"
        return f"€{int(v)}"
    except (TypeError, ValueError):
        return "N/A"


def check_lineup_validity(selected_players_list: list) -> dict:
    """
    Validate a lineup selection.
    Returns a dict with validity info and counts.
    """
    counts = {"GK": 0, "DEF": 0, "MID": 0, "FWD": 0}
    for p in selected_players_list:
        pos = get_position_group(p.get("position", ""))
        counts[pos] = counts.get(pos, 0) + 1

    total = len(selected_players_list)
    is_valid = (total == 11) and (counts["GK"] >= 1)

    if total < 11:
        message = f"Select {11 - total} more player{'s' if 11 - total > 1 else ''}."
    elif total > 11:
        message = f"{total - 11} too many players selected."
    elif counts["GK"] == 0:
        message = "Lineup must include at least 1 goalkeeper."
    else:
        message = "✓ Valid lineup!"

    return {
        "is_valid": is_valid,
        "has_gk": counts["GK"] >= 1,
        "gk_count": counts["GK"],
        "def_count": counts["DEF"],
        "mid_count": counts["MID"],
        "fwd_count": counts["FWD"],
        "total": total,
        "message": message,
    }


# ── CARD RENDERER ─────────────────────────────────────────────────────────────

_POS_COLORS = {
    "GK":  ("rgba(255,215,0,0.18)", "#ffd700"),
    "DEF": ("rgba(0,218,243,0.15)", "#00daf3"),
    "MID": ("rgba(0,255,135,0.15)", "#00ff87"),
    "FWD": ("rgba(255,71,87,0.15)",  "#ff4757"),
}


def render_player_card(player_row, is_selected: bool = False, card_id: str = "") -> str:
    """
    Build and return an HTML string for a single player card.

    Parameters
    ----------
    player_row : dict or pandas Series
        One row from master_players.csv (or equivalent dict).
    is_selected : bool
        Whether the player is currently in the selected lineup.
    card_id : str
        Unique identifier used for the select button's id attribute.
    """
    if hasattr(player_row, 'to_dict'):
        p = player_row.to_dict()
    else:
        p = dict(player_row)

    # ── Basic info ──────────────────────────────────────────────────────────
    name       = str(p.get("player_name", "Unknown")).upper()
    pos_raw    = str(p.get("position", "MID"))
    pos_group  = get_position_group(pos_raw)
    # Use UI Avatars as default (always works, no broken images)
    _default_avatar = f"https://ui-avatars.com/api/?name={urllib.parse.quote(name)}&background=0d1f3c&color=00e5ff&size=120&bold=true&rounded=true"
    photo_url  = p.get("photo_url") or _default_avatar

    # ── FC25 stats ──────────────────────────────────────────────────────────
    def _stat(key, default=0):
        v = p.get(key)
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return int(default)
        return int(v)

    ovr  = _stat("overall",  72)
    pac  = _stat("pace",     65)
    sho  = _stat("shooting", 50)
    dri  = _stat("dribbling",65)
    dfs  = _stat("defending",50)
    phy  = _stat("physic",   65)
    pas  = _stat("passing",  60)

    # ── Transfermarkt stats ──────────────────────────────────────────────────
    goals   = _stat("total_goals",   0)
    assists = _stat("total_assists",  0)
    mktval  = format_market_value(p.get("market_value_in_eur"))

    # ── Colors ──────────────────────────────────────────────────────────────
    pos_bg, pos_color = _POS_COLORS.get(pos_group, ("rgba(180,180,180,0.15)", "#aaa"))

    if is_selected:
        card_border = "2px solid #00e5ff"
        card_bg     = "#0f2548"
        card_shadow = "0 0 18px rgba(0,229,255,0.35)"
        ring_color  = "#ffd700"
        btn_bg      = "#00ff87"
        btn_text    = "✓ SELECTED"
    else:
        card_border = "1px solid rgba(0,229,255,0.2)"
        card_bg     = "#0d1f3c"
        card_shadow = "0 4px 16px rgba(0,0,0,0.4)"
        ring_color  = "#00e5ff"
        btn_bg      = "#00e5ff"
        btn_text    = "SELECT"

    # ── Overall color ────────────────────────────────────────────────────────
    if ovr >= 85:
        ovr_color = "#ffd700"
    elif ovr >= 75:
        ovr_color = "#00e5ff"
    else:
        ovr_color = "#adc8e0"

    # ── Render HTML ──────────────────────────────────────────────────────────
    html = f"""
<div style="
    background:{card_bg};
    border:{card_border};
    border-radius:12px;
    padding:14px 10px;
    text-align:center;
    box-shadow:{card_shadow};
    transition:all 0.25s ease;
    font-family:'Barlow Condensed',sans-serif;
    width:100%;
    box-sizing:border-box;
    margin-bottom:8px;
">
  <!-- Photo -->
  <img src="{photo_url}"
       onerror="this.src='https://ui-avatars.com/api/?name={name}&background=0d1f3c&color=00e5ff&size=120&bold=true&rounded=true'"
       style="width:80px;height:80px;border-radius:50%;object-fit:cover;
              border:3px solid {ring_color};display:block;margin:0 auto 8px;
              background:#151d1e;">

  <!-- Position badge + OVR -->
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
    <span style="
      background:{pos_bg};color:{pos_color};
      font-size:10px;font-weight:700;letter-spacing:1.2px;
      padding:2px 7px;border-radius:3px;border:1px solid {pos_color}44;">
      {pos_group}
    </span>
    <span style="font-size:13px;color:{ovr_color};font-weight:700;">
      OVR <strong style="font-size:16px;">{ovr}</strong>
    </span>
  </div>

  <!-- Player name -->
  <div style="font-size:13px;font-weight:900;color:#fff;
              text-transform:uppercase;margin:4px 0 8px;
              line-height:1.2;word-break:break-word;">
    {name}
  </div>

  <!-- Divider -->
  <hr style="border:none;border-top:1px solid rgba(0,229,255,0.12);margin:6px 0;">

  <!-- Stats row 1: PAC SHO DRI -->
  <div style="display:flex;justify-content:space-around;margin:4px 0;">
    <div>
      <div style="font-size:9px;color:#7a9bb5;letter-spacing:.5px;">⚡ PAC</div>
      <div style="font-size:14px;color:#e8f4fd;font-weight:700;">{pac}</div>
    </div>
    <div>
      <div style="font-size:9px;color:#7a9bb5;letter-spacing:.5px;">🎯 SHO</div>
      <div style="font-size:14px;color:#e8f4fd;font-weight:700;">{sho}</div>
    </div>
    <div>
      <div style="font-size:9px;color:#7a9bb5;letter-spacing:.5px;">🎨 DRI</div>
      <div style="font-size:14px;color:#e8f4fd;font-weight:700;">{dri}</div>
    </div>
  </div>

  <!-- Stats row 2: DEF PHY PAS -->
  <div style="display:flex;justify-content:space-around;margin:4px 0 8px;">
    <div>
      <div style="font-size:9px;color:#7a9bb5;letter-spacing:.5px;">🛡️ DEF</div>
      <div style="font-size:14px;color:#e8f4fd;font-weight:700;">{dfs}</div>
    </div>
    <div>
      <div style="font-size:9px;color:#7a9bb5;letter-spacing:.5px;">💪 PHY</div>
      <div style="font-size:14px;color:#e8f4fd;font-weight:700;">{phy}</div>
    </div>
    <div>
      <div style="font-size:9px;color:#7a9bb5;letter-spacing:.5px;">📤 PAS</div>
      <div style="font-size:14px;color:#e8f4fd;font-weight:700;">{pas}</div>
    </div>
  </div>

  <!-- Divider -->
  <hr style="border:none;border-top:1px solid rgba(0,229,255,0.08);margin:6px 0;">

  <!-- Goals / Assists -->
  <div style="font-size:11px;color:#adc8e0;margin-bottom:3px;">
    ⚽ <strong>{goals}</strong> goals &nbsp;|&nbsp; 🅰️ <strong>{assists}</strong> assists
  </div>
  <!-- Market Value -->
  <div style="font-size:10px;color:#7a9bb5;margin-bottom:8px;">
    💰 {mktval}
  </div>

  <!-- Select Button (visual only – Streamlit handles interaction) -->
  <div style="
    background:{btn_bg};
    color:#000;
    font-family:'Barlow Condensed',sans-serif;
    font-size:11px;
    font-weight:800;
    letter-spacing:1.5px;
    padding:6px 0;
    border-radius:4px;
    cursor:pointer;
    text-transform:uppercase;
  ">{btn_text}</div>
</div>
"""
    return html
