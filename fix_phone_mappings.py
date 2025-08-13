#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Fix phone mappings in the multi-league scheduler
This script updates the phone number mappings to match the CSV files
"""

import csv
import logging
import os
import sqlite3
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='fix_phone_mappings.log',
    filemode='w'
)

# File paths for CSV mapping files
CSV_FILES = {
    1: 'familyPlayers.csv',              # Wordle Warriorz
    2: 'familyPlayers - wordleGang.csv', # Wordle Gang
    3: 'familyPlayers - wordlePal.csv'   # PAL League
}

def load_csv_mappings():
    """Load player mappings from CSV files"""
    mappings = {}
    
    for league_id, csv_file in CSV_FILES.items():
        mappings[league_id] = {}
        
        if not os.path.exists(csv_file):
            logging.error(f"CSV file not found: {csv_file}")
            continue
            
        try:
            with open(csv_file, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header row
                
                for row in reader:
                    if len(row) >= 2:
                        player_name = row[0].strip()
                        phone = row[1].strip()
                        
                        # Clean phone number to just digits
                        cleaned_phone = re.sub(r'[^0-9]', '', phone)
                        if cleaned_phone:
                            mappings[league_id][cleaned_phone] = player_name
                            logging.info(f"Loaded mapping for league {league_id}: {player_name} -> {cleaned_phone}")
        except Exception as e:
            logging.error(f"Error loading CSV file {csv_file}: {e}")
    
    return mappings

def update_database_mappings(mappings):
    """Update database with correct phone mappings"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get existing player data
        cursor.execute("SELECT DISTINCT player_name, league_id FROM scores")
        existing_players = cursor.fetchall()
        
        updated_count = 0
        for player_name, league_id in existing_players:
            if league_id in mappings:
                # Find phone number for this player in the mapping
                phone_found = False
                for phone, mapped_player in mappings[league_id].items():
                    if mapped_player == player_name:
                        # Update the database with correct phone number
                        cursor.execute(
                            "UPDATE scores SET phone_number = ? WHERE player_name = ? AND league_id = ?",
                            (phone, player_name, league_id)
                        )
                        updated_count += cursor.rowcount
                        logging.info(f"Updated {player_name} in league {league_id} with phone {phone}")
                        phone_found = True
                        break
                
                if not phone_found:
                    logging.warning(f"No phone mapping found for {player_name} in league {league_id}")
        
        conn.commit()
        logging.info(f"Updated {updated_count} records in database")
        
        # Verify updates
        for league_id in mappings:
            cursor.execute(
                "SELECT player_name, phone_number FROM scores WHERE league_id = ? GROUP BY player_name",
                (league_id,)
            )
            logging.info(f"--- League {league_id} mappings after update ---")
            for row in cursor.fetchall():
                logging.info(f"Player: {row[0]}, Phone: {row[1]}")
        
        conn.close()
        return updated_count
    except Exception as e:
        logging.error(f"Error updating database: {e}")
        return 0

def create_mapping_reference():
    """Create a reference file with mappings from CSVs"""
    mappings = load_csv_mappings()
    
    with open('phone_mappings_reference.py', 'w') as f:
        f.write("# -*- coding: utf-8 -*-\n\n")
        f.write("'''\nPHONE MAPPINGS REFERENCE\n")
        f.write("This file contains the mappings between phone numbers and player names for each league.\n")
        f.write("These mappings are derived from the CSV files and should be kept in sync.\n'''\n\n")
        
        f.write("# Phone mappings by league\n")
        f.write("PHONE_MAPPINGS = {\n")
        
        for league_id, league_mappings in mappings.items():
            if league_id == 1:
                league_name = "Wordle Warriorz"
            elif league_id == 2:
                league_name = "Wordle Gang"
            elif league_id == 3:
                league_name = "PAL League"
            else:
                league_name = f"League {league_id}"
                
            f.write(f"    # {league_name} mappings (league_id: {league_id})\n")
            f.write(f"    {league_id}: {{\n")
            
            for phone, name in league_mappings.items():
                f.write(f"        '{phone}': '{name}',\n")
            
            f.write("    },\n\n")
        
        f.write("}\n")
    
    logging.info("Created phone_mappings_reference.py")

def main():
    """Main function"""
    logging.info("Starting phone mapping fix")
    
    # Load mappings from CSV files
    mappings = load_csv_mappings()
    
    # Create reference file
    create_mapping_reference()
    
    # Update database
    updated = update_database_mappings(mappings)
    
    logging.info(f"Phone mapping fix complete. Updated {updated} records.")
    print(f"Phone mapping fix complete. Updated {updated} records.")
    print("Created phone_mappings_reference.py for future reference")

if __name__ == "__main__":
    main()
