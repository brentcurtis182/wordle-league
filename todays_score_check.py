#!/usr/bin/env python3

import sqlite3
import sys

# Connect to the database
conn = sqlite3.connect('wordle_league.db')
cursor = conn.cursor()

print("===== DATABASE TABLES =====")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"- {table[0]}")

print("\n===== TODAY'S SCORES (WORDLE #1508) =====")
print("LeagueID | Player Name      | Score | Date Added")
print("---------|------------------|-------|------------")

# Let's first check the schema of the scores table
cursor.execute("PRAGMA table_info(scores)")
columns = cursor.fetchall()
print("\n===== SCORES TABLE SCHEMA =====")
for col in columns:
    print(f"- {col[1]} ({col[2]})")
print("\n")

# Now let's adjust our query based on the actual schema
query = """
    SELECT s.league, p.name, s.score, s.date_added, l.name
    FROM scores s
    JOIN players p ON s.player_id = p.id
    JOIN leagues l ON s.league = l.league_id
    WHERE s.wordle_num = 1508
    ORDER BY s.league, s.score
"""

cursor.execute(query)
scores = cursor.fetchall()

for league_id, player, score, date_added, league_name in scores:
    print(f"{league_id:8} | {player:16} | {score:5}/6 | {date_added} | {league_name}")

print("\n===== YESTERDAY'S SCORES (WORDLE #1507) =====")
print("LeagueID | Player Name      | Score | Date Added")
print("---------|------------------|-------|------------")

query = """
    SELECT s.league, p.name, s.score, s.date_added, l.name
    FROM scores s
    JOIN players p ON s.player_id = p.id
    JOIN leagues l ON s.league = l.league_id
    WHERE s.wordle_num = 1507
    ORDER BY s.league, s.score
"""

cursor.execute(query)
scores = cursor.fetchall()

for league_id, player, score, date_added, league_name in scores:
    print(f"{league_id:8} | {player:16} | {score:5}/6 | {date_added} | {league_name}")

conn.close()
