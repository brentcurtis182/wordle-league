import os
import re
import sys
import io
import sqlite3
import logging
from bs4 import BeautifulSoup

# Configure UTF-8 for output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_phone_to_name_mapping():
    """Get phone mapping from database"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, phone_number FROM player")
        players = {}
        
        for row in cursor.fetchall():
            name = row['name']
            phone = row['phone_number']
            
            # Store multiple formats for matching
            players[phone] = name  # Raw format from DB
            
            # Format as (XXX) XXX-XXXX
            if phone.startswith('1') and len(phone) == 11:
                formatted = f"({phone[1:4]}) {phone[4:7]}-{phone[7:11]}"
                players[formatted] = name
            elif len(phone) == 10:
                formatted = f"({phone[0:3]}) {phone[3:6]}-{phone[6:10]}"
                players[formatted] = name
            
            # Store without formatting
            digits_only = re.sub(r'\D', '', phone)
            players[digits_only] = name
            
            # Remove leading 1 if present
            if digits_only.startswith('1'):
                players[digits_only[1:]] = name
        
        conn.close()
        return players
    except Exception as e:
        logging.error(f"Error getting player mappings: {e}")
        return {
            "(310) 926-3555": "Joanna",
            "(949) 230-4472": "Nanna",
            "(858) 735-9353": "Brent",
            "(760) 334-1190": "Malia",
            "(760) 846-2302": "Evan"
        }

def extract_from_html_files():
    """Extract Wordle 1500 patterns from local HTML files"""
    # Get player name mapping
    phone_to_name = get_phone_to_name_mapping()
    print(f"Loaded {len(phone_to_name)} phone-to-name mappings")
    
    # Find all HTML files
    html_files = [f for f in os.listdir() if f.endswith('.html')]
    if not html_files:
        print("No HTML files found in current directory!")
        return {}
    
    print(f"Found {len(html_files)} HTML files to process")
    
    # Store results by player
    results = {}
    
    for html_file in html_files:
        try:
            print(f"\nProcessing {html_file}...")
            with open(html_file, 'r', encoding='utf-8') as file:
                content = file.read()
                
                # Check if this file contains Wordle 1500 data
                if "Wordle 1500" in content:
                    print(f"  Found 'Wordle 1500' mention in {html_file}")
                
                # Use BeautifulSoup to parse the HTML
                soup = BeautifulSoup(content, 'html.parser')
                
                # Find all hidden elements - the key to reliable extraction
                hidden_elements = soup.select('.cdk-visually-hidden')
                print(f"  Found {len(hidden_elements)} hidden elements")
                
                for element in hidden_elements:
                    try:
                        text = element.text.strip()
                        
                        # Skip if no relevant content
                        if "Wordle" not in text or "/6" not in text:
                            continue
                        
                        # Check if this is Wordle 1500
                        wordle_match = re.search(r'Wordle\s+#?([\d,]+)', text)
                        if not wordle_match:
                            continue
                            
                        wordle_num = wordle_match.group(1).replace(',', '')
                        if wordle_num != "1500":
                            continue
                        
                        print(f"\n  Found Wordle 1500 data!")
                        
                        # Extract phone number (multiple formats)
                        phone_match = re.search(r'from\s+(\d[\s\d]+\d)', text)
                        phone_number = None
                        
                        if phone_match:
                            # Clean up spaces
                            digits = phone_match.group(1).replace(" ", "")
                            
                            # Format to (XXX) XXX-XXXX
                            if len(digits) >= 10:
                                if digits.startswith('1') and len(digits) >= 11:
                                    # Strip leading 1 if present
                                    digits = digits[1:] if len(digits) > 10 else digits
                                
                                phone_number = f"({digits[:3]}) {digits[3:6]}-{digits[6:10]}"
                            else:
                                phone_number = digits
                        else:
                            # Try alternate formats
                            alt_match = re.search(r'from\s+\(?(\d{3})\)?[\s-]*(\d{3})[\s-]*(\d{4})', text)
                            if alt_match:
                                phone_number = f"({alt_match.group(1)}) {alt_match.group(2)}-{alt_match.group(3)}"
                        
                        # Try more generic pattern if still not found
                        if not phone_number:
                            digits = re.findall(r'\d', text[:100])  # Look in first 100 chars
                            if len(digits) >= 10:
                                digits_str = ''.join(digits)
                                if len(digits_str) >= 10:
                                    phone_number = f"({digits_str[:3]}) {digits_str[3:6]}-{digits_str[6:10]}"
                        
                        if not phone_number:
                            print(f"  Could not extract phone number")
                            continue
                        
                        # Find player name
                        player_name = None
                        for phone_format, name in phone_to_name.items():
                            if phone_number in phone_format or phone_format in phone_number:
                                player_name = name
                                break
                        
                        if not player_name:
                            # Try with just the digits
                            digits_only = re.sub(r'\D', '', phone_number)
                            player_name = phone_to_name.get(digits_only)
                        
                        if not player_name:
                            print(f"  Could not identify player for phone {phone_number}")
                            player_name = f"Unknown ({phone_number})"
                        
                        # Extract score
                        score_match = re.search(r'([\dX])/6', text)
                        if not score_match:
                            print(f"  Could not extract score")
                            continue
                            
                        score_value = score_match.group(1)
                        
                        # Extract emoji pattern - the key part we want
                        emoji_rows = re.findall(r'[⬛⬜🟨🟩]{5}', text)
                        
                        if emoji_rows:
                            emoji_pattern = "\n".join(emoji_rows)
                            print(f"  Player: {player_name}")
                            print(f"  Score: {score_value}/6")
                            print(f"  Pattern ({len(emoji_rows)} rows):")
                            print(f"{emoji_pattern}")
                            
                            # Store results
                            results[player_name] = {
                                'phone': phone_number,
                                'score': score_value,
                                'pattern': emoji_pattern,
                                'rows': len(emoji_rows),
                                'source_file': html_file
                            }
                        else:
                            print(f"  Could not extract emoji pattern")
                            
                            # If we found other data but no pattern, still log it
                            print(f"  Text excerpt: {text[:200].replace(chr(10), ' ')}")
                    
                    except Exception as e:
                        print(f"  Error processing element: {e}")
        
        except Exception as e:
            print(f"Error processing {html_file}: {e}")
    
    return results

def main():
    print("Extracting Wordle #1500 patterns from local HTML files...\n")
    results = extract_from_html_files()
    
    if not results:
        print("\nNo patterns found. Make sure HTML files contain .cdk-visually-hidden elements with Wordle 1500 data.")
        return
    
    print("\n===== EXTRACTED PATTERNS FOR WORDLE #1500 =====")
    for player, data in results.items():
        print(f"\n{player} - Score: {data['score']}/6 ({data['rows']} rows) [Source: {data['source_file']}]")
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
