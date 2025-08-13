import os
import re
from bs4 import BeautifulSoup
import sqlite3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

def extract_emoji_patterns():
    """Extract emoji patterns from HTML files for Wordle #1500"""
    html_files = [f for f in os.listdir() if f.startswith('conversation') and f.endswith('.html')]
    
    if not html_files:
        logging.error("No conversation HTML files found")
        return {}
    
    print(f"Found {len(html_files)} HTML files: {', '.join(html_files)}")
    extracted_patterns = {}
    
    for html_file in html_files:
        logging.info(f"Processing {html_file}")
        
        with open(html_file, 'r', encoding='utf-8') as file:
            try:
                content = file.read()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Debug: Check if file contains Wordle 1500 mention
                if "Wordle 1500" in content:
                    print(f"Found 'Wordle 1500' mention in {html_file}")
                
                # Look for all elements that might contain Wordle results
                # Try multiple selector approaches
                hidden_elements = soup.select('.cdk-visually-hidden')
                if not hidden_elements:
                    print(f"No .cdk-visually-hidden elements found in {html_file}")
                    # Try other potential classes
                    hidden_elements = soup.select('[class*="hidden"]') 
                
                # Check raw text content for emojis
                emoji_pattern = re.search(r'((?:[⬛🟨🟩]{5}\s*\n*){1,6})', content)
                if emoji_pattern:
                    print(f"Found direct emoji pattern in {html_file}: {emoji_pattern.group(1)}")
                
                for element in hidden_elements:
                    text = element.text.strip()
                    
                    # Debug: Print text content of elements to inspect
                    text_preview = text[:100].replace('\n', '\\n') + ('...' if len(text) > 100 else '')
                    print(f"Element in {html_file}: {text_preview}")
                    
                    # Try to find any Wordle pattern format
                    wordle_pattern = re.search(r'Wordle (\d+) (\d|X)/6', text)
                    if wordle_pattern:
                        wordle_num = wordle_pattern.group(1)
                        score = wordle_pattern.group(2)
                        print(f"Found Wordle {wordle_num} with score {score} in {html_file}")
                    
                    # Extract phone number if present
                    phone_match = re.search(r'\+1\s*\((\d{3})\)\s*(\d{3})-(\d{4})', text)
                    
                    # Find any emoji pattern - looking for blocks of square emojis
                    pattern_lines = []
                    lines = text.split('\n')
                    
                    for line in lines:
                        # Match any line with 5 emoji squares (more flexible pattern)
                        if re.search(r'[⬛⬜⬜🟨🟩◼◻◽◾▪▫️]{5}', line):
                            pattern_lines.append(line.strip())
                    
                    if pattern_lines:
                        print(f"Found pattern lines in {html_file}: {pattern_lines}")
                    
                    if phone_match and pattern_lines:
                        phone = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"
                        emoji_pattern = '\n'.join(pattern_lines)
                        
                        logging.info(f"Found complete pattern for {phone} in {html_file}")
                        extracted_patterns[phone] = emoji_pattern
                        print(f"\nComplete match - Phone: {phone}")
                        print(f"Pattern:\n{emoji_pattern}")
            except Exception as e:
                logging.error(f"Error processing {html_file}: {e}")
    
    return extracted_patterns

def get_player_names():
    """Get mapping of phone numbers to player names from the database"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT phone, name FROM player")
        players = {row['phone']: row['name'] for row in cursor.fetchall()}
        
        conn.close()
        return players
    except Exception as e:
        logging.error(f"Error getting player names: {e}")
        return {}

def main():
    # Extract patterns
    patterns = extract_emoji_patterns()
    
    if not patterns:
        logging.error("No patterns found!")
        
        # If no patterns found, try to find any emoji patterns in the HTML files
        print("\nTrying alternative approach: searching for any emoji patterns...")
        for file in os.listdir():
            if file.endswith('.html'):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        emoji_matches = re.findall(r'([⬛🟨🟩⬜]{5,})', content)
                        if emoji_matches:
                            print(f"\nFound emoji pattern in {file}:")
                            for match in emoji_matches[:3]:  # Show up to 3 matches
                                print(match)
                except Exception as e:
                    print(f"Error reading {file}: {e}")
        return
    
    # Get player names
    players = get_player_names()
    
    # Display the extracted patterns with player names
    print("\n===== EXTRACTED PATTERNS FOR WORDLE #1500 =====")
    for phone, pattern in patterns.items():
        player_name = players.get(phone, "Unknown Player")
        print(f"\n{player_name} ({phone}):")
        print(pattern)

if __name__ == "__main__":
    main()
