import os
import re
import sqlite3
import logging
from datetime import datetime
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def debug_dom_extraction():
    """Analyze the most recent DOM snapshots to find and debug Wordle scores extraction"""
    
    # Find the latest DOM snapshots for both leagues
    dom_dir = "dom_captures"
    warriorz_files = [f for f in os.listdir(dom_dir) if f.startswith("dom_Wordle_Warriorz_") and f.endswith(".html")]
    pal_files = [f for f in os.listdir(dom_dir) if f.startswith("dom_PAL_") and f.endswith(".html")]
    
    latest_files = []
    if warriorz_files:
        latest_warriorz = sorted(warriorz_files)[-1]
        latest_files.append((latest_warriorz, 1, "Wordle Warriorz"))
        
    if pal_files:
        latest_pal = sorted(pal_files)[-1]
        latest_files.append((latest_pal, 3, "PAL"))
    
    # Calculate today's and yesterday's Wordle numbers
    start_date = datetime(2021, 6, 19)
    today = datetime.now()
    days_since_start = (today - start_date).days
    today_wordle = days_since_start + 1
    yesterday_wordle = today_wordle - 1
    
    logging.info(f"Today's Wordle: #{today_wordle}, Yesterday's Wordle: #{yesterday_wordle}")
    
    # Connect to database
    db_path = 'wordle_league.db'
    if not os.path.exists(db_path):
        logging.error(f"Database file not found: {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Process each league's DOM snapshot
    for filename, league_id, league_name in latest_files:
        filepath = os.path.join(dom_dir, filename)
        logging.info(f"\n{'='*80}\nAnalyzing {league_name} DOM: {filename}")
        
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
        # Parse with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Define regular expressions
        wordle_regex = re.compile(r'Wordle ([\d,]+)(?:\s+#([\d,]+))?\s+([1-6X])/6')
        phone_regex_message = re.compile(r'Message from (\d[\s\d-]+\d)')
        phone_regex_format = re.compile(r'\((\d{3})\)[\s-]*(\d{3})[\s-]*(\d{4})')
        
        # Find elements that might contain scores
        annotations = soup.select("gv-annotation.preview")
        aria_elements = soup.select('[aria-label*="Wordle"]')
        hidden_elements = soup.select(".cdk-visually-hidden")
        
        logging.info(f"Found {len(annotations)} annotation elements")
        logging.info(f"Found {len(aria_elements)} aria-label elements")
        logging.info(f"Found {len(hidden_elements)} hidden elements")
        
        # Combine all elements
        all_elements = annotations + aria_elements + hidden_elements
        logging.info(f"Processing {len(all_elements)} total elements")
        
        scores_found = 0
        matched_scores = 0
        
        # Check for scores in each element
        for element in all_elements:
            element_text = element.get_text(strip=True)
            if not "Wordle" in element_text or not "/6" in element_text:
                continue
                
            # Skip reactions
            if element_text.startswith("Loved ") or element_text.startswith("Liked "):
                continue
                
            # Extract message content
            message_start = element_text.find("Message from")
            if message_start >= 0:
                message_content = element_text[message_start:]
            else:
                message_content = element_text
                
            # Find Wordle score
            match = wordle_regex.search(message_content)
            if not match:
                continue
                
            matched_scores += 1
            
            # Extract wordle number
            wordle_num_str = match.group(1)
            wordle_num = int(wordle_num_str.replace(',', ''))
            
            # Extract score
            score_str = match.group(3)
            score = 7 if score_str == 'X' else int(score_str)
            
            # Check if this is today's or yesterday's Wordle
            if wordle_num not in (today_wordle, yesterday_wordle):
                logging.info(f"IGNORED: Wordle #{wordle_num} is neither today's ({today_wordle}) nor yesterday's ({yesterday_wordle})")
                continue
                
            scores_found += 1
            
            # Find phone number
            phone = None
            phone_match = phone_regex_message.search(message_content)
            if phone_match:
                # Extract phone from 'Message from' format
                phone = phone_match.group(1)
                phone = re.sub(r'[\s\-\(\)]+', '', phone)
                # Handle +1 prefix
                if phone.startswith('+1'):
                    phone = phone[1:]  # Keep the 1 but remove the +
            else:
                # Try to extract from (XXX) XXX-XXXX format
                phone_matches = phone_regex_format.findall(message_content)
                if phone_matches:
                    area_code = phone_matches[0][0]
                    prefix = phone_matches[0][1]
                    suffix = phone_matches[0][2]
                    phone = f"1{area_code}{prefix}{suffix}"  # Always add leading 1
                    
            # Normalize phone number
            if phone:
                # Make sure we have exactly 11 digits with leading 1
                if len(phone) == 10 and not phone.startswith('1'):
                    phone = '1' + phone
                elif len(phone) > 11 and phone.startswith('1'):
                    phone = phone[:11]  # Truncate to 11 digits if too long
            
            # Check player mapping
            player_name = "Unknown"
            if phone:
                # Get player by phone number for this league
                cursor.execute("""
                    SELECT name FROM players 
                    WHERE (phone_number = ? OR phone_number = ? OR phone_number = ?) 
                    AND league_id = ?
                """, (phone, phone[1:] if phone.startswith('1') and len(phone) == 11 else phone, 
                       '1' + phone if not phone.startswith('1') and len(phone) == 10 else phone, 
                       league_id))
                       
                player_result = cursor.fetchone()
                if player_result:
                    player_name = player_result[0]
                    
            # Check if score already exists in database
            cursor.execute("""
                SELECT id FROM scores 
                WHERE player_name = ? AND wordle_num = ? AND league_id = ?
            """, (player_name, wordle_num, league_id))
            
            existing_score = cursor.fetchone()
            is_new_score = existing_score is None
            
            # Report on this score
            logging.info(f"\n{'NEW SCORE' if is_new_score else 'EXISTING SCORE'}: {player_name} - Wordle #{wordle_num} - {score}/6")
            logging.info(f"  Phone: {phone}")
            logging.info(f"  Raw Message: {message_content[:100]}...")
            
        logging.info(f"\nSummary for {league_name}:")
        logging.info(f"  {matched_scores} regex matches found")
        logging.info(f"  {scores_found} valid scores (today/yesterday)")
        
    conn.close()

if __name__ == "__main__":
    debug_dom_extraction()
