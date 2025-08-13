import sqlite3
import os
from datetime import datetime

def view_matt_score():
    """Direct database check for Matt's score"""
    
    conn = sqlite3.connect('wordle_league.db')
    cursor = conn.cursor()
    
    print("=" * 70)
    print(f"MATT'S WORDLE SCORE REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Get Matt's player info
    cursor.execute("SELECT id, name, league_id FROM players WHERE name = 'Matt'")
    matt_info = cursor.fetchone()
    
    if not matt_info:
        print("Matt not found in player database!")
        return
    
    matt_id, matt_name, league_id = matt_info
    
    # Get league name
    cursor.execute("SELECT name FROM leagues WHERE id = ?", (league_id,))
    league_name = cursor.fetchone()[0]
    
    print(f"Matt (ID: {matt_id}) is in league: {league_name} (ID: {league_id})")
    print("")
    
    # Get Matt's recent scores
    cursor.execute("""
        SELECT wordle_num, score, date, emoji_pattern 
        FROM scores 
        WHERE player_id = ? 
        ORDER BY wordle_num DESC
        LIMIT 5
    """, (matt_id,))
    
    scores = cursor.fetchall()
    
    print(f"Matt's recent scores (most recent first):")
    print("-" * 70)
    
    if not scores:
        print("No scores found for Matt")
    else:
        for wordle_num, score, date, emoji_pattern in scores:
            score_date = datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')
            print(f"Wordle #{wordle_num}: {score}/6 (submitted: {score_date})")
            
            if emoji_pattern:
                print("Pattern:")
                print("-" * 40)
                # Convert emoji pattern codes to readable form
                readable_pattern = emoji_pattern.replace("\\U0001f7e9", "🟩").replace("\\U0001f7e8", "🟨").replace("\\u2b1b", "⬛").replace("\\u2b1c", "⬜")
                print(readable_pattern)
                print("-" * 40)
            else:
                print("No emoji pattern available")
            
            print("")
    
    conn.close()
    print("=" * 70)

if __name__ == "__main__":
    view_matt_score()
