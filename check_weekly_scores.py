import sqlite3
import os
from datetime import datetime

def main():
    # Connect to the database
    conn = sqlite3.connect('wordle_league.db')
    cursor = conn.cursor()
    
    print("=== Scores for Wordle 1500-1506 by League ===")
    cursor.execute("""
    SELECT p.name, p.league_id, s.wordle_number, s.score, s.emoji_pattern, s.timestamp 
    FROM scores s 
    JOIN players p ON s.player_id = p.id 
    WHERE s.wordle_number >= 1500 AND s.wordle_number <= 1506 
    ORDER BY p.league_id, p.name, s.wordle_number
    """)
    
    scores = cursor.fetchall()
    
    # Print results by league
    current_league = None
    for row in scores:
        name, league_id, wordle_number, score, emoji_pattern, timestamp = row
        
        if league_id != current_league:
            print(f"\nLeague ID {league_id}:")
            current_league = league_id
        
        # Format the score (7 or "7" means X)
        display_score = "X" if score == 7 or score == "7" else score
        
        print(f"  {name} - Wordle {wordle_number}: {display_score}")
    
    if not scores:
        print("No scores found for Wordles 1500-1506")
    
    print("\n=== Players by League ===")
    cursor.execute("""
    SELECT league_id, COUNT(*) as player_count
    FROM players
    GROUP BY league_id
    """)
    
    for league_id, count in cursor.fetchall():
        print(f"League {league_id}: {count} players")
        
        # Get player list for this league
        cursor.execute("""
        SELECT name FROM players WHERE league_id = ?
        """, (league_id,))
        
        players = [row[0] for row in cursor.fetchall()]
        print(f"  Players: {', '.join(players)}")
    
    # Calculate weekly stat range
    today = datetime.now()
    weekday = today.weekday()  # 0 = Monday, 6 = Sunday
    
    if weekday == 0:  # Monday
        start_wordle = 1506  # Using today's wordle based on date
    else:
        start_wordle = 1506 - weekday
    
    end_wordle = start_wordle + 6
    
    print(f"\nCurrent Weekly Range: Wordles {start_wordle}-{end_wordle}")
    
    # Close connection
    conn.close()

if __name__ == "__main__":
    main()
