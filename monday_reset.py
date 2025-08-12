#!/usr/bin/env python3
"""
Monday Reset for Wordle League
A simple script that forces the Monday reset for the Wordle League website.
"""

import os
import sqlite3
import logging
import subprocess
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to perform Monday reset"""
    print("\n===== MONDAY RESET SCRIPT =====")
    print(f"Current date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Current weekday: {datetime.now().strftime('%A')}")
    print("==============================\n")
    
    try:
        # 1. Update all leagues
        print("1. Updating all leagues...")
        subprocess.run(["python", "update_all_correct_structure.py"], check=True)
        print("   [SUCCESS] All leagues updated")
        
        # 2. Fix tabs
        print("\n2. Fixing tabs...")
        subprocess.run(["python", "fix_tabs.py"], check=True)
        print("   [SUCCESS] Tabs fixed")
        
        # 3. Run safeguard
        print("\n3. Running safeguard...")
        subprocess.run(["python", "scheduler_safeguard.py"], check=True)
        print("   [SUCCESS] Safeguard completed")
        
        print("\n===== MONDAY RESET COMPLETED =====")
        print("The website should now be reset for the new week.")
        print("Check the website to confirm the reset has been applied.")
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        print("The reset process failed. Please check the logs for details.")

if __name__ == "__main__":
    main()
