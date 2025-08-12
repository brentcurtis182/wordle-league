import re
import logging
import sqlite3
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("improved_extraction.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def enhanced_save_score_to_db(player, wordle_num, score, emoji_pattern=None, validate_score=True):
    """Enhanced version of save_score_to_db with better validation
    
    Args:
        player: Player name
        wordle_num: Wordle number (as integer)
        score: Score value (1-6, or 7 for X/6)
        emoji_pattern: Optional emoji pattern string
        validate_score: Whether to validate score against emoji pattern
        
    Returns:
        str: Status code - 'new_score_added', 'score_updated', 'emoji_updated', 'no_change', 'error', or 'validation_failed'
    """
    logging.info(f"Saving score: Player={player}, Wordle#{wordle_num}, Score={score}, Pattern length={len(emoji_pattern) if emoji_pattern else 0}")
    
    # Validate the player name
    if not player or player.lower().startswith("unknown"):
        logging.warning(f"Invalid player name: {player}")
        return "validation_failed"
    
    # Validate the wordle number (must be within reasonable range)
    if wordle_num < 1 or wordle_num > 10000:
        logging.warning(f"Invalid Wordle number: {wordle_num}")
        return "validation_failed"
    
    # Validate the score (must be 1-7)
    if score < 1 or score > 7:
        logging.warning(f"Invalid score: {score}")
        return "validation_failed"
    
    # If we have an emoji pattern, validate the score against it
    if validate_score and emoji_pattern:
        inferred_score = infer_score_from_emoji(emoji_pattern)
        
        if inferred_score is not None:
            if score != inferred_score:
                logging.warning(f"Score {score} doesn't match emoji pattern (suggests {inferred_score})")
                if inferred_score == 7 and score < 7:
                    logging.info("Emoji pattern indicates failure (X/6) but score is numeric - using numeric score")
                    # Continue with the given score
                elif score == 7 and inferred_score < 7:
                    logging.info("Score is X/6 but emoji pattern indicates success - using emoji-inferred score")
                    score = inferred_score
    
    conn = None
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Look up player ID from player table
        cursor.execute("SELECT id FROM player WHERE name = ?", (player,))
        player_row = cursor.fetchone()
        
        if not player_row:
            logging.warning(f"Player '{player}' not found in database")
            conn.close()
            return "validation_failed"
        
        player_id = player_row['id']
        
        # Check if this score already exists
        cursor.execute(
            "SELECT id, score, emoji_pattern FROM score WHERE wordle_number = ? AND player_id = ?",
            (wordle_num, player_id)
        )
        existing = cursor.fetchone()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        if existing:
            logging.info(f"Found existing score: {existing['score']} for Wordle #{wordle_num} by {player}")
            
            # For X/6 (score=7), we want to keep a numeric score if it exists
            if score == 7 and existing['score'] < 7:
                logging.info(f"Keeping existing score {existing['score']} instead of X/6")
                
                # Still update emoji pattern if provided
                if emoji_pattern:
                    # Verify if the new pattern has more rows
                    existing_rows = existing['emoji_pattern'].count('\n') + 1 if existing['emoji_pattern'] else 0
                    new_rows = emoji_pattern.count('\n') + 1
                    
                    if new_rows > existing_rows:
                        logging.info(f"Updating emoji pattern from {existing_rows} rows to {new_rows} rows")
                        cursor.execute(
                            "UPDATE score SET emoji_pattern = ? WHERE id = ?",
                            (emoji_pattern, existing['id'])
                        )
                        conn.commit()
                        conn.close()
                        return "emoji_updated"
                    else:
                        logging.info(f"Keeping existing emoji pattern with {existing_rows} rows")
                        conn.close()
                        return "no_change"
                else:
                    conn.close()
                    return "no_change"
            
            # Update the score if it's better than the existing one
            elif score < existing['score']:
                logging.info(f"Updating score from {existing['score']} to {score} (better score)")
                cursor.execute(
                    "UPDATE score SET score = ?, date = ? WHERE id = ?",
                    (score, today, existing['id'])
                )
                
                # Update emoji pattern if provided
                if emoji_pattern:
                    cursor.execute(
                        "UPDATE score SET emoji_pattern = ? WHERE id = ?",
                        (emoji_pattern, existing['id'])
                    )
                
                conn.commit()
                conn.close()
                return "score_updated"
            
            else:
                # If the existing score is better, just update the emoji pattern if provided
                if emoji_pattern:
                    # Verify if the new pattern has more rows
                    existing_rows = existing['emoji_pattern'].count('\n') + 1 if existing['emoji_pattern'] else 0
                    new_rows = emoji_pattern.count('\n') + 1
                    
                    if new_rows > existing_rows:
                        logging.info(f"Updating emoji pattern from {existing_rows} rows to {new_rows} rows")
                        cursor.execute(
                            "UPDATE score SET emoji_pattern = ? WHERE id = ?",
                            (emoji_pattern, existing['id'])
                        )
                        conn.commit()
                        conn.close()
                        return "emoji_updated"
                    else:
                        logging.info(f"Keeping existing emoji pattern with {existing_rows} rows")
                        conn.close()
                        return "no_change"
                else:
                    conn.close()
                    return "no_change"
        else:
            # Insert new score
            cursor.execute(
                "INSERT INTO score (wordle_number, score, player_id, emoji_pattern, date, created_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
                (wordle_num, score, player_id, emoji_pattern, today)
            )
            
            conn.commit()
            logging.info(f"New score added: {score} for Wordle #{wordle_num} by {player}")
            conn.close()
            return "new_score_added"
    except Exception as e:
        logging.error(f"Database error: {e}")
        if conn:
            conn.close()
        return "error"

def infer_score_from_emoji(emoji_pattern):
    """Infer score from emoji pattern
    
    Args:
        emoji_pattern: Emoji pattern string with newlines separating rows
        
    Returns:
        int: Inferred score (1-6, or 7 for X/6), or None if inference not possible
    """
    if not emoji_pattern:
        return None
    
    # Split pattern into rows
    rows = emoji_pattern.split('\n')
    num_rows = len(rows)
    
    # Validate each row has 5 emoji
    valid_rows = [row for row in rows if len(row.strip()) == 5]
    if len(valid_rows) != num_rows:
        logging.warning(f"Invalid emoji pattern: some rows don't have exactly 5 emoji")
        return None
    
    # Check if the last row is all green (solved)
    last_row = rows[-1]
    all_green = all(c == '🟩' for c in last_row)
    
    if all_green:
        # Score is the number of rows (1-6)
        return num_rows
    elif num_rows == 6:
        # If we have 6 rows and the last one isn't all green, it's a failure (X/6)
        return 7
    else:
        # If we have fewer than 6 rows and the last isn't all green,
        # we can't determine if it's complete, so return None
        return None

def extract_enhanced_wordle_scores(conversation_text):
    """Extract Wordle scores from conversation text with enhanced patterns
    
    Args:
        conversation_text: Text of the conversation
        
    Returns:
        tuple: (wordle_num, score, emoji_pattern) or (None, None, None) if no score found
    """
    # Enhanced regex patterns for both regular and failed attempts
    wordle_score_patterns = [
        # Standard formats
        re.compile(r'Wordle\s*#?\s*(\d+(?:,\d+)?)\s*[-:;]?\s*(\d)/6', re.IGNORECASE),
        # More flexible formats
        re.compile(r'Wordle[^\d]*(\d+(?:,\d+)?)[^\d]*(\d)/6', re.IGNORECASE),
        # Very flexible format
        re.compile(r'(?:^|[\s\n])Wordle.*?(\d+(?:,\d+)?)[^\d]*?(\d)/6', re.IGNORECASE | re.DOTALL),
    ]
    
    # Similar patterns for failed attempts (X/6)
    wordle_failed_patterns = [
        # Standard formats
        re.compile(r'Wordle\s*#?\s*(\d+(?:,\d+)?)\s*[-:;]?\s*X/6', re.IGNORECASE),
        # More flexible formats
        re.compile(r'Wordle[^\d]*(\d+(?:,\d+)?)[^\d]*X/6', re.IGNORECASE),
        # Very flexible format
        re.compile(r'(?:^|[\s\n])Wordle.*?(\d+(?:,\d+)?)[^\d]*?X/6', re.IGNORECASE | re.DOTALL),
    ]
    
    # Extract emoji patterns from the conversation text
    emoji_pattern_regex = re.compile(r'((?:[⬛⬜🟨🟩]{5}[\s\n]*){1,6})', re.MULTILINE)
    emoji_matches = re.findall(emoji_pattern_regex, conversation_text)
    
    valid_emoji_matches = []
    if emoji_matches:
        for match in emoji_matches:
            # Clean up the pattern by splitting into lines and rejoining with newlines
            rows = [row for row in re.findall(r'[⬛⬜🟨🟩]{5}', match) if row]
            if rows:  # If we have valid rows
                clean_pattern = '\n'.join(rows)
                valid_emoji_matches.append(clean_pattern)
    
    # Find the best emoji pattern (with the most rows)
    emoji_pattern_to_save = None
    if valid_emoji_matches:
        emoji_pattern_to_save = max(valid_emoji_matches, key=lambda p: p.count('\n') + 1)
    
    # Look for regular scores
    for pattern in wordle_score_patterns:
        matches = pattern.findall(conversation_text)
        if matches:
            # Get the first match
            match = matches[0]
            # Remove commas from the Wordle number
            wordle_num_str = match[0].replace(',', '')
            try:
                wordle_num = int(wordle_num_str)
                score = int(match[1])
                return (wordle_num, score, emoji_pattern_to_save)
            except ValueError:
                logging.warning(f"Could not convert Wordle number '{wordle_num_str}' or score '{match[1]}' to integer")
    
    # Look for failed attempts (X/6)
    for pattern in wordle_failed_patterns:
        matches = pattern.findall(conversation_text)
        if matches:
            # Get the first match
            match = matches[0]
            # Remove commas from the Wordle number
            wordle_num_str = match.replace(',', '')
            try:
                wordle_num = int(wordle_num_str)
                score = 7  # X/6 is represented as 7
                return (wordle_num, score, emoji_pattern_to_save)
            except ValueError:
                logging.warning(f"Could not convert Wordle number '{wordle_num_str}' to integer")
    
    # If we have an emoji pattern but no score text, try to infer the score
    if emoji_pattern_to_save:
        inferred_score = infer_score_from_emoji(emoji_pattern_to_save)
        if inferred_score is not None:
            # If we can infer a score but don't have a Wordle number, return None for wordle_num
            return (None, inferred_score, emoji_pattern_to_save)
    
    return (None, None, None)

def validate_database_scores():
    """Validate and clean database scores
    
    Removes scores with invalid player names, prevents duplicate scores
    for the same Wordle number and player, and adds any missing emoji patterns.
    """
    conn = None
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Remove scores with unknown players
        cursor.execute("SELECT id FROM score WHERE player_id NOT IN (SELECT id FROM player WHERE name NOT LIKE 'Unknown%')")
        unknown_scores = cursor.fetchall()
        
        if unknown_scores:
            logging.info(f"Found {len(unknown_scores)} scores with unknown players, removing them")
            cursor.execute("DELETE FROM score WHERE player_id NOT IN (SELECT id FROM player WHERE name NOT LIKE 'Unknown%')")
        
        # Check for duplicate scores (same player, same wordle number)
        cursor.execute("""
            SELECT s1.id, s1.wordle_number, p.name, s1.score, s1.emoji_pattern, s1.date 
            FROM score s1 
            JOIN player p ON s1.player_id = p.id
            JOIN (
                SELECT wordle_number, player_id, COUNT(*) as cnt
                FROM score
                GROUP BY wordle_number, player_id
                HAVING COUNT(*) > 1
            ) s2 ON s1.wordle_number = s2.wordle_number AND s1.player_id = s2.player_id
            ORDER BY s1.wordle_number DESC, s1.player_id, s1.score
        """)
        
        duplicates = cursor.fetchall()
        if duplicates:
            logging.info(f"Found {len(duplicates)} duplicate scores")
            
            # Group duplicates by wordle number and player
            duplicate_groups = {}
            for dup in duplicates:
                key = (dup['wordle_number'], dup['name'])
                if key not in duplicate_groups:
                    duplicate_groups[key] = []
                duplicate_groups[key].append(dup)
            
            # Process each group
            for key, group in duplicate_groups.items():
                wordle_num, player_name = key
                logging.info(f"Processing duplicates for Wordle #{wordle_num}, Player: {player_name}")
                
                # Find the best score (lowest numeric score)
                best_score = min(group, key=lambda x: x['score'])
                
                # Find the entry with the most emoji rows
                entries_with_emoji = [e for e in group if e['emoji_pattern']]
                if entries_with_emoji:
                    best_emoji = max(
                        entries_with_emoji, 
                        key=lambda x: x['emoji_pattern'].count('\n') + 1 if x['emoji_pattern'] else 0
                    )
                    
                    # Combine best score with best emoji pattern
                    if best_score['id'] != best_emoji['id']:
                        logging.info(f"Keeping score {best_score['score']} from ID {best_score['id']} but using emoji pattern from ID {best_emoji['id']}")
                        cursor.execute(
                            "UPDATE score SET emoji_pattern = ? WHERE id = ?",
                            (best_emoji['emoji_pattern'], best_score['id'])
                        )
                
                # Delete all other entries
                for entry in group:
                    if entry['id'] != best_score['id']:
                        logging.info(f"Deleting duplicate score ID {entry['id']}")
                        cursor.execute("DELETE FROM score WHERE id = ?", (entry['id'],))
        
        conn.commit()
        logging.info("Database validation completed")
        
        return True
    except Exception as e:
        logging.error(f"Database validation error: {e}")
        return False
    finally:
        if conn:
            conn.close()

# Example usage function
def test_extraction():
    # This is just a test function to demonstrate the improved extraction
    test_texts = [
        "Wordle 1,500 6/6\n\n⬛⬛🟨⬛⬛\n⬛⬛⬛🟨⬛\n⬛🟨⬛⬛⬛\n⬛🟨🟨🟨⬛\n🟩⬛🟩⬛🟩\n🟩🟩🟩🟩🟩",  # Nanna's pattern
        "Wordle 1500 X/6\n\n⬛⬛⬛⬛⬛\n⬛⬛⬛⬛⬛\n⬛⬛⬛⬛⬛\n⬛⬛⬛⬛⬛\n⬛⬛⬛⬛⬛\n⬛⬛⬛⬛⬛",  # Malia's pattern
        "Wordle #1500: 4/6\n\n⬛⬛⬛⬛⬛\n⬛⬛⬛⬛⬛\n⬛⬛⬛⬛⬛\n🟩🟩🟩🟩🟩",  # Different format
        "Wordle 1500 (4/6)\n⬛⬛⬛⬛⬛\n⬛⬛⬛⬛⬛\n⬛⬛⬛⬛⬛\n🟩🟩🟩🟩🟩",  # Format with parentheses
    ]
    
    for i, text in enumerate(test_texts):
        print(f"\n--- Test Text {i+1} ---")
        print(text)
        result = extract_enhanced_wordle_scores(text)
        print(f"Extracted: Wordle #{result[0]}, Score: {result[1]}/6, Emoji pattern: {result[2]}")
        
        if result[1] is not None and result[2] is not None:
            inferred = infer_score_from_emoji(result[2])
            print(f"Inferred score from emoji: {inferred}/6")
            print(f"Match with extracted: {'Yes' if result[1] == inferred else 'No'}")

if __name__ == "__main__":
    # Run tests
    test_extraction()
    
    # Validate database
    validate_database_scores()
