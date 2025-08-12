import sqlite3
import os
from datetime import datetime

def update_player_name():
    """Update Shawn's name to Shawna in the database"""
    
    conn = sqlite3.connect('wordle_league.db')
    cursor = conn.cursor()
    
    print("=" * 70)
    print(f"PLAYER NAME UPDATE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # First check if player exists
    cursor.execute("SELECT id, name, league_id FROM players WHERE name = 'Shawn'")
    player_info = cursor.fetchone()
    
    if not player_info:
        print("Player 'Shawn' not found in database!")
        conn.close()
        return
    
    player_id, old_name, league_id = player_info
    
    print(f"Found player: {old_name} (ID: {player_id}) in League {league_id}")
    print(f"Current name: {old_name}")
    print(f"New name: Shawna")
    
    # Update the name
    cursor.execute("UPDATE players SET name = 'Shawna' WHERE id = ?", (player_id,))
    conn.commit()
    
    # Verify the update
    cursor.execute("SELECT name FROM players WHERE id = ?", (player_id,))
    new_name = cursor.fetchone()[0]
    
    print(f"Name updated to: {new_name}")
    print(f"Update successful: {new_name == 'Shawna'}")
    
    conn.close()
    print("=" * 70)

if __name__ == "__main__":
    update_player_name()
