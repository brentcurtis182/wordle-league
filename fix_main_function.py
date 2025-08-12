#!/usr/bin/env python3
"""
Fix Main Function in Integrated Auto Update Script
This ensures the reset functions are called automatically during the scheduler run.
"""

import os
import logging
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_main_function.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def fix_main_function():
    """Update main function to call reset functions in integrated_auto_update_multi_league.py"""
    
    script_path = os.path.join(os.getcwd(), "integrated_auto_update_multi_league.py")
    
    if not os.path.exists(script_path):
        logger.error(f"Script file not found: {script_path}")
        return False
    
    try:
        # Read the file content
        with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Check if main function already contains reset function calls
        if "check_for_daily_reset" in content and "reset_weekly_stats()" in content:
            logger.info("Reset function calls already present in main function")
            return True
        
        # Look for the main function
        main_pattern = re.compile(r'def\s+main\s*\([^)]*\):.*?if\s+__name__\s*==\s*["\']__main__["\']:', re.DOTALL)
        main_match = main_pattern.search(content)
        
        if not main_match:
            logger.error("Could not find main function in the script")
            return False
        
        main_function = main_match.group(0)
        
        # Look for a good insertion point in the main function
        # Try to find the extraction_success or similar variables
        insertion_point = None
        
        patterns_to_try = [
            r'extraction_success\s*=', 
            r'export_success\s*=',
            r'success\s*=',
            r'extraction_complete',
            r'update_all_leagues',
            r'# Update complete'
        ]
        
        for pattern in patterns_to_try:
            match = re.search(pattern, main_function)
            if match:
                insertion_point = match.start()
                break
        
        if insertion_point is None:
            logger.error("Could not find suitable insertion point in main function")
            return False
        
        # Prepare the reset function calls to add
        reset_code = """
    # Check for daily/weekly resets
    logging.info("Checking for daily and weekly resets")
    current_hour = datetime.now().hour
    force_reset = current_hour >= 3  # Force reset if after 3 AM
    daily_reset = check_for_daily_reset(force_reset=force_reset)
    if daily_reset:
        logging.info("Daily reset performed")
    
    # Check for weekly reset (Monday)
    if datetime.now().weekday() == 0:  # Monday = 0
        logging.info("Today is Monday, checking for weekly reset")
        weekly_reset = reset_weekly_stats()
        if weekly_reset:
            logging.info("Weekly reset performed")
"""
        
        # Split the main function at the insertion point
        main_before = main_function[:insertion_point]
        main_after = main_function[insertion_point:]
        
        # Insert the reset code
        updated_main = main_before + reset_code + main_after
        
        # Replace the old main function with the updated one
        new_content = content.replace(main_function, updated_main)
        
        # Write the updated content back to the file
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.info("Successfully updated main function to call reset functions")
        return True
    
    except Exception as e:
        logger.error(f"Error updating main function: {e}")
        return False

def main():
    """Main function"""
    print("\n===== FIXING MAIN FUNCTION IN UPDATE SCRIPT =====")
    
    if fix_main_function():
        print("[SUCCESS] Main function updated to call reset functions automatically")
        print("\nThe scheduler will now perform daily resets at 3 AM and weekly resets on Mondays.")
    else:
        print("[FAILED] Could not update main function")
        print("\nManual intervention may be required to ensure reset functions are called.")
    
    print("\n===== FIX COMPLETE =====")

if __name__ == "__main__":
    main()
