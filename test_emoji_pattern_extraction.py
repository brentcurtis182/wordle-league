#!/usr/bin/env python3
# Test script to verify emoji pattern extraction logic

import sqlite3
import re
import logging
import sys
from datetime import datetime

# Fix for Unicode/emoji display in Windows command prompt
sys.stdout.reconfigure(encoding='utf-8')
# Or use this alternate approach if the above doesn't work
# import io
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_emoji_extraction():
    """Test function to verify the improved emoji pattern extraction logic"""
    
    # Sample message content with problematic emoji patterns (including date/time text)
    test_messages = [
        """
        Wordle 1503 4/6
        
        🟨⬜⬜⬜⬜
        ⬜⬜🟩⬜⬜
        ⬜🟩🟩🟩🟩
        🟩🟩🟩🟩🟩
        Sent at 10:45 PM
        """,
        
        """
        Wordle 1503 3/6
        
        ⬜🟨⬜⬜⬜
        🟩🟩🟩⬜🟩
        🟩🟩🟩🟩🟩
        August 1, 2025
        """,
        
        """
        Wordle 1503 5/6
        
        ⬜⬜⬜⬜🟨
        ⬜⬜⬜🟨⬜
        ⬜🟨⬜⬜⬜
        ⬜🟩🟩🟩🟩
        🟩🟩🟩🟩🟩
        """
    ]
    
    for i, message_content in enumerate(test_messages):
        print(f"\nTesting message #{i+1}:")
        print("=" * 40)
        print(message_content)
        print("-" * 40)
        
        # Extract emoji pattern using the improved logic
        emoji_pattern = extract_emoji_pattern(message_content)
        
        print("Extracted pattern:")
        print(emoji_pattern if emoji_pattern else "No pattern extracted")
        print("=" * 40)
        
    # Test with a real database entry if available
    test_with_database()
    
def extract_emoji_pattern(message_content):
    """Extract emoji pattern using the improved logic from integrated_auto_update_multi_league.py"""
    
    emoji_pattern = None
    if '\n' in message_content:
        lines = message_content.split('\n')
        # Look for emoji pattern in the next few lines after the Wordle score line
        emoji_lines = []
        in_emoji_pattern = False
        
        # IMPROVED: More strict pattern validation for emoji lines
        # Regex to match valid emoji pattern lines (must contain only emojis and whitespace)
        valid_emoji_pattern = re.compile(r'^[🟩⬛⬜🟨\s]+$')
        
        # Search through the lines to find and collect all emoji pattern lines
        for i in range(1, min(len(lines), 15)):  # Extended range to catch all potential emoji lines
            pattern_part = lines[i].strip()
            
            # STRICT CHECK 1: Line must contain at least one Wordle emoji
            has_wordle_emoji = '🟩' in pattern_part or '⬛' in pattern_part or '⬜' in pattern_part or '🟨' in pattern_part
            
            # STRICT CHECK 2: Line must contain ONLY Wordle emojis and whitespace
            # This prevents date/time text from being included in patterns
            is_valid_pattern_line = bool(valid_emoji_pattern.match(pattern_part))
            
            # Accept line only if it passes BOTH checks
            if has_wordle_emoji and is_valid_pattern_line:
                emoji_lines.append(pattern_part)
                in_emoji_pattern = True
            elif in_emoji_pattern:
                # If we've already found emoji lines and now hit a non-emoji line, stop
                break
        
        # Join all emoji lines into a single pattern
        if emoji_lines:
            emoji_pattern = '\n'.join(emoji_lines)
            logging.info(f"Extracted complete emoji pattern with {len(emoji_lines)} lines")
    
    return emoji_pattern

def test_with_database():
    """Test by reading and updating problematic emoji patterns in the test database"""
    
    try:
        # Connect to the test database
        conn = sqlite3.connect('wordle_league_test.db')
        cursor = conn.cursor()
        
        # Find players with known emoji pattern issues in Wordle Warriorz league
        problematic_players = ['Malia', 'Evan']
        
        # Query recent scores for these players
        cursor.execute("""
        SELECT s.id, p.name, s.wordle_num, s.score, s.emoji_pattern
        FROM scores s
        JOIN players p ON s.player_name = p.name AND s.league_id = p.league_id
        WHERE p.name IN (?, ?) AND s.league_id = 1 
        ORDER BY s.wordle_num DESC
        LIMIT 5
        """, (problematic_players[0], problematic_players[1]))
        
        results = cursor.fetchall()
        
        if not results:
            print("\nNo problematic emoji patterns found in database to test")
            return
        
        print("\nTesting with database entries:")
        print("=" * 40)
        
        for row in results:
            score_id, name, wordle_num, score, original_pattern = row
            
            if not original_pattern:
                continue
            
            print(f"Player: {name}, Wordle: {wordle_num}, Score: {score}")
            print("Original emoji pattern:")
            print(original_pattern)
            
            # Apply the new extraction logic to clean up the pattern
            cleaned_pattern = extract_emoji_pattern(original_pattern)
            
            print("Cleaned emoji pattern:")
            print(cleaned_pattern if cleaned_pattern else "No pattern extracted")
            
            # Update the test database with the cleaned pattern
            if cleaned_pattern and cleaned_pattern != original_pattern:
                cursor.execute("""
                UPDATE scores 
                SET emoji_pattern = ? 
                WHERE id = ?
                """, (cleaned_pattern, score_id))
                conn.commit()
                print("✓ Updated in test database")
            
            print("-" * 40)
        
        conn.close()
            
    except Exception as e:
        logging.error(f"Database test error: {e}")

if __name__ == "__main__":
    print("Testing improved emoji pattern extraction logic")
    test_emoji_extraction()
