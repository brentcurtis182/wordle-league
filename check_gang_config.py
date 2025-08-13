#!/usr/bin/env python3
import json
import os
import logging
import sqlite3

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Check the configuration for Wordle Gang league"""
    # Load the league configuration
    try:
        with open('league_config.json', 'r') as f:
            config = json.load(f)
        
        # Find Wordle Gang league config
        gang_league = None
        for league in config['leagues']:
            if league['league_id'] == 2:
                gang_league = league
                break
        
        if not gang_league:
            logging.error("Could not find Wordle Gang league in configuration")
            return
        
        logging.info("=== Wordle Gang League Configuration ===")
        logging.info(f"Name: {gang_league['name']}")
        logging.info(f"Thread ID: {gang_league['thread_id']}")
        logging.info(f"Players CSV: {gang_league['players_csv']}")
        
        # Check if the thread ID matches what we expect
        expected_thread = "g.Group%20Message.fWsZEz2b9B%2BpjZMex%2BCAYQ"
        if gang_league['thread_id'] == expected_thread:
            logging.info("✅ Thread ID matches expected value")
        else:
            logging.error(f"❌ Thread ID does not match expected value")
            
        # Check if the database has this thread ID stored
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Check if there's a config table entry for this
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='config'")
        if cursor.fetchone():
            cursor.execute("SELECT key, value FROM config WHERE key LIKE '%thread%' AND key LIKE '%2%'")
            thread_configs = cursor.fetchall()
            if thread_configs:
                for key, value in thread_configs:
                    logging.info(f"Database config: {key} = {value}")
                    if value == expected_thread:
                        logging.info("✅ Database thread ID matches expected value")
                    else:
                        logging.warning(f"❌ Database thread ID does not match: {value}")
            else:
                logging.info("No thread configuration found in database")
        
        # Check Mylene's player record
        cursor.execute("""
            SELECT id, name, phone_number FROM players 
            WHERE name = 'Mylene' AND league_id = 2
        """)
        player = cursor.fetchone()
        if player:
            player_id, name, phone = player
            logging.info(f"Mylene's record: ID={player_id}, Phone={phone}")
            
            # Check if the phone number matches what we expect
            expected_phone = "17142718280"
            if phone == expected_phone:
                logging.info("✅ Phone number matches expected value")
            else:
                logging.warning(f"❌ Phone number does not match expected value: {phone}")
        else:
            logging.error("Could not find Mylene in the players table")
        
        conn.close()
        
        # Check if the CSV file has been updated
        if os.path.exists(gang_league['players_csv']):
            with open(gang_league['players_csv'], 'r') as f:
                csv_content = f.read()
                logging.info(f"CSV content:\n{csv_content}")
                
                if "17142718280" in csv_content:
                    logging.info("✅ Phone number found in CSV file")
                else:
                    logging.warning("❌ Phone number not found in CSV file")
        else:
            logging.error(f"Players CSV file not found: {gang_league['players_csv']}")
        
    except Exception as e:
        logging.error(f"Error checking configuration: {str(e)}")

if __name__ == "__main__":
    main()
