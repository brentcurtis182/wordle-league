import os
import re
import sqlite3
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def save_wordle_1505_scores():
    """Simple script to extract and save Wordle #1505 scores from existing DOM captures"""
    
    # Force today's Wordle to be #1505
    today_wordle = 1505
    
    # Find DOM captures
    dom_dir = "dom_captures"
    if not os.path.exists(dom_dir):
        logging.error(f"DOM captures directory not found: {dom_dir}")
        return
        
    # Connect to database
    db_path = 'wordle_league.db'
    if not os.path.exists(db_path):
        logging.error(f"Database file not found: {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Process leagues
    leagues = [
        {"id": 1, "name": "Wordle Warriorz"},
        {"id": 3, "name": "PAL"}
    ]
    
    scores_saved = 0
    
    for league in leagues:
        league_id = league["id"]
        league_name = league["name"]
        
        # Find latest DOM file for this league
        if league_name == "Wordle Warriorz":
            files = [f for f in os.listdir(dom_dir) if f.startswith("dom_Wordle_Warriorz_") and f.endswith(".html")]
        else:
            files = [f for f in os.listdir(dom_dir) if f.startswith("dom_PAL_") and f.endswith(".html")]
        
        if not files:
            logging.warning(f"No DOM captures found for {league_name}")
            continue
            
        # Use the latest DOM file
        latest_file = sorted(files)[-1]
        file_path = os.path.join(dom_dir, latest_file)
        
        logging.info(f"Processing {league_name} DOM from {latest_file}")
        
        # Read and parse DOM
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
        soup = BeautifulSoup(content, 'html.parser')
        
        # Regular expressions for extracting information
        wordle_regex = re.compile(r'Wordle ([\d,]+)(?:\s+#([\d,]+))?\s+([1-6X])/6')
        phone_regex = re.compile(r'Message from (\d[\s\d-]+\d)')
        phone_format_regex = re.compile(r'\((\d{3})\)[\s-]*(\d{3})[\s-]*(\d{4})')
        
        # Find all elements that could contain scores
        elements = soup.select(".cdk-visually-hidden, [aria-label*='Wordle'], gv-annotation")
        
        # Track processed scores to avoid duplicates
        processed_scores = set()
        
        for element in elements:
            text = element.get_text(strip=True)
            
            # Skip non-Wordle messages or reactions
            if "Wordle" not in text or "/6" not in text or text.startswith("Loved ") or text.startswith("Liked "):
                continue
                
            # Extract Wordle info
            match = wordle_regex.search(text)
            if not match:
                continue
                
            wordle_num_str = match.group(1)
            wordle_num = int(wordle_num_str.replace(',', ''))
            
            # Focus only on Wordle #1505
            if wordle_num != today_wordle:
                continue
                
            score_str = match.group(3)
            score = 7 if score_str == 'X' else int(score_str)
            
            # Extract emoji pattern
            emoji_pattern = ""
            if '\n' in text:
                lines = text.split('\n')
                emoji_lines = []
                in_pattern = False
                
                for line in lines:
                    if '🟩' in line or '⬛' in line or '⬜' in line or '🟨' in line:
                        emoji_lines.append(line)
                        in_pattern = True
                    elif in_pattern:
                        break
                        
                if emoji_lines:
                    emoji_pattern = '\n'.join(emoji_lines)
            
            # Find phone number
            phone = None
            phone_match = phone_regex.search(text)
            if phone_match:
                # Extract from 'Message from' format
                phone = phone_match.group(1)
                phone = re.sub(r'[\s\-\(\)]+', '', phone)
                if phone.startswith('+1'):
                    phone = phone[1:]  # Keep the 1 but remove the +
            else:
                # Try to extract from (XXX) XXX-XXXX format
                phone_matches = phone_format_regex.findall(text)
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
                    phone = phone[:11]
            else:
                logging.warning("Could not extract phone number from message")
                continue
                
            # Find player by phone number
            cursor.execute("""
                SELECT name FROM players 
                WHERE (phone_number = ? OR phone_number = ? OR phone_number = ?) 
                AND league_id = ?
            """, (phone, phone[1:] if phone.startswith('1') and len(phone) == 11 else phone, 
                   '1' + phone if not phone.startswith('1') and len(phone) == 10 else phone, 
                   league_id))
                   
            player_result = cursor.fetchone()
            if not player_result:
                logging.warning(f"No player found for phone {phone} in league {league_id}")
                continue
                
            player_name = player_result[0]
            
            # Create a unique key to avoid duplicate processing
            score_key = f"{player_name}:{wordle_num}:{league_id}"
            if score_key in processed_scores:
                continue
                
            processed_scores.add(score_key)
            
            # Check if score already exists
            cursor.execute("""
                SELECT id FROM scores 
                WHERE player_name = ? AND wordle_num = ? AND league_id = ?
            """, (player_name, wordle_num, league_id))
            
            existing_score = cursor.fetchone()
            if existing_score:
                logging.info(f"Score already exists for {player_name}, Wordle #{wordle_num} in {league_name}")
                continue
                
            # Calculate score date based on Wordle number
            # Reference: Wordle #1503 is July 31, 2025
            reference_date = datetime(2025, 7, 31).date()
            reference_wordle = 1503
            days_diff = wordle_num - reference_wordle
            score_date = reference_date + timedelta(days=days_diff)
            
            # Get player_id for score table
            cursor.execute("SELECT id FROM players WHERE name = ? AND league_id = ?", 
                          (player_name, league_id))
            player_id_result = cursor.fetchone()
            player_id = player_id_result[0] if player_id_result else None
            
            if not player_id:
                logging.warning(f"Could not find player_id for {player_name} in league {league_id}")
                continue
                
            # Format date for database
            date_str = score_date.strftime('%Y-%m-%d')
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Save to scores table (plural)
            cursor.execute("""
                INSERT INTO scores 
                (player_name, score, wordle_num, emoji_pattern, league_id) 
                VALUES (?, ?, ?, ?, ?)
            """, (player_name, score, wordle_num, emoji_pattern, league_id))
            
            # Also save to 'score' table (singular) for compatibility
            cursor.execute("""
                INSERT INTO score 
                (player_id, score, wordle_number, date, created_at, emoji_pattern, league_id) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (player_id, score, wordle_num, date_str, now_str, emoji_pattern, league_id))
            
            conn.commit()
            scores_saved += 1
            logging.info(f"SAVED NEW SCORE: {player_name} - Wordle #{wordle_num} - {score}/6 - {league_name}")
    
    conn.close()
    
    if scores_saved > 0:
        logging.info(f"Successfully saved {scores_saved} new scores for Wordle #1505")
    else:
        logging.info("No new scores were saved")

if __name__ == "__main__":
    save_wordle_1505_scores()
