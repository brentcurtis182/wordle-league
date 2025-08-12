#!/usr/bin/env python3
# Script to update Matt's phone number for better identification

import sqlite3
import sys

# Connect to the database
conn = sqlite3.connect('wordle_league.db')
cursor = conn.cursor()

# First, let's check Matt's current info
cursor.execute("""
    SELECT id, name, phone_number, league_id
    FROM players
    WHERE id = 18
""")

matt_info = cursor.fetchone()
if matt_info:
    player_id, name, current_phone, league_id = matt_info
    print(f"Current info for Matt (ID {player_id}):")
    print(f"  Name: {name}")
    print(f"  Phone: {current_phone}")
    print(f"  League: {league_id}")
    
    # Update Matt's phone number to include "DinkBeach"
    new_phone = "DinkBeach"
    cursor.execute("""
        UPDATE players
        SET phone_number = ?
        WHERE id = 18
    """, (new_phone,))
    
    # Commit the change
    conn.commit()
    
    # Verify the update
    cursor.execute("SELECT name, phone_number FROM players WHERE id = 18")
    updated_info = cursor.fetchone()
    if updated_info:
        name, phone = updated_info
        print(f"\nUpdated Matt's phone number:")
        print(f"  Name: {name}")
        print(f"  New Phone: {phone}")
        print("\nUpdate successful! The system should now be able to identify Matt's scores.")
    else:
        print("\nError: Could not verify the update.")
else:
    print("Error: Could not find player with ID 18 (Matt) in the database.")
    
    # Let's check if Matt exists under a different ID
    cursor.execute("SELECT id, name, phone_number, league_id FROM players WHERE name LIKE 'Matt%' AND league_id = 4")
    alt_matts = cursor.fetchall()
    if alt_matts:
        print("\nFound possible Matt entries:")
        for alt in alt_matts:
            print(f"  ID: {alt[0]}, Name: {alt[1]}, Phone: {alt[2]}, League: {alt[3]}")
            
            # Update this entry instead
            cursor.execute("UPDATE players SET phone_number = 'DinkBeach' WHERE id = ?", (alt[0],))
            conn.commit()
            print(f"  Updated ID {alt[0]} with phone 'DinkBeach'")
    else:
        print("No alternate Matt entries found.")

print("\nFinished processing.")
conn.close()
