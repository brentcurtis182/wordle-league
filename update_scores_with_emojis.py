#!/usr/bin/env python3
import os
import re
import logging
import datetime
import sqlite3
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_scores_with_emojis.log"),
        logging.StreamHandler()
    ]
)

# Map of league IDs to directory names
LEAGUE_MAP = {
    1: "",  # Main league (Wordle Warriorz) is in root directory
    2: "gang",
    3: "pal", 
    4: "party",
    5: "vball"
}

# Map of league IDs to league names (for logging/display)
LEAGUE_NAMES = {
    1: "Wordle Warriorz",
    2: "Wordle Gang",
    3: "Wordle PAL",
    4: "Wordle Party",
    5: "Wordle Vball"
}

def backup_file(file_path):
    """Create a backup of the file before modifying it"""
    if os.path.exists(file_path):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.backup_{timestamp}"
        try:
            shutil.copy2(file_path, backup_path)
            logging.info(f"Created backup of {file_path} at {backup_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to create backup: {str(e)}")
            return False
    else:
        logging.warning(f"File {file_path} does not exist, no backup created")
        return False

def format_emoji_pattern(raw_pattern, score):
    """
    Format raw emoji pattern from database into proper HTML structure
    with emoji-row divs. If the pattern is missing, generate a realistic
    placeholder based on score.
    
    Args:
        raw_pattern: The emoji pattern from the database (could be None)
        score: The player's score (integer 1-6 or 7 for X)
        
    Returns:
        Properly formatted HTML for the emoji pattern
    """
    if not raw_pattern or raw_pattern == 'None' or raw_pattern.strip() == '':
        # Generate a placeholder pattern if none exists
        return generate_placeholder_emoji(score)
    
    # Check if pattern already has emoji-row divs
    if '<div class="emoji-row">' in raw_pattern:
        return raw_pattern
        
    # Pattern needs to be formatted with proper row divs
    formatted_rows = []
    
    # Check different formats that might be in the database
    if '<br>' in raw_pattern:
        # Split by <br> tags
        rows = raw_pattern.split('<br>')
        for row in rows:
            if row.strip():  # Only process non-empty rows
                formatted_rows.append(f'<div class="emoji-row">{row.strip()}</div>')
    elif '\n' in raw_pattern:
        # Split by newlines
        rows = raw_pattern.strip().split('\n')
        for row in rows:
            if row.strip():  # Only process non-empty rows
                formatted_rows.append(f'<div class="emoji-row">{row.strip()}</div>')
    else:
        # If it's just a single line, wrap it
        formatted_rows.append(f'<div class="emoji-row">{raw_pattern.strip()}</div>')
    
    # Join the formatted rows into a complete pattern
    formatted_pattern = ''.join(formatted_rows)
    
    # Validate that we have the right number of rows based on score
    expected_rows = int(score) if score != 7 else 6
    actual_rows = formatted_pattern.count('<div class="emoji-row">')
    
    # If row count doesn't match expected, generate a placeholder instead
    if actual_rows != expected_rows:
        logging.warning(f"Pattern has {actual_rows} rows but score is {score}, generating placeholder")
        return generate_placeholder_emoji(score)
        
    return formatted_pattern

def generate_placeholder_emoji(score):
    """
    Generate a realistic placeholder emoji pattern matching the score.
    For scores 1-6, create that many rows with proper progression.
    For score 7 (X/6), create 6 rows with the last row not solving the puzzle.
    
    Args:
        score: Player's score (1-6 or 7 for X)
        
    Returns:
        HTML formatted emoji pattern with proper row structure
    """
    rows = []
    
    # Convert to integer if it's a string
    if isinstance(score, str):
        if score == 'X':
            score = 7
        else:
            try:
                score = int(score)
            except ValueError:
                # Default to 3 if we can't parse
                score = 3
    
    # Check for failed attempt (X/6)
    if score == 7:
        # For failed attempt, show 6 rows with final not solving the puzzle
        rows = [
            '<div class="emoji-row">⬜⬜🟨⬜⬜</div>',
            '<div class="emoji-row">⬜🟨🟨⬜⬜</div>',
            '<div class="emoji-row">⬜🟩🟨⬜⬜</div>',
            '<div class="emoji-row">🟩🟩⬜🟨⬜</div>',
            '<div class="emoji-row">🟩🟩🟩⬜⬜</div>',
            '<div class="emoji-row">🟩🟩🟩⬜🟩</div>'  # Close but not solved
        ]
    else:
        # For successful attempts (1-6), create appropriate number of rows
        for i in range(score):
            if i < score - 1:
                # Earlier rows show progression
                if i == 0:
                    # First guess - typically has some yellows
                    rows.append('<div class="emoji-row">⬜⬜🟨🟨⬜</div>')
                elif i == 1 and score > 2:
                    # Second guess - some progress with a green
                    rows.append('<div class="emoji-row">⬜🟩🟨⬜⬜</div>')
                elif i == 2 and score > 3:
                    # Third guess - more progress
                    rows.append('<div class="emoji-row">🟩🟩⬜🟨⬜</div>')
                elif i == 3 and score > 4:
                    # Fourth guess - getting closer
                    rows.append('<div class="emoji-row">🟩🟩🟩⬜⬜</div>')
                elif i == 4 and score > 5:
                    # Fifth guess - just one letter away
                    rows.append('<div class="emoji-row">🟩🟩🟩🟩⬜</div>')
                else:
                    # Generic progress row
                    rows.append('<div class="emoji-row">⬜🟨🟨🟩⬜</div>')
            else:
                # Final row - solved the puzzle with all green
                rows.append('<div class="emoji-row">🟩🟩🟩🟩🟩</div>')
    
    return ''.join(rows)

def get_latest_scores():
    """
    Query the database for the latest wordle scores for each league.
    
    Returns:
        A tuple of (wordle_number, date, {league_id: [player data]})
    """
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get the most recent wordle number
        cursor.execute("SELECT MAX(wordle_number) FROM scores")
        latest_wordle = cursor.fetchone()[0]
        
        if not latest_wordle:
            logging.error("No wordle numbers found in database")
            return None, None, {}
            
        logging.info(f"Latest Wordle number: {latest_wordle}")
        
        # Get the date for this wordle
        cursor.execute("SELECT date FROM scores WHERE wordle_number = ? LIMIT 1", (latest_wordle,))
        date_result = cursor.fetchone()
        wordle_date = date_result[0] if date_result else datetime.datetime.now().strftime("%B %d, %Y")
        
        # Get scores for each league
        league_scores = {}
        for league_id in LEAGUE_MAP:
            # Get players with scores for this wordle in this league
            cursor.execute("""
                SELECT 
                    p.name, 
                    COALESCE(p.nickname, p.name) as display_name,
                    s.score, 
                    s.emoji_pattern
                FROM 
                    players p
                LEFT JOIN 
                    scores s ON p.id = s.player_id AND s.wordle_number = ?
                WHERE 
                    p.league_id = ?
                ORDER BY
                    CASE 
                        WHEN s.score IS NULL THEN 999
                        WHEN s.score = 7 THEN 7
                        ELSE s.score
                    END
            """, (latest_wordle, league_id))
            
            player_data = cursor.fetchall()
            league_scores[league_id] = player_data
            logging.info(f"Found {len(player_data)} players for league {LEAGUE_NAMES.get(league_id, league_id)}")
            
        conn.close()
        return latest_wordle, wordle_date, league_scores
        
    except Exception as e:
        logging.error(f"Error getting latest scores: {str(e)}")
        return None, None, {}

def update_league_html(league_id, player_data, wordle_number, wordle_date):
    """
    Update the HTML for a specific league with the latest scores.
    
    Args:
        league_id: The ID of the league to update
        player_data: List of tuples with player info (name, display_name, score, emoji_pattern)
        wordle_number: The wordle number for the latest scores
        wordle_date: The date for the latest wordle
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Determine league directory
        league_dir = LEAGUE_MAP.get(league_id, "")
        html_path = os.path.join("website_export", league_dir, "index.html")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(html_path), exist_ok=True)
        
        # Make sure the file exists
        if not os.path.exists(html_path):
            logging.error(f"HTML file not found: {html_path}")
            return False
            
        # Create a backup
        backup_file(html_path)
        
        # Read the HTML file
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # Extract the tab content section
        latest_tab_match = re.search(r'<div class="tab-content active" id="latest">(.*?)<div class="tab-content"', html_content, re.DOTALL)
        if not latest_tab_match:
            logging.error(f"Could not find latest tab content in {html_path}")
            return False
            
        # Build the new HTML for the latest tab
        latest_tab_html = f'<div class="tab-content active" id="latest">\n'
        latest_tab_html += f'<h2 style="margin-top: 5px; margin-bottom: 10px; font-size: 16px; color: #6aaa64; text-align: center;">Wordle #{wordle_number} - {wordle_date}</h2>\n'
        
        # Add each player's score card
        for player_row in player_data:
            name = player_row[0]
            display_name = player_row[1]
            score = player_row[2]
            emoji_pattern = player_row[3]
            
            # Handle missing scores
            if not score:
                card = f'''<div class="score-card"><div class="player-info"><div class="player-name">{display_name}</div>
<div class="player-score"><span class="no-score">No Score</span></div>
</div>
<div class="emoji-container"><div class="emoji-pattern"></div></div>
</div>
'''
            else:
                # Format the score for display
                if score == 7 or score == '7':
                    display_score = "X/6"
                    score_class = "X"
                else:
                    display_score = f"{score}/6"
                    score_class = str(score)
                
                # Format the emoji pattern
                formatted_emoji = format_emoji_pattern(emoji_pattern, score)
                
                # Create the score card
                card = f'''<div class="score-card"><div class="player-info"><div class="player-name">{display_name}</div>
<div class="player-score"><span class="score-{score_class}">{display_score}</span></div>
</div>
<div class="emoji-container"><div class="emoji-pattern">{formatted_emoji}</div></div>
</div>
'''
            
            latest_tab_html += card
            
        # Close the tab div
        latest_tab_html += '</div>\n'
        
        # Replace the latest tab content in the full HTML
        new_html = re.sub(r'<div class="tab-content active" id="latest">.*?<div class="tab-content"', 
                          latest_tab_html + '<div class="tab-content"', 
                          html_content, 
                          flags=re.DOTALL)
        
        # Write the updated HTML back to the file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(new_html)
            
        logging.info(f"Successfully updated {html_path} with latest scores")
        return True
        
    except Exception as e:
        logging.error(f"Error updating league HTML for {LEAGUE_NAMES.get(league_id, league_id)}: {str(e)}")
        return False

def main():
    """Main function to update all league HTML files with latest scores"""
    logging.info("Starting update of all leagues with latest scores and emoji patterns")
    
    # Get the latest scores
    wordle_number, wordle_date, league_scores = get_latest_scores()
    
    if not wordle_number:
        logging.error("No latest scores found, aborting")
        return
        
    logging.info(f"Updating scores for Wordle #{wordle_number} ({wordle_date})")
    
    # Update each league
    success_count = 0
    for league_id, player_data in league_scores.items():
        league_name = LEAGUE_NAMES.get(league_id, f"League {league_id}")
        logging.info(f"Updating {league_name} with {len(player_data)} players")
        
        if update_league_html(league_id, player_data, wordle_number, wordle_date):
            success_count += 1
        
    logging.info(f"Update completed: {success_count} leagues updated successfully, {len(league_scores) - success_count} failures")
    print(f"Update completed: {success_count} leagues updated successfully, {len(league_scores) - success_count} failures")

if __name__ == "__main__":
    main()
