#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test the centralized phone mappings
"""

import logging
from phone_mappings import get_player_name, print_all_mappings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

def test_with_various_formats():
    """Test phone mappings with various formats to ensure robustness"""
    test_cases = [
        # League 1 test cases
        (1, "7608462302", "Evan"),     # Direct match for Evan's number
        (1, "17608462302", "Evan"),    # With country code
        (1, "(760) 846-2302", "Evan"), # Formatted number
        (1, "760 846 2302", "Evan"),   # Spaces
        (1, "760-846-2302", "Evan"),   # Dashes
        
        # League 3 test cases
        (3, "8587359353", "Vox"),      # Should map to Vox in PAL league
        (3, "18587359353", "Vox"),     # With country code
        
        # Test cases that should fail
        (1, "9999999999", None),       # Non-existent number
        (2, "7608462302", None),       # Evan's number in wrong league
    ]
    
    print("Testing phone number mappings with various formats:")
    print("==================================================")
    
    for league_id, phone, expected in test_cases:
        result = get_player_name(phone, league_id)
        status = "PASS" if result == expected else "FAIL"
        print(f"League {league_id}, Phone: {phone}, Expected: {expected}, Got: {result} - {status}")

if __name__ == "__main__":
    print("\nALL PHONE MAPPINGS:")
    print("==================")
    print_all_mappings()
    
    print("\nTEST RESULTS:")
    print("============")
    test_with_various_formats()
