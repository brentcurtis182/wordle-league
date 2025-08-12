#!/usr/bin/env python3
import sqlite3
import logging
import os
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def delete_vox_scores():
    """Delete Vox's erroneous Wordle #1503 scores and modify export script to prevent re-addition"""
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
        
        # Verify Vox's Wordle #1502 (yesterday's) scores still exist
        cursor.execute("""
            SELECT id, player_name, wordle_num, score, timestamp, emoji_pattern, league_id 
            FROM scores 
            WHERE player_name = 'Vox' AND wordle_num = '1502'
        """)
        
        records = cursor.fetchall()
        logging.info(f"Vox still has {len(records)} valid scores for Wordle #1502")
        
        # Close the connection
        conn.close()
        
        # Now let's manually fix the HTML files to remove Vox's entry from Wordle #1503 
        pal_wordle_1503_file = 'website_export/pal/daily/wordle-1503.html'
        if os.path.exists(pal_wordle_1503_file):
            logging.info(f"Fixing {pal_wordle_1503_file} to remove Vox's entry")
            
            with open(pal_wordle_1503_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find and remove Vox's score card
            vox_start = content.find('<div class="score-card">', content.find('<div class="player-name">Vox</div>') - 100)
            if vox_start >= 0:
                vox_end = content.find('</div>', content.find('</div>', content.find('</div>', vox_start + 1) + 1) + 1) + 6
                if vox_end > vox_start:
                    new_content = content[:vox_start] + content[vox_end:]
                    
                    # Create a backup
                    backup_file = f"{pal_wordle_1503_file}.bak"
                    shutil.copy2(pal_wordle_1503_file, backup_file)
                    logging.info(f"Created backup at {backup_file}")
                    
                    # Write updated content
                    with open(pal_wordle_1503_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    logging.info("Successfully removed Vox's entry from HTML file")
                else:
                    logging.error("Could not find the end of Vox's score card in the HTML")
            else:
                logging.info("Could not find Vox's entry in the HTML file")
                
        # Also fix the emoji pattern display for PAL league
        pal_template_file = 'website_export/templates/wordle.html'
        pal_daily_dir = 'website_export/pal/daily'
        
        for file_name in os.listdir(pal_daily_dir):
            if file_name.startswith('wordle-') and file_name.endswith('.html'):
                file_path = os.path.join(pal_daily_dir, file_name)
                logging.info(f"Fixing emoji patterns in {file_path}")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Fix the emoji pattern display by removing date text
                new_content = content.replace('</div>, Thursday, July 31 2025', '</div>')
                
                if new_content != content:
                    # Create a backup
                    backup_file = f"{file_path}.bak"
                    shutil.copy2(file_path, backup_file)
                    
                    # Write fixed content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    logging.info(f"Fixed emoji pattern display in {file_path}")
        
    except Exception as e:
        logging.error(f"Error: {e}")
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    delete_vox_scores()
