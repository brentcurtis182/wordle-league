#!/usr/bin/env python3
import sqlite3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def update_mylene_phone():
    """Update Mylene's phone number in the database to match the CSV file"""
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # First, check Mylene's current record
        cursor.execute("""
            SELECT id, name, phone_number FROM players 
            WHERE name = 'Mylene' AND league_id = 2
        """)
        
        player = cursor.fetchone()
        if not player:
            logging.error("Mylene not found in the players table for Wordle Gang")
            return
            
        player_id, name, old_phone = player
        logging.info(f"Found Mylene (ID: {player_id}) with current phone: {old_phone}")
        
        # Update to the new phone number from the CSV
        new_phone = "17142718280"
        cursor.execute("""
            UPDATE players 
            SET phone_number = ? 
            WHERE id = ?
        """, (new_phone, player_id))
        
        conn.commit()
        
        # Verify the update
        cursor.execute("""
            SELECT phone_number FROM players WHERE id = ?
        """, (player_id,))
        
        updated_phone = cursor.fetchone()[0]
        if updated_phone == new_phone:
            logging.info(f"✅ Successfully updated Mylene's phone to: {new_phone}")
        else:
            logging.error(f"❌ Failed to update phone number. Still showing as: {updated_phone}")
        
        conn.close()
        
    except Exception as e:
        logging.error(f"Error updating phone number: {str(e)}")

if __name__ == "__main__":
    update_mylene_phone()
