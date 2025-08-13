#!/usr/bin/env python3
import sqlite3
import sys

# Connect to the database
conn = sqlite3.connect('wordle_league.db')
cursor = conn.cursor()

# First, check Matt's current phone number
cursor.execute('SELECT id, name, phone_number FROM players WHERE id = 18')
before = cursor.fetchone()
print(f"Before update: ID={before[0]}, Name={before[1]}, Phone={before[2]}")

# Update Matt's phone number to exactly "Dinkbeach" (correct case)
cursor.execute('UPDATE players SET phone_number = ? WHERE id = 18', ('Dinkbeach',))
conn.commit()

# Verify the update
cursor.execute('SELECT id, name, phone_number FROM players WHERE id = 18')
after = cursor.fetchone()
print(f"After update: ID={after[0]}, Name={after[1]}, Phone={after[2]}")

print("Update completed successfully!")
conn.close()
