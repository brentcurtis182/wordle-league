#!/usr/bin/env python3
# Script to check emoji patterns in the database and save to a file

import sqlite3
import sys
import os
import datetime

def check_emoji_patterns(db_path, output_file, limit=10):
    """Check emoji patterns in the database and save to a file"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query for most recent emoji patterns
        cursor.execute("""
        SELECT player_name, wordle_num, emoji_pattern, league_id
        FROM scores 
        WHERE emoji_pattern IS NOT NULL 
        ORDER BY wordle_num DESC, timestamp DESC
        LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        
        # Write to HTML file to properly display emojis
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Emoji Pattern Check</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .pattern {{ white-space: pre; font-family: monospace; }}
        .entry {{ margin-bottom: 20px; padding: 10px; border: 1px solid #ccc; }}
    </style>
</head>
<body>
    <h1>Recent Emoji Patterns from Database</h1>
    <p>Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
""")
            
            for row in rows:
                player_name = row[0]
                wordle_num = row[1]
                emoji_pattern = row[2]
                league_id = row[3]
                
                # Get league name
                league_name = "Unknown"
                if league_id == 1:
                    league_name = "Wordle Warriorz"
                elif league_id == 2:
                    league_name = "Wordle Gang"
                elif league_id == 3:
                    league_name = "PAL League"
                
                f.write(f"""
    <div class="entry">
        <h3>Player: {player_name}, Wordle #{wordle_num}, League: {league_name}</h3>
        <div class="pattern">
{emoji_pattern}
        </div>
    </div>
                """)
            
            f.write("""
</body>
</html>
""")
            
        return len(rows)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 0
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    output_file = "emoji_patterns_check.html"
    count = check_emoji_patterns('wordle_league.db', output_file)
    print(f"Found {count} emoji patterns and saved to {output_file}")
    print(f"File path: {os.path.abspath(output_file)}")
    
    # Try to open the file in the default browser
    try:
        import webbrowser
        webbrowser.open(os.path.abspath(output_file))
        print("Opened file in browser")
    except:
        print("Could not open file in browser automatically")
