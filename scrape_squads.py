"""
scrape_squads.py — Scrape official FIFA World Cup 2026 squad lists from Wikipedia.
Outputs: data/wc2026_squads.csv with columns: player_name, team, position, caps, club, group
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads"


def map_position(pos_text):
    """Map Wikipedia position codes to simplified groups."""
    pos = pos_text.upper().strip()
    pos = re.sub(r'^\d+', '', pos)  # Remove leading numbers like '1GK'
    if pos in ('GK',):
        return 'GK'
    elif pos in ('DF', 'CB', 'LB', 'RB', 'LWB', 'RWB'):
        return 'DEF'
    elif pos in ('MF', 'CM', 'CDM', 'CAM', 'LM', 'RM', 'DM', 'AM'):
        return 'MID'
    elif pos in ('FW', 'ST', 'CF', 'LW', 'RW', 'SS'):
        return 'FWD'
    return 'MID'


def scrape_squads():
    """Scrape all 48 official WC 2026 squads from Wikipedia."""
    print(f"Fetching {URL}...")
    resp = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0 KickStats/1.0'})
    resp.raise_for_status()
    print(f"Downloaded {len(resp.text)} bytes")

    soup = BeautifulSoup(resp.text, 'html.parser')
    all_h3 = soup.find_all('h3')

    rows = []
    current_group = ''
    teams_found = []

    for h3 in all_h3:
        team_name = re.sub(r'\[.*?\]', '', h3.get_text(strip=True)).strip()

        # Skip non-team headings
        skip_keywords = ['Age', 'Player representation', 'Average age', 'Coach',
                         'Statistics', 'References', 'External links', 'Notes', 'See also', 'Contents']
        if any(kw in team_name for kw in skip_keywords):
            continue

        # Determine group from previous h2
        prev_h2 = h3.find_previous('h2')
        if prev_h2:
            group_text = re.sub(r'\[.*?\]', '', prev_h2.get_text(strip=True)).strip()
            if group_text.startswith('Group'):
                current_group = group_text

        # Find next squad table
        table = h3.find_next('table', class_='wikitable')
        if table is None:
            continue

        trs = table.find_all('tr')
        if len(trs) < 2:
            continue

        # Parse headers
        headers = [th.get_text(strip=True).lower() for th in trs[0].find_all(['th'])]

        # Identify column indices
        pos_idx, name_idx, caps_idx, club_idx = 1, 2, None, None
        for i, h in enumerate(headers):
            if h == 'pos.' or h == 'pos':
                pos_idx = i
            elif 'player' in h or 'name' in h:
                name_idx = i
            elif h == 'caps':
                caps_idx = i
            elif h == 'club':
                club_idx = i

        team_players = []
        for tr in trs[1:]:
            cells = tr.find_all(['td', 'th'])
            if len(cells) <= max(pos_idx, name_idx):
                continue

            # Player name
            name_cell = cells[name_idx]
            link = name_cell.find('a')
            pname = link.get_text(strip=True) if link else name_cell.get_text(strip=True)
            pname = re.sub(r'\(.*?\)', '', pname).strip()
            pname = re.sub(r'\[.*?\]', '', pname).strip()
            pname = pname.replace('(captain)', '').replace('(c)', '').strip()

            if not pname or pname.isdigit() or len(pname) < 2:
                continue

            # Position
            position = map_position(cells[pos_idx].get_text(strip=True))

            # Caps
            caps = 0
            if caps_idx is not None and caps_idx < len(cells):
                try:
                    caps = int(re.sub(r'\D', '', cells[caps_idx].get_text(strip=True)) or '0')
                except ValueError:
                    caps = 0

            # Club
            club = ''
            if club_idx is not None and club_idx < len(cells):
                club_cell = cells[club_idx]
                club_link = club_cell.find('a')
                club = (club_link.get_text(strip=True) if club_link
                        else club_cell.get_text(strip=True))

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

    print(f"\nTotal teams: {len(teams_found)}")
    print(f"Total players: {len(rows)}")

    df = pd.DataFrame(rows)
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/wc2026_squads.csv', index=False)
    print(f"Saved data/wc2026_squads.csv")
    return df


if __name__ == '__main__':
    scrape_squads()
