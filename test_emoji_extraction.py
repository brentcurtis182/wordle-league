#!/usr/bin/env python3
"""
Test the emoji pattern extraction with text appended to emoji patterns
"""
import re
import logging
import sqlite3
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Sample message text with the problem pattern ("boom" appended to emoji pattern)
test_text = """Message from 9 4 9 2 3 0 4 4 7 2, Wordle 1,510 3/6

⬜🟨⬜⬜⬜
⬜🟨🟩🟨⬜
🟩🟩🟩🟩🟩boom, Thursday, August 7 2025, 8:46 AM."""

def test_old_method():
    """Test the old emoji extraction method"""
    print("TESTING OLD METHOD:")
    emoji_chars = ['🟩', '🟨', '⬛', '⬜', '⬜']
    lines = test_text.split('\n')
    emoji_lines = []
    
    for line in lines:
        # Line must contain at least one emoji character
        if any(emoji in line for emoji in emoji_chars):
            # Only include lines that are pure emoji patterns (possibly with spaces)
            cleaned_line = line.split(',')[0].strip()
            if all(c in '🟩🟨⬛⬜ ' for c in cleaned_line):
                print(f"✅ Line accepted: {cleaned_line}")
                emoji_lines.append(cleaned_line)
            else:
                print(f"❌ Line rejected: {cleaned_line}")
    
    if emoji_lines:
        emoji_pattern = '\n'.join(emoji_lines)
        print(f"Extracted emoji pattern:\n{emoji_pattern}")
        print(f"Number of emoji lines: {len(emoji_lines)}")
    else:
        print("No emoji pattern found")

def test_new_method():
    """Test the new emoji extraction method"""
    print("\nTESTING NEW METHOD:")
    emoji_chars = ['🟩', '🟨', '⬛', '⬜', '⬜']
    lines = test_text.split('\n')
    emoji_lines = []
    
    for line in lines:
        # Line must contain at least one emoji character
        if any(emoji in line for emoji in emoji_chars):
            # First split by comma to handle cases like "🟩🟩🟩🟩🟩, Saturday, August 2 2025"
            cleaned_line = line.split(',')[0].strip()
            
            # Now handle cases where text is appended without a comma like "🟩🟩🟩🟩🟩boom"
            # Extract just the emoji part by finding the longest prefix that contains only emojis and spaces
            emoji_only = ''
            for char in cleaned_line:
                if char in '🟩🟨⬛⬜ ':
                    emoji_only += char
                else:
                    # Stop once we hit a non-emoji character
                    break
            
            # If we extracted a valid emoji pattern, add it
            if emoji_only and any(emoji in emoji_only for emoji in emoji_chars):
                print(f"✅ Extracted: {emoji_only} from: {cleaned_line}")
                emoji_lines.append(emoji_only.strip())
            else:
                print(f"❌ No valid pattern in: {cleaned_line}")
    
    if emoji_lines:
        emoji_pattern = '\n'.join(emoji_lines)
        print(f"Extracted emoji pattern:\n{emoji_pattern}")
        print(f"Number of emoji lines: {len(emoji_lines)}")
    else:
        print("No emoji pattern found")

def run_extraction_on_nanna():
    """Connect to the database and check Nanna's emoji pattern"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get today's Wordle number
        ref_date = datetime(2025, 7, 31).date()
        ref_wordle = 1503
        today = datetime.now().date()
        days_since_ref = (today - ref_date).days
        todays_wordle = ref_wordle + days_since_ref
        
        print(f"\nCHECKING DATABASE FOR NANNA'S SCORE (Wordle #{todays_wordle}):")
        
        # Get Nanna's player ID
        cursor.execute("SELECT id FROM players WHERE name = 'Nanna'")
        result = cursor.fetchone()
        if not result:
            print("Nanna not found in players table")
            return
            
        nanna_id = result[0]
        print(f"Nanna's player ID: {nanna_id}")
        
        # Check if Nanna has a score for today
        cursor.execute("""
        SELECT score, emoji_pattern FROM scores 
        WHERE player_id = ? AND wordle_number = ?
        """, (nanna_id, todays_wordle))
        
        result = cursor.fetchone()
        if result:
            score, emoji_pattern = result
            print(f"Nanna's score: {score}/6")
            print(f"Emoji pattern in database:\n{emoji_pattern}")
            
            # Count lines in the emoji pattern
            if emoji_pattern:
                lines = emoji_pattern.strip().split('\n')
                print(f"Number of emoji pattern lines: {len(lines)}")
            else:
                print("No emoji pattern stored")
        else:
            print(f"No score found for Nanna for Wordle #{todays_wordle}")
            
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_old_method()
    test_new_method()
    run_extraction_on_nanna()
    
    print("\nNow let's run a manual extraction on the test message:")
    from direct_hidden_extraction import extract_with_hidden_elements
    
    # Test with our sample text
    league_id = 2  # Assuming league_id 2 for Wordle Gang
    results = extract_with_hidden_elements([test_text], league_id, silent=False)
    print(f"\nExtraction result: {results}")
