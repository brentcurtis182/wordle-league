#!/usr/bin/env python3
"""
Fix the player mapping function to prevent incorrect score assignments across leagues
"""

import os
import shutil
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mapping_fix.log"),
        logging.StreamHandler()
    ]
)

def backup_file(file_path):
    """Create a backup of the file before modifying it"""
    backup_path = f"{file_path}.bak.{os.path.basename(file_path)}"
    try:
        shutil.copy2(file_path, backup_path)
        logging.info(f"Created backup at {backup_path}")
        return True
    except Exception as e:
        logging.error(f"Error creating backup: {e}")
        return False

def fix_player_mapping_function():
    """Fix the get_player_by_phone_for_league function to prevent fallback"""
    file_path = os.path.join("integrated_auto_update_multi_league.py")
    
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return False
    
    # Create backup
    if not backup_file(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Define the pattern to find the problematic function
        old_function_pattern = re.compile(
            r"def get_player_by_phone_for_league\(phone_number, league_id\):(.*?)"
            r"# If not found, fallback to original lookup method for compatibility(.*?)"
            r"return player\[0\](.*?)"
            r"return None", 
            re.DOTALL
        )
        
        # Define the replacement function
        new_function = """def get_player_by_phone_for_league(phone_number, league_id):
    \"\"\"Get player name by phone number for a specific league\"\"\"
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # FIXED: Only find players in the specified league
        cursor.execute(\"\"\"
        SELECT name FROM players 
        WHERE phone_number = ? AND league_id = ?
        \"\"\", (phone_number, league_id))
        
        player = cursor.fetchone()
        
        if player:
            return player[0]
            
        # NO FALLBACK - Strict league matching only
        logging.info(f"No player found with phone {phone_number} in league {league_id}")
        return None
        """
        
        # Replace the function
        if old_function_pattern.search(content):
            new_content = old_function_pattern.sub(new_function, content)
            
            # Write the modified content back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            logging.info(f"Successfully fixed player mapping function in {file_path}")
            print(f"Successfully fixed player mapping function in {file_path}")
            return True
        else:
            logging.error("Could not find the player mapping function pattern")
            print("Error: Could not find the player mapping function pattern")
            
            # Try a different approach - look for key lines
            if "# If not found, fallback to original lookup method for compatibility" in content:
                print("Found fallback comment but regex pattern didn't match.")
                print("Please manually update the function to remove the fallback logic.")
            return False
            
    except Exception as e:
        logging.error(f"Error fixing player mapping function: {e}")
        print(f"Error: {e}")
        return False

def check_extraction_process():
    """Check if the extraction process properly uses league IDs"""
    extract_file = "direct_hidden_extraction.py"
    
    if not os.path.exists(extract_file):
        logging.warning(f"File not found: {extract_file}")
        return
        
    try:
        with open(extract_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check if league_id is being passed to the player mapping function
        if "player = get_player_by_phone_for_league(phone, league_id)" in content:
            logging.info("Extraction code correctly passes league_id to player mapping function")
            print("Extraction code correctly passes league_id to player mapping function")
        else:
            logging.warning("Extraction code might not be passing league_id correctly")
            print("Warning: Extraction code might not be passing league_id correctly")
    
    except Exception as e:
        logging.error(f"Error checking extraction process: {e}")

def manually_fix_instructions():
    """Provide instructions for manual fix if automated fix fails"""
    print("\n==== MANUAL FIX INSTRUCTIONS ====")
    print("If the automated fix didn't work, follow these steps:")
    print("\n1. Open integrated_auto_update_multi_league.py")
    print("2. Find the 'get_player_by_phone_for_league' function (around line 462)")
    print("3. Remove the fallback code that looks like this:")
    print("```python")
    print("# If not found, fallback to original lookup method for compatibility")
    print("cursor.execute(\"SELECT name FROM players WHERE phone_number = ?\", (phone_number,))")
    print("player = cursor.fetchone()")
    print("if player:")
    print("    logging.warning(f\"Player {player[0]} ({phone_number}) found in default players table but not in league {league_id}\")")
    print("    return player[0]")
    print("```")
    print("\n4. This fallback is causing Keith to incorrectly get Joanna's scores")
    print("5. Save the file and try running the extraction again")
    print("==================================")

def main():
    logging.info("Starting to fix player mapping function...")
    
    # Fix the player mapping function
    success = fix_player_mapping_function()
    
    # Check extraction process
    check_extraction_process()
    
    # Provide manual instructions if needed
    if not success:
        manually_fix_instructions()
    
    print("\nRemember:")
    print("1. This fix enforces strict league-specific player mapping")
    print("2. Players with the same phone number in different leagues will only get scores for their specific league")
    print("3. You should test the extraction with this fix to ensure all scores are correctly assigned")
    print("\nOnce you've verified the fix works, you can re-enable the scheduler.")
    
    logging.info("Player mapping fix process completed")

if __name__ == "__main__":
    main()
