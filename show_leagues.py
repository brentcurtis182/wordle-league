#!/usr/bin/env python3
"""
Show league players and phone numbers
"""

import sqlite3

def main():
    conn = sqlite3.connect('wordle_league.db')
    cur = conn.cursor()
    
    print('=== LEAGUE PLAYERS AND PHONE NUMBERS ===\n')
    
    # Get all leagues
    cur.execute("SELECT DISTINCT league_id FROM players ORDER BY league_id")
    leagues = [row[0] for row in cur.fetchall()]
    
    # Map league IDs to names
    league_names = {
        1: 'Wordle Warriorz',
        2: 'Wordle Gang',
        3: 'PAL'
    }
    
    # Show players for each league
    for league_id in leagues:
        league_name = league_names.get(league_id, f"Unknown League {league_id}")
        print(f'\n## LEAGUE {league_id}: {league_name} ##')
        
        # Get players in this league
        cur.execute("""
            SELECT name, phone_number 
            FROM players 
            WHERE league_id = ? 
            ORDER BY name
        """, (league_id,))
        
        players = cur.fetchall()
        for name, phone in players:
            print(f'* {name}: {phone}')
    
    conn.close()

if __name__ == "__main__":
    main()
