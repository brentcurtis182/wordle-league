#!/usr/bin/env python3
"""
Test the fixed phone number mapping function to verify it works correctly
Focusing specifically on Evan's phone number mapping which was previously broken
"""
import sys
import os
import logging
import re
import sqlite3
import csv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Import our fixed function from the extraction script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from extract_scores_multi_league import get_player_by_phone_for_league

def test_phone_mappings():
    """Test phone mappings for each league using our fixed function"""
    print("\n===== TESTING PHONE MAPPINGS =====\n")
    
    # Test data for each league
    test_cases = [
        # Wordle Warriorz (League 1)
        {"phone": "18587359353", "league_id": 1, "expected": "Brent"},
        {"phone": "17603341190", "league_id": 1, "expected": "Malia"},
        {"phone": "17608462302", "league_id": 1, "expected": "Evan"},  # This was broken
        {"phone": "13109263555", "league_id": 1, "expected": "Joanna"},
        {"phone": "19492304472", "league_id": 1, "expected": "Nanna"},
        
        # Wordle Gang (League 2)
        {"phone": "18587359353", "league_id": 2, "expected": "Brent"},
        {"phone": "13102004244", "league_id": 2, "expected": "Ana"},
        {"phone": "17148228341", "league_id": 2, "expected": "Kaylie"},
        
        # PAL League (League 3)
        {"phone": "18587359353", "league_id": 3, "expected": "Vox"},
        {"phone": "17604206113", "league_id": 3, "expected": "Fuzwuz"},
        {"phone": "17605830059", "league_id": 3, "expected": "Pants"},
        {"phone": "14698345364", "league_id": 3, "expected": "Starslider"}
    ]
    
    # Run tests
    success = 0
    failure = 0
    
    for test in test_cases:
        phone = test["phone"]
        league_id = test["league_id"]
        expected = test["expected"]
        
        # Get the actual mapping using our fixed function
        actual = get_player_by_phone_for_league(phone, league_id)
        
        # Check result
        if actual == expected:
            result = "PASS"
            success += 1
        else:
            result = "FAIL"
            failure += 1
            
        league_name = "Wordle Warriorz" if league_id == 1 else "Wordle Gang" if league_id == 2 else "PAL League"
        print(f"{result}: {phone} -> {actual} (expected: {expected}) in {league_name}")
    
    # Summary
    print(f"\n{success} tests passed, {failure} tests failed")
    return success, failure

def verify_evan_phone_mapping():
    """Specifically verify that Evan's phone mapping is fixed"""
    print("\n===== VERIFYING EVAN'S PHONE MAPPING =====\n")
    
    # Evan's correct phone number
    evan_phone = "17608462302"
    
    # Check if it maps correctly
    result = get_player_by_phone_for_league(evan_phone, 1)
    
    if result == "Evan":
        print(f"SUCCESS: {evan_phone} correctly maps to Evan in the main league")
        return True
    else:
        print(f"FAILURE: {evan_phone} maps to {result} instead of Evan in the main league")
        return False

def test_csv_loading():
    """Test that CSV files are loaded correctly"""
    print("\n===== TESTING CSV FILE LOADING =====\n")
    
    csv_files = {
        1: 'familyPlayers.csv',              # Wordle Warriorz
        2: 'familyPlayers - wordleGang.csv', # Wordle Gang
        3: 'familyPlayers - wordlePal.csv'   # PAL League
    }
    
    for league_id, csv_path in csv_files.items():
        league_name = "Wordle Warriorz" if league_id == 1 else "Wordle Gang" if league_id == 2 else "PAL League"
        
        print(f"Testing CSV for {league_name}: {csv_path}")
        
        if not os.path.exists(csv_path):
            print(f"  Error: CSV file not found: {csv_path}")
            continue
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)  # Skip header row
                
                rows = list(reader)
                print(f"  Found {len(rows)} player mappings")
                
                # Print first few mappings
                for i, row in enumerate(rows[:3]):  # Show up to 3 mappings
                    if len(row) >= 2:
                        print(f"  {row[0]} -> {row[1]}")
                        
                if len(rows) > 3:
                    print(f"  ... and {len(rows) - 3} more players")
        except Exception as e:
            print(f"  Error reading CSV file: {e}")
    
    return True

if __name__ == "__main__":
    print("Testing the fixed phone mapping function")
    
    # Test CSV loading
    test_csv_loading()
    
    # Test Evan's mapping specifically
    evan_ok = verify_evan_phone_mapping()
    
    # Test all mappings
    success, failure = test_phone_mappings()
    
    # Summary
    print("\n===== SUMMARY =====\n")
    
    if evan_ok:
        print("✅ Evan's phone mapping is working correctly")
    else:
        print("❌ Evan's phone mapping is still broken")
        
    if failure == 0:
        print(f"✅ All {success} phone mappings tested successfully")
    else:
        print(f"❌ {failure} phone mappings still failing")
        
    print("\nFix should now be applied. Run the multi-league scheduler to verify it extracts Evan's score.")
    print("\n==== TESTING PAL LEAGUE MAPPINGS ====")
    for phone in test_phones_pal:
        player = extract_player_name_from_phone(phone, league_id=3)
        print(f"Phone: {phone} -> Player: {player}")

if __name__ == "__main__":
    test_phone_mappings()
