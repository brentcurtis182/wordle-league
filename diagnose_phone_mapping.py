#!/usr/bin/env python3
"""
Diagnose phone number mapping issues between leagues
"""
import sqlite3
import re
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def extract_player_name_from_phone(phone_number, league_id=1):
    """Extract player name from phone number for a specific league"""
    logging.info(f"Looking up phone number {phone_number} for league {league_id}")
    
    # Clean phone number to digits-only for consistency
    digits_only = ''.join(filter(str.isdigit, phone_number))
    logging.info(f"Cleaned phone number: '{phone_number}' (digits: {digits_only})")
    
    # Main league mappings
    if league_id == 1:
        phone_to_name = {
            "3109263555": "Joanna",
            "9492304472": "Nanna",
            "8587359353": "Brent",
            "7603341190": "Malia",
            "7608462302": "Evan"
        }
        
        if digits_only in phone_to_name:
            player_name = phone_to_name[digits_only]
            logging.info(f"Found player {player_name} for phone {digits_only} in main league mapping")
            return player_name
    
    # PAL league mappings
    elif league_id == 3:
        phone_to_name = {
            "8587359353": "Vox",  # Map Brent's number to Vox in PAL league
            "7604206113": "Fuzwuz",
            "7605830059": "Pants",
            "4698345364": "Starslider"
        }
        
        if digits_only in phone_to_name:
            player_name = phone_to_name[digits_only]
            logging.info(f"Found player {player_name} for phone {digits_only} in PAL league mapping")
            return player_name
    
    return None

def simulate_extraction():
    """Simulate extraction from both leagues to see any interference"""
    print("\n=== SIMULATING EXTRACTION SCENARIO ===")
    
    # Test phone number (Brent's number)
    test_phone = "8587359353"
    formatted_phone = "(858) 735-9353"
    
    # Scenario 1: Main league first, then PAL league
    print("\nScenario 1: Main league first, then PAL league")
    main_player = extract_player_name_from_phone(test_phone, league_id=1)
    print(f"Extracted player from main league: {main_player}")
    pal_player = extract_player_name_from_phone(test_phone, league_id=3)
    print(f"Extracted player from PAL league: {pal_player}")
    
    # Scenario 2: PAL league first, then main league
    print("\nScenario 2: PAL league first, then main league")
    pal_player = extract_player_name_from_phone(test_phone, league_id=3)
    print(f"Extracted player from PAL league: {pal_player}")
    main_player = extract_player_name_from_phone(test_phone, league_id=1)
    print(f"Extracted player from main league: {main_player}")
    
    # Scenario 3: Test with formatted phone number
    print("\nScenario 3: Using formatted phone number")
    main_player = extract_player_name_from_phone(formatted_phone, league_id=1)
    print(f"Extracted player from main league with formatted phone: {main_player}")
    pal_player = extract_player_name_from_phone(formatted_phone, league_id=3)
    print(f"Extracted player from PAL league with formatted phone: {pal_player}")

def examine_threads(threads, league_id):
    """Simulate examining threads for a league"""
    print(f"\n=== EXAMINING THREADS FOR LEAGUE {league_id} ===")
    
    # For this simulation, we'll use fake thread data
    phone_numbers = []
    
    if league_id == 1:  # Main league
        phone_numbers = ["8587359353", "3109263555", "7603341190"]
    elif league_id == 3:  # PAL league
        phone_numbers = ["8587359353", "7604206113", "4698345364"]  # Same first number
    
    print(f"Thread participants for league {league_id}:")
    for phone in phone_numbers:
        player = extract_player_name_from_phone(phone, league_id)
        print(f"  Phone: {phone} -> Player: {player}")
        
    print(f"Checking for Wordle scores in league {league_id}:")
    # Simulate finding scores in hidden elements
    for phone in phone_numbers:
        player = extract_player_name_from_phone(phone, league_id)
        if player:
            print(f"  Found score for player: {player}")
            # Simulate saving to database
            print(f"  Would save score for {player} in league {league_id}")

def debug_phone_mapping():
    """Debug overall phone mapping process"""
    print("\n=== DEBUGGING PHONE MAPPING FLOW ===")
    
    # Test both leagues in sequence like the main script would
    leagues = [
        {"name": "Wordle Warriorz", "id": 1},
        {"name": "Wordle PAL", "id": 3}
    ]
    
    for league in leagues:
        print(f"\nProcessing league: {league['name']} (ID: {league['id']})")
        # Simulate thread extraction and processing
        examine_threads(["fake_thread"], league['id'])
        
if __name__ == "__main__":
    print("===== PHONE MAPPING DIAGNOSTIC TOOL =====")
    simulate_extraction()
    debug_phone_mapping()
    print("\nDiagnostic complete.")
