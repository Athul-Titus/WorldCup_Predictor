"""Debug the Wikipedia HTML structure."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from bs4 import BeautifulSoup

HTML_PATH = r'C:\Users\athul\.gemini\antigravity-ide\brain\522435ca-9e60-4fe6-9208-30a7b41abfef\.system_generated\steps\52\content.md'

with open(HTML_PATH, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

# Find h3 elements
h3s = soup.find_all('h3')
print(f"Found {len(h3s)} h3 elements")
for h3 in h3s[:10]:
    span = h3.find('span', class_='mw-headline')
    if span:
        text = span.get_text(strip=True)
        print(f"  H3: '{text}'")
        # Check what follows
        next_sib = h3.find_next_sibling()
        if next_sib:
            print(f"    Next sibling: <{next_sib.name}> class={next_sib.get('class', '')}")
    else:
        print(f"  H3 (no headline span): {h3.get_text(strip=True)[:50]}")

print("\n--- Looking for tables ---")
tables = soup.find_all('table')
print(f"Total tables: {len(tables)}")
for i, t in enumerate(tables[:5]):
    classes = t.get('class', [])
    rows = t.find_all('tr')
    print(f"  Table {i}: classes={classes}, rows={len(rows)}")
    if rows and len(rows) > 1:
        # Print first 2 rows
        for r in rows[:2]:
            cells = r.find_all(['th', 'td'])
            print(f"    Row: {[c.get_text(strip=True)[:30] for c in cells[:6]]}")

# Let's also look for the specific US squad section
print("\n--- Looking for 'United States' ---")
us_span = soup.find('span', id='United_States')
if us_span:
    print(f"Found span id=United_States: {us_span.parent.name}")
    parent = us_span.parent
    sib = parent.find_next_sibling()
    count = 0
    while sib and count < 5:
        print(f"  Sibling: <{sib.name}> class={sib.get('class', [])}")
        if sib.name == 'table':
            rows = sib.find_all('tr')
            print(f"    Rows: {len(rows)}")
            for r in rows[:3]:
                cells = r.find_all(['th', 'td'])
                print(f"    -> {[c.get_text(strip=True)[:30] for c in cells[:8]]}")
            break
        sib = sib.find_next_sibling()
        count += 1
else:
    print("  Not found by id")
    # Try text search
    for span in soup.find_all('span', class_='mw-headline'):
        if 'United States' in span.get_text():
            print(f"  Found via text: '{span.get_text()}' id={span.get('id')}")
