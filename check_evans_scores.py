#!/usr/bin/env python3
import sqlite3
import datetime
from datetime import timedelta

# Connect to database
conn = sqlite3.connect('wordle_league.db')
cursor = conn.cursor()

print("=== Evan's scores in the database ===")
cursor.execute("""
    SELECT player_name, score, date(timestamp), timestamp, league_id 
    FROM scores 
    WHERE player_name='Evan' 
    ORDER BY timestamp DESC
""")

scores = cursor.fetchall()
print(f"Found {len(scores)} scores for Evan")

for score in scores:
    print(f"Player: {score[0]}, Score: {score[1]}, Date: {score[2]}, Timestamp: {score[3]}, League: {score[4]}")

# Get start of current week (Monday)
today = datetime.datetime.now()
start_of_week = today - timedelta(days=today.weekday())
start_of_week = datetime.datetime(start_of_week.year, start_of_week.month, start_of_week.day)

print(f"\n=== Evan's scores this week (since {start_of_week.date()}) ===")
cursor.execute("""
    SELECT player_name, score, date(timestamp), timestamp, league_id 
    FROM scores 
    WHERE player_name='Evan' AND timestamp >= ?
    ORDER BY timestamp DESC
""", (start_of_week.strftime("%Y-%m-%d"),))

weekly_scores = cursor.fetchall()
print(f"Found {len(weekly_scores)} scores for Evan this week")

for score in weekly_scores:
    print(f"Player: {score[0]}, Score: {score[1]}, Date: {score[2]}, Timestamp: {score[3]}, League: {score[4]}")

conn.close()
