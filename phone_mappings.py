#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Phone number to player name mappings for all leagues
This is the SINGLE SOURCE OF TRUTH for all phone mappings
All extraction scripts should import from this file
"""

# Phone mappings by league ID
# Format: "cleaned_phone_number": "player_name"
# Note: Phone numbers should have NO spaces, dashes, or parentheses
# If a number has country code, include it (e.g. "18587359353")
# If a number is 10 digits without country code, just use those digits (e.g. "8587359353")
PHONE_MAPPINGS = {
    # League 1: Wordle Warriorz
    1: {
        # Each phone number maps to exactly ONE player in this league
        "18587359353": "Brent",
        "17603341190": "Malia",
        "17608462302": "Evan",      # This is Evan's phone number
        "13109263555": "Joanna",
        "19492304472": "Nanna",
    },
    
    # League 2: Wordle Gang
    2: {
        # Each phone number maps to exactly ONE player in this league
        "18587359353": "Brent",
        "13102004244": "Ana",
        "17148228341": "Kaylie",
        "13109263555": "Joanna",
        "17148030122": "Keith",
        "13107953164": "Rochelle",
        "13102661718": "Will",
    },
    
    # League 3: Wordle PAL
    3: {
        # Each phone number maps to exactly ONE player in this league
        "18587359353": "Vox",
        "17604206113": "Fuzwuz",
        "17605830059": "Pants",
        "14698345364": "Starslider",
    },
    
    # League 4: Wordle Party
    4: {
        # Each phone number maps to exactly ONE player in this league
        "17606825666": "Matt",
        "17605830059": "Jess",
        "17608462302": "Kinley",
        "18587359353": "Brent",
    },
    
    # League 5: Wordle Vball
    5: {
        # Each phone number maps to exactly ONE player in this league
        "17604206113": "Jason",
        "17603341190": "Shawn",
        "18587359353": "Brent",
    }
}

def get_player_name(phone_number, league_id):
    """
    Get player name for a phone number in a specific league
    
    Args:
        phone_number (str): The phone number to look up
        league_id (int): The league ID to check in
    
    Returns:
        str: Player name if found, None if not found
    """
    if not phone_number:
        return None
    
    # Normalize phone number by removing non-digits
    digits_only = ''.join(c for c in phone_number if c.isdigit())
    
    # Try with and without leading 1 (country code)
    if league_id in PHONE_MAPPINGS:
        # Try direct match
        if digits_only in PHONE_MAPPINGS[league_id]:
            return PHONE_MAPPINGS[league_id][digits_only]
        
        # Try adding leading 1 if it's missing and length is 10
        if len(digits_only) == 10:
            with_country_code = "1" + digits_only
            if with_country_code in PHONE_MAPPINGS[league_id]:
                return PHONE_MAPPINGS[league_id][with_country_code]
        
        # Try without leading 1 if it has one and length is 11
        if len(digits_only) == 11 and digits_only[0] == "1":
            without_country_code = digits_only[1:]
            if without_country_code in PHONE_MAPPINGS[league_id]:
                return PHONE_MAPPINGS[league_id][without_country_code]
    
    return None

def print_all_mappings():
    """Print all mappings for debugging"""
    print("Phone number mappings by league:\n")
    
    for league_id, mappings in PHONE_MAPPINGS.items():
        league_name = ""
        if league_id == 1:
            league_name = "Wordle Warriorz"
        elif league_id == 2:
            league_name = "Wordle Gang"
        elif league_id == 3:
            league_name = "Wordle PAL"
        elif league_id == 4:
            league_name = "Wordle Party"
        elif league_id == 5:
            league_name = "Wordle Vball"
        
        print(f"League {league_id}: {league_name}")
        print("-------------------------")
        
        for phone, name in mappings.items():
            print(f"  {phone} -> {name}")
        
        print()

if __name__ == "__main__":
    print_all_mappings()
