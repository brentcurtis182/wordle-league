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

def enhanced_score_extraction_demo():
    """Test the improved Wordle score extraction with various formats"""
    # Define some test cases (avoiding printing emoji directly)
    test_cases = [
        {
            'description': "Nanna's format with comma in number",
            'text': "Wordle 1,500 6/6",
            'expected_wordle': 1500,
            'expected_score': 6
        },
        {
            'description': "Malia's X/6 format",
            'text': "Wordle 1500 X/6",
            'expected_wordle': 1500,
            'expected_score': 7  # X/6 is represented as 7
        },
        {
            'description': "Format with # and colon",
            'text': "Wordle #1500: 4/6",
            'expected_wordle': 1500,
            'expected_score': 4
        },
        {
            'description': "Format with parentheses",
            'text': "Wordle 1500 (4/6)",
            'expected_wordle': 1500,
            'expected_score': 4
        },
        {
            'description': "Very unusual format",
            'text': "I got Wordle number 1,500 and scored 5/6",
            'expected_wordle': 1500,
            'expected_score': 5
        }
    ]
    
    logging.info("Testing improved Wordle score extraction")
    
    # Define our enhanced regex patterns
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
    
    # Test each case
    for i, case in enumerate(test_cases):
        logging.info(f"\nTesting case {i+1}: {case['description']}")
        logging.info(f"Input text: {case['text']}")
        
        # Try regular score patterns
        wordle_num = None
        score = None
        
        for pattern in wordle_score_patterns:
            matches = pattern.findall(case['text'])
            if matches:
                # Get the first match
                match = matches[0]
                # Remove commas from the Wordle number
                wordle_num_str = match[0].replace(',', '')
                try:
                    wordle_num = int(wordle_num_str)
                    score = int(match[1])
                    logging.info(f"Found score using pattern: {pattern.pattern}")
                    break
                except ValueError:
                    logging.warning(f"Could not convert values to integers")
        
        # If no regular score found, try failed patterns
        if wordle_num is None:
            for pattern in wordle_failed_patterns:
                matches = pattern.findall(case['text'])
                if matches:
                    # Get the first match
                    match = matches[0]
                    # Remove commas from the Wordle number
                    wordle_num_str = match.replace(',', '')
                    try:
                        wordle_num = int(wordle_num_str)
                        score = 7  # X/6 is represented as 7
                        logging.info(f"Found X/6 score using pattern: {pattern.pattern}")
                        break
                    except ValueError:
                        logging.warning(f"Could not convert Wordle number to integer")
        
        # Check against expected results
        if wordle_num == case['expected_wordle'] and score == case['expected_score']:
            logging.info(f"SUCCESS: Extracted Wordle #{wordle_num}, Score: {'X/6' if score == 7 else f'{score}/6'}")
        else:
            logging.error(f"FAILURE: Expected Wordle #{case['expected_wordle']}, Score: {'X/6' if case['expected_score'] == 7 else f'{case['expected_score']}/6'}")
            logging.error(f"         Got Wordle #{wordle_num}, Score: {'X/6' if score == 7 else f'{score}/6'}")
    
    logging.info("\nTesting completed!")

def validate_database_scores():
    """Validate and clean database scores
    
    Checks for and removes any scores with:
    1. Unknown players
    2. Duplicate entries for the same player and wordle number
    
    Returns:
        bool: True if validation was successful
    """
    logging.info("Starting database validation")
    
    conn = None
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check for scores with unknown players
        cursor.execute("""
            SELECT s.id, p.name, s.wordle_number, s.score 
            FROM score s
            JOIN player p ON s.player_id = p.id
            WHERE p.name LIKE 'Unknown%'
        """)
        
        unknown_scores = cursor.fetchall()
        if unknown_scores:
            logging.info(f"Found {len(unknown_scores)} scores with unknown players:")
            for score in unknown_scores:
                score_display = "X/6" if score['score'] == 7 else f"{score['score']}/6"
                logging.info(f"  ID {score['id']}: {score['name']} - Wordle #{score['wordle_number']} - {score_display}")
                
            # Ask if they should be removed
            logging.info("These Unknown player scores should be removed")
            cursor.execute("DELETE FROM score WHERE player_id IN (SELECT id FROM player WHERE name LIKE 'Unknown%')")
            deleted = cursor.rowcount
            logging.info(f"Deleted {deleted} unknown player scores")
        else:
            logging.info("No scores with unknown players found")
        
        # Check for duplicate scores (same player, same wordle number)
        cursor.execute("""
            SELECT s1.id, p.name, s1.wordle_number, s1.score
            FROM score s1
            JOIN player p ON s1.player_id = p.id
            JOIN (
                SELECT wordle_number, player_id, COUNT(*) as cnt
                FROM score
                GROUP BY wordle_number, player_id
                HAVING COUNT(*) > 1
            ) s2 ON s1.wordle_number = s2.wordle_number AND s1.player_id = s2.player_id
            ORDER BY s1.wordle_number DESC, s1.player_id, s1.id
        """)
        
        duplicates = cursor.fetchall()
        if duplicates:
            logging.info(f"Found {len(duplicates)} duplicate scores:")
            
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
                logging.info(f"\nDuplicates for Wordle #{wordle_num}, Player: {player_name}")
                
                for score in group:
                    score_display = "X/6" if score['score'] == 7 else f"{score['score']}/6"
                    logging.info(f"  ID {score['id']}: {score_display}")
                
                # Keep the lowest score ID (oldest entry) and delete others
                to_keep = min(group, key=lambda x: x['id'])
                logging.info(f"Keeping score ID {to_keep['id']}")
                
                for score in group:
                    if score['id'] != to_keep['id']:
                        logging.info(f"Deleting duplicate score ID {score['id']}")
                        cursor.execute("DELETE FROM score WHERE id = ?", (score['id'],))
        else:
            logging.info("No duplicate scores found")
        
        conn.commit()
        logging.info("Database validation completed successfully")
        return True
        
    except Exception as e:
        logging.error(f"Database validation error: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logging.info("Starting improved extraction tests")
    enhanced_score_extraction_demo()
    
    logging.info("\n\n===== DATABASE VALIDATION =====")
    validate_database_scores()
