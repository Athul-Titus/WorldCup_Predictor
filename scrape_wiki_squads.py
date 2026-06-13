"""
scrape_wiki_squads.py — Scrape ALL 48 official WC 2026 squads from Wikipedia.
Downloads the full page and parses all squad tables.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os

URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads"
print(f"Fetching {URL}...")
resp = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0 KickStats/1.0'})
resp.raise_for_status()
print(f"Downloaded {len(resp.text)} bytes")

soup = BeautifulSoup(resp.text, 'html.parser')

# The page structure:
# h2 > Group X
#   h3 > Team Name
#     table.wikitable.sortable > squad table

# Find all tables
all_tables = soup.find_all('table', class_='wikitable')
print(f"Found {len(all_tables)} wikitable elements")

# Strategy: walk through all h3 elements (team names) and find their associated table
all_h3 = soup.find_all('h3')
print(f"Found {len(all_h3)} h3 elements")

# Also grab h2 for groups
all_h2 = soup.find_all('h2')

# Map position codes
def map_position(pos_text):
    pos = pos_text.upper().strip()
    # Remove leading numbers like '1GK' -> 'GK'
    pos = re.sub(r'^\d+', '', pos)
    if pos in ('GK',):
        return 'GK'
    elif pos in ('DF', 'CB', 'LB', 'RB', 'LWB', 'RWB'):
        return 'DEF'
    elif pos in ('MF', 'CM', 'CDM', 'CAM', 'LM', 'RM', 'DM', 'AM'):
        return 'MID'
    elif pos in ('FW', 'ST', 'CF', 'LW', 'RW', 'SS'):
        return 'FWD'
    return 'MID'

# Track current group
rows = []
current_group = ''
teams_found = []

for h3 in all_h3:
    # Get team name text
    team_name = h3.get_text(strip=True)
    # Clean up: remove [edit] links
    team_name = re.sub(r'\[.*?\]', '', team_name).strip()
    
    # Skip non-team headings
    skip_keywords = ['Age', 'Player representation', 'Average age', 'Coach', 'Statistics',
                     'References', 'External links', 'Notes', 'See also', 'Contents']
    if any(kw in team_name for kw in skip_keywords):
        continue
    
    # Find the group this belongs to (previous h2)
    prev_h2 = h3.find_previous('h2')
    if prev_h2:
        group_text = prev_h2.get_text(strip=True)
        group_text = re.sub(r'\[.*?\]', '', group_text).strip()
        if group_text.startswith('Group'):
            current_group = group_text
    
    # Find the next table after this h3
    table = h3.find_next('table', class_='wikitable')
    if table is None:
        continue
    
    # Make sure this table is between this h3 and the next h3
    next_h3 = h3.find_next('h3')
    if next_h3:
        # Check if table comes before next h3 in document order
        table_pos = str(table.sourceline) if hasattr(table, 'sourceline') else ''
        # Simpler: check if our table is a sibling/descendant between h3s
        pass  # We'll just trust find_next works
    
    # Parse table rows
    trs = table.find_all('tr')
    if len(trs) < 2:
        continue
    
    # Get header row
    headers = []
    for th in trs[0].find_all(['th']):
        headers.append(th.get_text(strip=True).lower())
    
    team_players = []
    for tr in trs[1:]:
        cells = tr.find_all(['td', 'th'])
        if len(cells) < 3:
            continue
        
        # Find position and name columns by header
        pos_idx = None
        name_idx = None
        caps_idx = None
        goals_idx = None
        club_idx = None
        
        for i, h in enumerate(headers):
            if h == 'pos.' or h == 'pos':
                pos_idx = i
            elif 'player' in h or 'name' in h:
                name_idx = i
            elif h == 'caps':
                caps_idx = i
            elif h == 'goals':
                goals_idx = i
            elif h == 'club':
                club_idx = i
        
        # Fallback: typical layout is No., Pos., Player, DOB, Caps, Goals, Club
        if pos_idx is None:
            pos_idx = 1
        if name_idx is None:
            name_idx = 2
        
        if len(cells) <= max(pos_idx, name_idx):
            continue
        
        # Get player name
        name_cell = cells[name_idx]
        # Try to get from link first
        link = name_cell.find('a')
        if link:
            pname = link.get_text(strip=True)
        else:
            pname = name_cell.get_text(strip=True)
        
        # Clean name
        pname = re.sub(r'\(.*?\)', '', pname).strip()
        pname = re.sub(r'\[.*?\]', '', pname).strip()
        pname = pname.replace('(captain)', '').replace('(c)', '').strip()
        
        if not pname or pname.isdigit() or len(pname) < 2:
            continue
        
        # Get position
        pos_text = cells[pos_idx].get_text(strip=True)
        position = map_position(pos_text)
        
        # Get caps
        caps = 0
        if caps_idx is not None and caps_idx < len(cells):
            try:
                caps = int(re.sub(r'\D', '', cells[caps_idx].get_text(strip=True)) or '0')
            except:
                caps = 0
        
        # Get club
        club = ''
        if club_idx is not None and club_idx < len(cells):
            club_cell = cells[club_idx]
            club_link = club_cell.find('a')
            if club_link:
                club = club_link.get_text(strip=True)
            else:
                club = club_cell.get_text(strip=True)
        
        team_players.append({
            'player_name': pname,
            'team': team_name,
            'position': position,
            'caps': caps,
            'club': club,
            'group': current_group,
        })
    
    if team_players:
        teams_found.append(team_name)
        rows.extend(team_players)
        print(f"  {current_group} | {team_name}: {len(team_players)} players")

print(f"\n{'='*50}")
print(f"Total teams: {len(teams_found)}")
print(f"Total players: {len(rows)}")

# Save
df = pd.DataFrame(rows)
os.makedirs('data', exist_ok=True)
df.to_csv('data/wc2026_squads_new.csv', index=False)
print(f"\nSaved: data/wc2026_squads_new.csv")
print(f"\nAll teams ({len(teams_found)}):")
for t in sorted(teams_found):
    print(f"  {t}")
