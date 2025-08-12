#!/usr/bin/env python
# Enhanced failed attempt detection script for debugging X/6 score issues
# This script does NOT modify the main extraction code, only helps diagnose issues

import re
import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("x6_detection.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def check_evan_message_format():
    """Read the conversation files to examine Evan's specific message format"""
    try:
        # Read the conversation files
        files_to_check = [
            "conversation_1.txt",
            "conversation_1_annotated.txt",
            "conversation_2.txt",
            "conversation_2_annotated.txt"
        ]
        
        evans_messages = []
        for filename in files_to_check:
            try:
                with open(filename, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    
                    # Find sections that might be from Evan
                    evan_sections = re.findall(r'(?i)(?:evan|From Evan:).*?(?:Wordle.*?\d+.*?(?:\d|x)/6)', content, re.DOTALL)
                    if evan_sections:
                        evans_messages.extend(evan_sections)
                        logging.info(f"Found {len(evan_sections)} potential Evan messages in {filename}")
            except FileNotFoundError:
                logging.warning(f"File {filename} not found")
                continue
                
        if evans_messages:
            logging.info(f"Found {len(evans_messages)} total messages that might be from Evan")
            for i, msg in enumerate(evans_messages):
                logging.info(f"\n--- Evan's message {i+1} ---")
                logging.info(msg[:200] + "..." if len(msg) > 200 else msg)
                
                # Look specifically for Wordle score formats
                wordle_mentions = re.findall(r'Wordle.*?\d+.*?(?:\d|x|X)/6', msg, re.IGNORECASE)
                if wordle_mentions:
                    logging.info("Wordle score format found:")
                    for mention in wordle_mentions:
                        logging.info(f"  {mention}")
        else:
            logging.warning("No messages from Evan found")
    except Exception as e:
        logging.error(f"Error checking Evan's messages: {e}")

def test_enhanced_detection(sample_text=None):
    """Test more robust X/6 detection patterns"""
    
    # Current patterns in the system
    current_patterns = [
        re.compile(r'Wordle\s+#?([\d,]+)\s+X/6'),
        re.compile(r'Wordle[:\s]+#?([\d,]+)\s*[:\s]+X/6'),
        re.compile(r'Wordle[^\d]*([\d,]+)[^\d]*X/6')
    ]
    
    # Enhanced patterns that could help
    enhanced_patterns = [
        # Same patterns but case-insensitive for the X
        re.compile(r'Wordle\s+#?([\d,]+)\s+[xX]/6', re.IGNORECASE),
        re.compile(r'Wordle[:\s]+#?([\d,]+)\s*[:\s]+[xX]/6', re.IGNORECASE),
        re.compile(r'Wordle[^\d]*([\d,]+)[^\d]*[xX]/6', re.IGNORECASE),
        
        # Additional patterns for possible variations
        re.compile(r'Wordle\s+#?([\d,]+)\s+(?:failed|fail|x|X).*?6', re.IGNORECASE),
        re.compile(r'Wordle\s+#?([\d,]+)\s+.*?not\s+(?:solve|solved)', re.IGNORECASE)
    ]
    
    # Sample texts to test against if none provided
    if not sample_text:
        sample_texts = [
            "Wordle 1500 X/6",
            "Wordle #1500 X/6",
            "Wordle 1500 x/6",
            "Wordle #1,500 x/6",
            "Wordle 1500: X/6",
            "Wordle #1500: X/6",
            "Wordle 1500 - X/6",
            "wordle 1500 x/6",
            "Wordle 1500 failed in 6",
            "Wordle 1500 not solved",
            "Wordle #1500 6/6" # This should NOT be detected as X/6
        ]
    else:
        sample_texts = [sample_text]
    
    logging.info("Testing current system patterns:")
    for sample in sample_texts:
        logging.info(f"\nSample: {sample}")
        
        # Test current patterns
        current_matches = []
        for pattern in current_patterns:
            matches = pattern.findall(sample)
            if matches:
                current_matches.extend(matches)
                logging.info(f"  ✓ Matched current pattern: {pattern.pattern}")
            
        if not current_matches:
            logging.warning(f"  ✗ No matches with current patterns")
        
        # Test enhanced patterns
        enhanced_matches = []
        for pattern in enhanced_patterns:
            matches = pattern.findall(sample)
            if matches:
                enhanced_matches.extend(matches)
                logging.info(f"  ✓ Matched enhanced pattern: {pattern.pattern}")
                
        if not enhanced_matches:
            logging.warning(f"  ✗ No matches with enhanced patterns")
            
def suggest_fixes():
    """Suggest code changes to fix X/6 detection without breaking existing functionality"""
    
    logging.info("\nRecommended changes to improve X/6 detection:")
    logging.info("1. Add case-insensitive flag to the existing patterns:")
    logging.info("""
    failed_patterns = [
        re.compile(r'Wordle\\s+#?([\\d,]+)\\s+X/6', re.IGNORECASE),  # Standard format
        re.compile(r'Wordle[:\\s]+#?([\\d,]+)\\s*[:\\s]+X/6', re.IGNORECASE),  # With colons
        re.compile(r'Wordle[^\\d]*([\\d,]+)[^\\d]*X/6', re.IGNORECASE)  # Very flexible
    ]
    """)
    
    logging.info("2. For even more robustness, add these additional patterns:")
    logging.info("""
    # Additional patterns for special cases
    additional_failed_patterns = [
        re.compile(r'Wordle\\s+#?([\\d,]+)\\s+(?:failed|fail).*?6', re.IGNORECASE),
        re.compile(r'Wordle\\s+#?([\\d,]+)\\s+.*?not\\s+(?:solve|solved)', re.IGNORECASE)
    ]
    failed_patterns.extend(additional_failed_patterns)
    """)
    
    logging.info("\nHow to implement safely:")
    logging.info("1. Make a backup of integrated_auto_update.py")
    logging.info("2. Add only the re.IGNORECASE flag to existing patterns first")
    logging.info("3. Test with known problematic messages")
    logging.info("4. If needed, add the additional patterns")
    logging.info("5. Consider adding this to the daily check script to catch issues early:")
    logging.info("""
    def verify_x6_scores():
        \"\"\"Verify all X/6 scores are correctly stored as 7\"\"\"
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Find all scores with 6-row emoji patterns but score=6 (should be 7)
        cursor.execute('''
            SELECT p.name, s.wordle_number, s.score, s.emoji_pattern 
            FROM score s 
            JOIN player p ON s.player_id = p.id 
            WHERE s.score = 6 
            AND (
                s.emoji_pattern LIKE '%\\n%\\n%\\n%\\n%\\n%' 
                OR s.emoji_pattern LIKE '%⬛%⬛%⬛%⬛%⬛\\n%'
            )
        ''')
        
        potential_issues = cursor.fetchall()
        if potential_issues:
            for issue in potential_issues:
                name, wordle_num, score, pattern = issue
                logging.warning(f"Potential X/6 issue: {name}, Wordle #{wordle_num}, stored as {score}/6")
                if pattern:
                    rows = pattern.count('\\n') + 1
                    logging.warning(f"  Pattern has {rows} rows, last row: {pattern.split('\\n')[-1]}")
                    
        conn.close()
    """)

if __name__ == "__main__":
    logging.info("===== Enhanced X/6 Detection Analysis =====")
    
    # Check Evan's message format
    logging.info("\nChecking Evan's message format in conversation files...")
    check_evan_message_format()
    
    # Test enhanced detection patterns
    logging.info("\nTesting enhanced X/6 detection patterns...")
    test_enhanced_detection()
    
    # Provide recommendations
    logging.info("\nGenerating recommendations...")
    suggest_fixes()
