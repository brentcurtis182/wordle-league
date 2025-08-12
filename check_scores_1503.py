#!/usr/bin/env python3
"""
Script to check scores for Wordle 1503 across all leagues
"""
import sqlite3
import sys

try:
    # Connect to the database
    conn = sqlite3.connect('wordle_league.db')
    cursor = conn.cursor()
    
    # Get league names - assuming league_id is directly used
    leagues = {
        1: "Wordle Warriorz",
        2: "Wordle Gang",
        3: "Wordle PAL"
    }
    
    print("Scores for Wordle 1503 across all leagues:")
    print("=" * 80)
    
    for league_id, league_name in leagues.items():
        # Query scores for Wordle 1503 in this league
        cursor.execute("""
        SELECT player_name, score, timestamp
        FROM scores
        WHERE league_id = ? AND wordle_num = 1503
        ORDER BY player_name
        """, (league_id,))
        
        rows = cursor.fetchall()
        
        print(f"\n{league_name} (ID: {league_id}):")
        print("-" * 40)
        
        if rows:
            print(f"{'Player':<20} {'Score':<10} {'Timestamp':<30}")
            print("-" * 60)
            for row in rows:
                player_name = row[0]
                score = row[1]
                timestamp = row[2]
                print(f"{player_name:<20} {score:<10} {timestamp:<30}")
        else:
            print("No scores found for this league.")
    
    # Check for any scores from specific players in PAL league
    print("\nChecking for specific players in PAL league (ID: 3):")
    print("-" * 60)
    
    for player in ["FuzWuz", "Starslider"]:
        cursor.execute("""
        SELECT wordle_num, score, timestamp
        FROM scores
        WHERE league_id = 3 AND player_name = ?
        ORDER BY wordle_num DESC
        """, (player,))
        
        rows = cursor.fetchall()
        
        if rows:
            print(f"\n{player}'s scores:")
            print(f"{'Wordle #':<10} {'Score':<10} {'Timestamp':<30}")
            print("-" * 50)
            for row in rows:
                wordle_num = row[0]
                score = row[1]
                timestamp = row[2]
                print(f"{wordle_num:<10} {score:<10} {timestamp:<30}")
        else:
            print(f"\nNo scores found for {player}")
    
    # Check by inspecting the phone_mappings.py file directly
    print("\nPAL League Phone Mappings:")
    print("-" * 60)
    
    # Import the phone mapping module
    try:
        import phone_mappings
        # Get all mappings for league 3
        if hasattr(phone_mappings, 'phone_to_name_by_league'):
            pal_mappings = phone_mappings.phone_to_name_by_league.get(3, {})
            
            if pal_mappings:
                print(f"{'Phone Number':<20} {'Player Name':<20}")
                print("-" * 40)
                for phone, name in pal_mappings.items():
                    print(f"{phone:<20} {name:<20}")
            else:
                print("No phone mappings found for PAL league")
        else:
            print("phone_to_name_by_league not found in phone_mappings.py")
    except Exception as e:
        print(f"Error loading phone mappings: {e}")
    
    # No need for additional code here, phone mappings are handled above

except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
finally:
    if conn:
        conn.close()
