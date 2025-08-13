import os
import re
from bs4 import BeautifulSoup
import sqlite3
import logging
import sys
import io

# Configure UTF-8 for output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_player_names():
    """Get mapping of phone numbers to player names from the database"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT phone_number, name FROM player")
        # Create two mappings - one with raw digits and one with formatted numbers
        raw_players = {}
        formatted_players = {}
        for row in cursor.fetchall():
            name = row['name']
            phone_raw = row['phone_number']
            if phone_raw.startswith('1'):
                phone_raw = phone_raw[1:]  # Remove leading 1 if present
            
            # Store raw format (just digits)
            raw_players[phone_raw] = name
            
            # Store formatted version
            if len(phone_raw) == 10:
                formatted = f"({phone_raw[:3]}) {phone_raw[3:6]}-{phone_raw[6:]}"
                formatted_players[formatted] = name
        
        conn.close()
        return {'raw': raw_players, 'formatted': formatted_players}
    except Exception as e:
        logging.error(f"Error getting player names: {e}")
        return {'raw': {}, 'formatted': {}}

def extract_patterns_from_html():
    """Extract emoji patterns from HTML files focusing on the known approach"""
    players_dict = get_player_names()
    raw_players = players_dict['raw']
    formatted_players = players_dict['formatted']
    html_files = [f for f in os.listdir() if f.endswith('.html')]
    
    # Store results by player name
    results = {}
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as file:
                content = file.read()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Find all hidden elements - the key to reliable extraction
                hidden_elements = soup.select('.cdk-visually-hidden')
                
                for element in hidden_elements:
                    text = element.text.strip()
                    
                    # Check if this contains Wordle 1500 data
                    if "Wordle" in text and "/6" in text and "1500" in text:
                        print(f"\nFound Wordle 1500 data in {html_file}")
                        
                        # Extract phone number (multiple formats)
                        phone_match = re.search(r'from\s+(\d[\s\d]+\d)', text)
                        phone_number = None
                        
                        if not phone_match:
                            phone_match = re.search(r'from\s+\(?(\d{3})\)?[\s-]*(\d{3})[\s-]*(\d{4})', text)
                            if phone_match:
                                phone_number = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"
                        else:
                            digits = phone_match.group(1).replace(" ", "")
                            phone_number = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
                        
                        if not phone_number:
                            # Try alternate phone formats
                            alt_phone = re.search(r'\+1\s*\((\d{3})\)\s*(\d{3})-(\d{4})', text)
                            if alt_phone:
                                phone_number = f"({alt_phone.group(1)}) {alt_phone.group(2)}-{alt_phone.group(3)}"
                        
                        if not phone_number:
                            print(f"  Could not extract phone number from: {text[:100]}...")
                            continue
                        
                        # Clean up phone number for matching
                        digits_only = re.sub(r'\D', '', phone_number)  # Remove non-digits
                        if digits_only.startswith('1'):
                            digits_only = digits_only[1:]  # Remove leading 1 if present
                            
                        # Try to match player by phone number
                        player_name = raw_players.get(digits_only)
                        if not player_name:
                            player_name = formatted_players.get(phone_number, f"Unknown Player ({phone_number})")
                            
                        print(f"  Found player: {player_name} (Phone: {phone_number}, Clean: {digits_only})")
                        
                        # Extract Wordle number
                        wordle_match = re.search(r'Wordle\s+#?([\d,]+)', text)
                        if wordle_match:
                            wordle_num = int(wordle_match.group(1).replace(',', ''))
                            print(f"  Wordle #{wordle_num}")
                        else:
                            print(f"  Could not extract Wordle number")
                        
                        # Extract score
                        score_match = re.search(r'([\dX])/6', text)
                        if score_match:
                            score_value = score_match.group(1)
                            score = 'X' if score_value.upper() == 'X' else score_value
                            print(f"  Score: {score}/6")
                        else:
                            print(f"  Could not extract score")
                        
                        # Extract emoji pattern - the key part we want
                        emoji_rows = re.findall(r'[⬛⬜🟨🟩]{5}', text)
                        
                        if emoji_rows:
                            emoji_pattern = "\n".join(emoji_rows)
                            print(f"  Player: {player_name}")
                            print(f"  Pattern ({len(emoji_rows)} rows):")
                            print(f"{emoji_pattern}")
                            
                            # Store by player name for final output
                            results[player_name] = {
                                "phone": phone_number,
                                "pattern": emoji_pattern,
                                "rows": len(emoji_rows),
                                "score": score if 'score' in locals() else "?"
                            }
                        else:
                            print(f"  Could not extract emoji pattern")
                            
        except Exception as e:
            print(f"Error processing {html_file}: {e}")
    
    return results

def main():
    print("Extracting correct emoji patterns for Wordle #1500...\n")
    results = extract_patterns_from_html()
    
    if not results:
        print("\nNo patterns found. Something went wrong with the extraction.")
        return
    
    print("\n===== EXTRACTED PATTERNS FOR WORDLE #1500 =====")
    for player, data in results.items():
        print(f"\n{player} ({data['phone']}) - Score: {data['score']}/6 ({data['rows']} rows)")
        print(data['pattern'])
        print("-" * 20)
    
    # Print a summary in a format that can be used in code
    print("\n\nPATTERN SUMMARY FOR CODE USE:")
    print("patterns = {")
    for player, data in results.items():
        # Format the pattern for code (with proper escaping)
        pattern_code = repr(data['pattern'])
        print(f"    '{player}': {pattern_code},")
    print("}")

if __name__ == "__main__":
    main()
