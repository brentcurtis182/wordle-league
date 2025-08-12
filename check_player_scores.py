#!/usr/bin/env python3
"""
Script to check recent scores for Joanna and Keith in the database
"""

import sqlite3
import datetime

def check_scores():
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get today's date
        today = datetime.date.today().strftime("%Y-%m-%d")
        
        # Check all scores from today
        print(f"All scores from today ({today}):")
        cursor.execute("SELECT date, league_id, wordle_num, player, score FROM scores WHERE date = ? ORDER BY league_id", (today,))
        today_scores = cursor.fetchall()
        for score in today_scores:
            print(score)
        
        print("\n" + "-"*50 + "\n")
        
        # Check recent scores for Joanna
        print("Recent scores for Joanna:")
        cursor.execute("SELECT date, league_id, wordle_num, player, score FROM scores WHERE player LIKE ? ORDER BY date DESC LIMIT 10", ("%Joanna%",))
        joanna_scores = cursor.fetchall()
        for score in joanna_scores:
            print(score)
        
        print("\n" + "-"*50 + "\n")
        
        # Check recent scores for Keith
        print("Recent scores for Keith:")
        cursor.execute("SELECT date, league_id, wordle_num, player, score FROM scores WHERE player LIKE ? ORDER BY date DESC LIMIT 10", ("%Keith%",))
        keith_scores = cursor.fetchall()
        for score in keith_scores:
            print(score)
            
        print("\n" + "-"*50 + "\n")
        
        # Check player mappings
        print("Player mapping information:")
        cursor.execute("SELECT id, name, phone FROM players WHERE name LIKE ? OR name LIKE ? ORDER BY id", ("%Joanna%", "%Keith%"))
        players = cursor.fetchall()
        for player in players:
            print(player)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close the connection
        if conn:
            conn.close()

if __name__ == "__main__":
    check_scores()
