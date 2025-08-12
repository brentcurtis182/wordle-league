"""
Simple script to check if Vox has any scores in the PAL league database
and to analyze the phone number mapping issue.
"""

import sqlite3
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(message)s')

def check_database():
    """Check scores for Vox in PAL league"""
    conn = sqlite3.connect('wordle_league.db')
    cursor = conn.cursor()
    
    # Get column names
    cursor.execute("PRAGMA table_info(scores)")
    columns = [col[1] for col in cursor.fetchall()]
    logging.info(f"Scores table columns: {columns}")
    
    # Check for Vox scores in PAL league
    cursor.execute("""
    SELECT * FROM scores 
    WHERE player_name = ? AND league_id = ? 
    ORDER BY wordle_num DESC LIMIT 10
    """, ("Vox", 3))
    
    vox_scores = cursor.fetchall()
    logging.info(f"\nVox scores in PAL league (count: {len(vox_scores)}):")
    for score in vox_scores:
        logging.info(score)
    
    # Check if Brent's number appears in any scores for PAL league
    cursor.execute("""
    SELECT * FROM scores 
    WHERE league_id = 3
    ORDER BY wordle_num DESC LIMIT 20
    """)
    
    pal_scores = cursor.fetchall()
    logging.info(f"\nAll recent PAL league scores (count: {len(pal_scores)}):")
    for score in pal_scores:
        logging.info(score)
    
    conn.close()

def analyze_phone_mappings():
    """Test phone number extraction and mapping"""
    # Test cases with different phone formats
    test_phones = [
        "(858) 735-9353",  # Standard format
        "858-735-9353",    # Dashed format
        "8587359353",      # Digits only
        "1-858-735-9353",  # With country code
        "+1(858)735-9353", # International format
        "‎(858) 735-9353‎", # With invisible unicode chars
        "\u202a(858) 735-9353\u202c"  # With direction control chars
    ]
    
    logging.info("\nPhone number extraction and mapping test:")
    for phone in test_phones:
        # Clean the phone number (similar to what's in the main script)
        cleaned = re.sub(r'[\u200e\u200f\u202a\u202b\u202c\u202d\u202e]', '', phone)
        digits_only = ''.join(filter(str.isdigit, cleaned))
        
        # Check if this would map to Vox in PAL league
        is_vox = digits_only == "8587359353"
        
        logging.info(f"Original: '{phone}'")
        logging.info(f"  Unicode repr: {repr(phone)}")
        logging.info(f"  Cleaned: '{cleaned}'")
        logging.info(f"  Digits only: '{digits_only}'")
        logging.info(f"  Would map to Vox in PAL league: {is_vox}\n")

if __name__ == "__main__":
    logging.info("=== Checking Vox scores in database ===")
    check_database()
    
    logging.info("\n=== Testing phone number extraction and mapping ===")
    analyze_phone_mappings()
