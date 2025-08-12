import sqlite3
import json
import sys
from pathlib import Path

# Set stdout to handle UTF-8 to avoid encoding issues with emoji patterns
sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')

# Check database first
conn = sqlite3.connect('wordle_league.db')
cursor = conn.cursor()

print("=== CHECKING DATABASE FOR VOX'S SCORES ===")
# Get column names first
cursor.execute("PRAGMA table_info(scores)")
columns = [col[1] for col in cursor.fetchall()]

# Get Vox's scores
cursor.execute("SELECT id, wordle_num, score, player_name, timestamp, league_id FROM scores WHERE player_name='Vox' AND league_id=3")
vox_scores = cursor.fetchall()
print(f"Found {len(vox_scores)} scores for Vox in PAL league (id=3):")
for score in vox_scores:
    # Print safely without the emoji pattern that causes encoding issues
    print(f"ID: {score[0]}, Wordle: {score[1]}, Score: {score[2]}, Player: {score[3]}, Time: {score[4]}, League: {score[5]}")


# Check website exported files
print("\n=== CHECKING WEBSITE EXPORTS ===")
latest_json = Path('website_export/api/latest.json')
if latest_json.exists():
    with open(latest_json, 'r') as f:
        data = json.load(f)
        print("Latest scores in exported JSON file:")
        if 'leagues' in data and ('3' in data['leagues'] or 3 in data['leagues']):
            pal_league = data['leagues']['3'] if '3' in data['leagues'] else data['leagues'][3]
            print(f"PAL League data found: {pal_league['name']}")
            if 'scores' in pal_league:
                vox_entries = [s for s in pal_league['scores'] if s['name'] == 'Vox']
                print(f"Found {len(vox_entries)} entries for Vox in PAL league:")
                for entry in vox_entries:
                    print(f"  Wordle #{entry['wordle_num']} - Score: {entry['score']}")
            else:
                print("No scores section found in PAL league data")
        else:
            print("No PAL league (id=3) found in latest.json")
else:
    print(f"latest.json file not found at {latest_json}")

conn.close()
