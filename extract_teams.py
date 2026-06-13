import re

with open(r'C:\Users\athul\.gemini\antigravity-ide\brain\522435ca-9e60-4fe6-9208-30a7b41abfef\.system_generated\steps\52\content.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract team names from TOC level-2 entries
teams = re.findall(r'id="toc-([^"]+)"\s*\n\s*class="vector-toc-list-item vector-toc-level-2"', content)
teams = [t.replace('_', ' ') for t in teams]
print(f"Total teams: {len(teams)}")
for i, t in enumerate(teams, 1):
    print(f"{i}. {t}")
