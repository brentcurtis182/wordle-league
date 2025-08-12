#!/usr/bin/env python3
import sqlite3
import logging
import os
import re
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def fix_database_issues():
    """Delete Vox's erroneous Wordle #1503 score from the database"""
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Check if Vox's scores exist for Wordle #1503
        cursor.execute("""
            SELECT id, player_name, wordle_num, score, timestamp, emoji_pattern, league_id 
            FROM scores 
            WHERE player_name = 'Vox' AND wordle_num = '1503'
        """)
        
        records = cursor.fetchall()
        
        if records:
            logging.info(f"Found {len(records)} erroneous scores for Vox (Wordle #1503)")
            
            # Delete each record
            for record in records:
                record_id = record[0]
                cursor.execute("DELETE FROM scores WHERE id = ?", (record_id,))
                logging.info(f"Deleted score ID {record_id} for Vox, Wordle #1503")
            
            # Commit the changes
            conn.commit()
            logging.info("Deletion committed to database")
        else:
            logging.info("No Wordle #1503 scores found for Vox - already deleted")
        
        # Double check Vox's all-time stats - are there duplicate entries?
        cursor.execute("""
            SELECT COUNT(*) FROM scores WHERE player_name = 'Vox' AND league_id = 3
        """)
        count = cursor.fetchone()[0]
        logging.info(f"Vox has {count} total scores in league 3 (PAL)")
        
        # Show all Vox's scores for verification
        cursor.execute("""
            SELECT id, player_name, wordle_num, score, date(timestamp) as date, emoji_pattern, league_id 
            FROM scores 
            WHERE player_name = 'Vox' AND league_id = 3
            ORDER BY wordle_num
        """)
        
        vox_scores = cursor.fetchall()
        for score in vox_scores:
            logging.info(f"Vox score: ID={score[0]}, Wordle #{score[2]}, Score={score[3]}, Date={score[4]}")
        
        # Close the connection
        conn.close()
        
    except Exception as e:
        logging.error(f"Error fixing database: {e}")
        if 'conn' in locals() and conn:
            conn.close()

def fix_emoji_patterns_directly():
    """Fix emoji patterns in PAL HTML files by directly editing the files"""
    try:
        pal_dir = 'website_export/pal/daily'
        if not os.path.exists(pal_dir):
            logging.error(f"PAL directory not found: {pal_dir}")
            return
            
        # Process all Wordle HTML files
        for file_name in os.listdir(pal_dir):
            if file_name.startswith('wordle-') and file_name.endswith('.html'):
                file_path = os.path.join(pal_dir, file_name)
                logging.info(f"Processing file: {file_path}")
                
                # Create backup if not exists
                backup_file = f"{file_path}.clean.bak"
                if not os.path.exists(backup_file):
                    shutil.copy2(file_path, backup_file)
                    logging.info(f"Created backup: {backup_file}")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find all emoji-row divs that contain date/time text and clean them
                # This simpler approach looks for emoji squares followed by quotes, commas, or periods
                new_content = content
                for emoji_row_match in re.finditer(r'<div class="emoji-row">(.*?)</div>', content):
                    full_div = emoji_row_match.group(0)
                    emoji_content = emoji_row_match.group(1)
                    
                    # If there's a date/time text after the emoji squares
                    if any(c in emoji_content for c in ['"', ',', '.']) and '🟩' in emoji_content:
                        # Clean the content - get just the emoji squares
                        clean_emoji = re.search(r'[⬜⬛🟨🟩🟥🟦🟪🟧🟫⬜]{5}', emoji_content)
                        if clean_emoji:
                            clean_div = f'<div class="emoji-row">{clean_emoji.group(0)}</div>'
                            new_content = new_content.replace(full_div, clean_div)
                            logging.info(f"Fixed emoji row: '{emoji_content}' -> '{clean_emoji.group(0)}'")
                
                # Write the cleaned content back if changes were made
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    logging.info(f"Fixed emoji patterns in {file_path}")
                else:
                    logging.info(f"No emoji patterns to fix in {file_path}")
                    
                # Check if Vox's score card is in this file
                if "Vox</div>" in new_content and "1503" in file_path:
                    logging.info(f"Found Vox in {file_path} - removing score card")
                    
                    # Simple approach to remove Vox's score card
                    vox_card_pattern = r'<div class="score-card">.*?<div class="player-name">Vox</div>.*?</div>\s*</div>\s*</div>'
                    updated_content = re.sub(vox_card_pattern, '', new_content, flags=re.DOTALL)
                    
                    if updated_content != new_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(updated_content)
                        logging.info(f"Successfully removed Vox's score card from {file_path}")
                    else:
                        logging.info(f"Could not find and remove Vox's score card with regex")
    
    except Exception as e:
        logging.error(f"Error fixing emoji patterns: {e}")

if __name__ == "__main__":
    logging.info("Starting final comprehensive fix")
    fix_database_issues()
    fix_emoji_patterns_directly()
    logging.info("Running export again to ensure fixes are applied")
    os.system("python integrated_auto_update_multi_league.py --export-only")
    logging.info("Final fix completed")
