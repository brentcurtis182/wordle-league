import sqlite3
import logging

def check_player_mappings():
    """Check player mappings in the database"""
    print("Checking player mappings in the database...")
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        print("\n--- PAL League Players (League ID 3) ---")
        cursor.execute("""
        SELECT name, phone_number, league_id FROM players 
        WHERE league_id = 3
        """)
        
        pal_players = cursor.fetchall()
        if pal_players:
            for player in pal_players:
                print(f"Player: {player[0]}, Phone: {player[1]}, League ID: {player[2]}")
        else:
            print("No players found for PAL league (ID 3)")
            
        print("\n--- Wordle Warriorz Players (League ID 1) ---")
        cursor.execute("""
        SELECT name, phone_number, league_id FROM players 
        WHERE league_id = 1
        """)
        
        warriorz_players = cursor.fetchall()
        if warriorz_players:
            for player in warriorz_players:
                print(f"Player: {player[0]}, Phone: {player[1]}, League ID: {player[2]}")
        else:
            print("No players found for Wordle Warriorz league (ID 1)")
            
        print("\n--- All Players (Any League) ---")
        cursor.execute("""
        SELECT name, phone_number, league_id FROM players
        ORDER BY league_id
        """)
        
        all_players = cursor.fetchall()
        if all_players:
            for player in all_players:
                print(f"Player: {player[0]}, Phone: {player[1]}, League ID: {player[2] if player[2] else 'None'}")
        else:
            print("No players found in database")
            
    except Exception as e:
        print(f"Error accessing database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_player_mappings()
