#!/usr/bin/env python3

import sqlite3
import sys

# Connect to the database
conn = sqlite3.connect('wordle_league.db')
cursor = conn.cursor()

# Check leagues table structure
print("===== LEAGUES TABLE SCHEMA =====")
cursor.execute("PRAGMA table_info(leagues)")
columns = cursor.fetchall()
for col in columns:
    print(f"- {col[1]} ({col[2]})")

# Check leagues data
print("\n===== LEAGUES DATA =====")
cursor.execute("SELECT * FROM leagues")
leagues = cursor.fetchall()
for league in leagues:
    print(league)

# Check the schema of the players table
print("\n===== PLAYERS TABLE SCHEMA =====")
cursor.execute("PRAGMA table_info(players)")
columns = cursor.fetchall()
for col in columns:
    print(f"- {col[1]} ({col[2]})")

# Check today's scores with player information
print("\n===== TODAY'S SCORES (WORDLE #1508) WITH PLAYER INFO =====")
print("Player Name      | Score | League Info")
print("-----------------|-------|------------")

query = """
    SELECT p.name, p.id, s.score, p.league_id, s.date 
    FROM scores s
    JOIN players p ON s.player_id = p.id
    WHERE s.wordle_number = 1508
    ORDER BY p.league_id, s.score
"""

cursor.execute(query)
scores = cursor.fetchall()

for player, player_id, score, league_id, date in scores:
    # Get league name
    cursor.execute("SELECT name FROM leagues WHERE league_id = ?", (league_id,))
    league_name = cursor.fetchone()
    league_name = league_name[0] if league_name else "Unknown League"
    
    print(f"{player:16} | {score:5}/6 | League {league_id}: {league_name} (Date: {date})")

# Check if any players appear in scores for multiple leagues
print("\n===== CHECKING FOR CROSS-LEAGUE SCORE ISSUES =====")
query = """
    SELECT p.name, p.id, COUNT(DISTINCT p.league_id) as league_count
    FROM players p
    JOIN scores s ON s.player_id = p.id
    WHERE s.wordle_number = 1508
    GROUP BY p.name, p.id
    HAVING league_count > 1
"""

cursor.execute(query)
duplicate_players = cursor.fetchall()

if duplicate_players:
    print("WARNING: Found players with scores in multiple leagues:")
    for player, player_id, league_count in duplicate_players:
        print(f"- {player} (ID: {player_id}) appears in {league_count} leagues")
        
        # Show the actual scores
        cursor.execute("""
            SELECT p.league_id, l.name, s.score
            FROM scores s
            JOIN players p ON s.player_id = p.id
            JOIN leagues l ON p.league_id = l.league_id
            WHERE p.id = ? AND s.wordle_number = 1508
        """, (player_id,))
        
        player_scores = cursor.fetchall()
        for league_id, league_name, score in player_scores:
            print(f"  - League {league_id} ({league_name}): {score}/6")
else:
    print("✓ No cross-league issues found")

conn.close()
