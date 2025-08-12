#!/usr/bin/env python3
"""
Check Keith's phone number in the database
"""
import sqlite3

# Connect to the database
conn = sqlite3.connect('wordle_league.db')
cursor = conn.cursor()

# Query for Keith's phone number
cursor.execute("""
SELECT name, phone_number, league_id 
FROM players 
WHERE name = 'Keith'
""")

keith_records = cursor.fetchall()
print(f"Found {len(keith_records)} records for Keith")

for name, phone, league_id in keith_records:
    print(f"League {league_id}: {name}, Phone: {phone}")

# Check if "714 8030122" exists as a phone number
phone_to_check = "714 8030122"
cursor.execute("""
SELECT name, phone_number, league_id 
FROM players 
WHERE phone_number = ?
""", (phone_to_check,))

matching_records = cursor.fetchall()
print(f"\nFound {len(matching_records)} players with phone number '{phone_to_check}'")

for name, phone, league_id in matching_records:
    print(f"League {league_id}: {name}, Phone: {phone}")

conn.close()
