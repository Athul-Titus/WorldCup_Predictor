"""
parse_wiki_squads.py — Parse the official FIFA WC 2026 squads from downloaded Wikipedia HTML.
Extracts all 48 teams with player names and positions.
"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

from bs4 import BeautifulSoup
import pandas as pd
import re

HTML_PATH = r'C:\Users\athul\.gemini\antigravity-ide\brain\522435ca-9e60-4fe6-9208-30a7b41abfef\.system_generated\steps\52\content.md'

with open(HTML_PATH, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

# Find all squad tables - they are .wikitable.sortable
tables = soup.find_all('table', class_='sortable')
print(f"Found {len(tables)} sortable tables")

# Each team's squad is preceded by an h3 heading with the team name
# Let's find all h3 span.mw-headline elements and their following tables
headings = soup.find_all('span', class_='mw-headline')

teams_data = {}
current_group = None

for heading in headings:
    text = heading.get_text(strip=True)
    
    # Check if it's a group heading
    if text.startswith('Group '):
        current_group = text
        continue
    
    # Skip non-team headings
    if text in ('Age', 'Player representation by club', 'Player representation by league system', 
                'Player representation by club confederation', 'Average age of squads',
                'Coach representation by country', 'Statistics', 'References', 'External links',
                'Notes', 'See also'):
        continue
    
    # Find the next table after this heading
    parent = heading.parent  # h3 or h2
    if parent is None:
        continue
    
    # Walk siblings to find the next table
    sibling = parent.find_next_sibling()
    table = None
    while sibling:
        if sibling.name == 'table':
            table = sibling
            break
        if sibling.name in ('h2', 'h3'):
            break  # Hit next section
        sibling = sibling.find_next_sibling()
    
    if table is None:
        continue
    
    # Parse the table
    rows = table.find_all('tr')
    if len(rows) < 2:
        continue
    
    # Get headers
    headers = []
    header_row = rows[0]
    for th in header_row.find_all(['th']):
        headers.append(th.get_text(strip=True).lower())
    
    players = []
    for row in rows[1:]:
        cells = row.find_all(['td', 'th'])
        if len(cells) < 3:
            continue
        
        # Try to extract player name and position
        # Typical columns: #, Pos., Player, Date of birth (age), Caps, Club
        player_data = {}
        for i, cell in enumerate(cells):
            if i < len(headers):
                player_data[headers[i]] = cell.get_text(strip=True)
        
        # Extract player name - usually in a link
        name_cell = None
        for i, h in enumerate(headers):
            if 'player' in h or 'name' in h:
                name_cell = cells[i]
                break
        
        if name_cell is None and len(cells) >= 3:
            name_cell = cells[2]  # Usually 3rd column
        
        if name_cell:
            # Get the player name from the link if available
            link = name_cell.find('a')
            if link:
                pname = link.get_text(strip=True)
            else:
                pname = name_cell.get_text(strip=True)
            
            # Clean up name
            pname = re.sub(r'\(.*?\)', '', pname).strip()
            pname = re.sub(r'\[.*?\]', '', pname).strip()
            
            if not pname or pname.isdigit():
                continue
            
            # Get position
            pos = ''
            for i, h in enumerate(headers):
                if 'pos' in h:
                    pos = cells[i].get_text(strip=True)
                    break
            if not pos and len(cells) >= 2:
                pos = cells[1].get_text(strip=True)
            
            # Map position
            pos_upper = pos.upper().strip()
            if pos_upper in ('GK', '1GK'):
                mapped_pos = 'GK'
            elif pos_upper in ('DF', 'CB', 'LB', 'RB', 'LWB', 'RWB'):
                mapped_pos = 'DEF'
            elif pos_upper in ('MF', 'CM', 'CDM', 'CAM', 'LM', 'RM', 'DM', 'AM'):
                mapped_pos = 'MID'
            elif pos_upper in ('FW', 'ST', 'CF', 'LW', 'RW', 'SS'):
                mapped_pos = 'FWD'
            else:
                mapped_pos = 'MID'  # default
            
            players.append({
                'player_name': pname,
                'position': mapped_pos,
                'raw_pos': pos,
            })
    
    if players:
        team_name = text
        teams_data[team_name] = {
            'group': current_group,
            'players': players
        }
        print(f"  {current_group} - {team_name}: {len(players)} players")

print(f"\nTotal teams parsed: {len(teams_data)}")
print(f"Total players: {sum(len(t['players']) for t in teams_data.values())}")

# Build CSV
rows = []
for team, data in teams_data.items():
    for p in data['players']:
        rows.append({
            'player_name': p['player_name'],
            'team': team,
            'position': p['position'],
            'caps': 0,
            'club': '',
            'group': data['group'],
        })

df = pd.DataFrame(rows)
os.makedirs('data', exist_ok=True)
df.to_csv('data/wc2026_squads_new.csv', index=False)
print(f"\nSaved data/wc2026_squads_new.csv with {len(df)} players from {df['team'].nunique()} teams")
print(f"\nTeams: {sorted(df['team'].unique())}")
