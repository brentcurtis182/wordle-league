#!/usr/bin/env python
# Validate the fixes we've made to ensure they'll persist with automated runs

import sqlite3
import logging
import json
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

def check_db_config():
    """Check that the main script is using the correct database"""
    try:
        with open('integrated_auto_update.py', 'r') as f:
            content = f.read()
        
        # Check which database the script is configured to use
        if 'wordle_league.db' in content and 'wordle_scores.db' not in content:
            logging.info("✅ integrated_auto_update.py correctly configured to use wordle_league.db")
            return True
        else:
            if 'wordle_scores.db' in content:
                logging.error("❌ integrated_auto_update.py is still using wordle_scores.db!")
            else:
                logging.warning("⚠️ Could not determine database configuration in script")
            return False
    except Exception as e:
        logging.error(f"Error checking script configuration: {e}")
        return False

def check_patterns():
    """Check that Joanna and Brent's patterns are correctly set in the database"""
    try:
        conn = sqlite3.connect("wordle_league.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        patterns = {}
        
        # Get Joanna's pattern
        cursor.execute("""
            SELECT s.id, p.name, s.wordle_number, s.score, s.emoji_pattern 
            FROM score s
            JOIN player p ON s.player_id = p.id
            WHERE p.name = 'Joanna' AND s.wordle_number = 1500
        """)
        joanna = cursor.fetchone()
        if joanna:
            pattern = joanna['emoji_pattern']
            rows = pattern.count('\n') + 1 if pattern else 0
            score = joanna['score']
            patterns['joanna'] = {
                'score': score,
                'rows': rows,
                'correct': rows == 5 and score == 5,
                'pattern': pattern
            }
            if patterns['joanna']['correct']:
                logging.info(f"✅ Joanna's pattern is correct: Score={score}/6, Rows={rows}")
            else:
                logging.error(f"❌ Joanna's pattern is incorrect: Score={score}/6, Rows={rows}")
        else:
            logging.error("❌ Could not find Joanna's score for Wordle 1500")
        
        # Get Brent's pattern
        cursor.execute("""
            SELECT s.id, p.name, s.wordle_number, s.score, s.emoji_pattern 
            FROM score s
            JOIN player p ON s.player_id = p.id
            WHERE p.name = 'Brent' AND s.wordle_number = 1500
        """)
        brent = cursor.fetchone()
        if brent:
            pattern = brent['emoji_pattern']
            rows = pattern.count('\n') + 1 if pattern else 0
            score = brent['score']
            patterns['brent'] = {
                'score': score,
                'rows': rows,
                'correct': rows == 6 and score == 6,
                'pattern': pattern
            }
            if patterns['brent']['correct']:
                logging.info(f"✅ Brent's pattern is correct: Score={score}/6, Rows={rows}")
            else:
                logging.error(f"❌ Brent's pattern is incorrect: Score={score}/6, Rows={rows}")
        else:
            logging.error("❌ Could not find Brent's score for Wordle 1500")
        
        conn.close()
        return patterns
    except Exception as e:
        logging.error(f"Error checking patterns: {e}")
        return {}

def check_for_empty_patterns():
    """Check for any empty or invalid patterns in the database"""
    try:
        conn = sqlite3.connect("wordle_league.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check for empty patterns
        cursor.execute("""
            SELECT s.id, p.name, s.wordle_number, s.score, s.emoji_pattern 
            FROM score s
            JOIN player p ON s.player_id = p.id
            WHERE s.emoji_pattern IS NULL OR s.emoji_pattern = ''
        """)
        empty_patterns = cursor.fetchall()
        
        if empty_patterns:
            logging.warning(f"⚠️ Found {len(empty_patterns)} scores with empty emoji patterns:")
            for row in empty_patterns:
                logging.warning(f"  - {row['name']}: Wordle {row['wordle_number']}, Score {row['score']}")
        else:
            logging.info("✅ No empty emoji patterns found in the database")
        
        # Check for inconsistent row counts
        cursor.execute("""
            SELECT s.id, p.name, s.wordle_number, s.score, s.emoji_pattern 
            FROM score s
            JOIN player p ON s.player_id = p.id
            WHERE s.emoji_pattern IS NOT NULL AND s.emoji_pattern != ''
        """)
        
        inconsistent = []
        for row in cursor.fetchall():
            pattern = row['emoji_pattern']
            rows = pattern.count('\n') + 1
            score = row['score']
            
            # Score 7 represents X/6, should have 6 rows
            expected_rows = min(score, 6)
            
            if rows != expected_rows:
                inconsistent.append({
                    'id': row['id'],
                    'name': row['name'],
                    'wordle': row['wordle_number'],
                    'score': score,
                    'rows': rows,
                    'expected': expected_rows
                })
        
        if inconsistent:
            logging.warning(f"⚠️ Found {len(inconsistent)} scores with inconsistent row counts:")
            for item in inconsistent:
                logging.warning(f"  - {item['name']}: Wordle {item['wordle']}, Score {item['score']}/6, " + 
                               f"Has {item['rows']} rows but should have {item['expected']}")
        else:
            logging.info("✅ All patterns have consistent row counts")
        
        conn.close()
        return empty_patterns, inconsistent
    except Exception as e:
        logging.error(f"Error checking for empty patterns: {e}")
        return [], []

def main():
    logging.info("Validating fixes to the Wordle League system...")
    
    # Check script configuration
    db_config_ok = check_db_config()
    
    # Check patterns
    patterns = check_patterns()
    
    # Check for empty or inconsistent patterns
    empty_patterns, inconsistent = check_for_empty_patterns()
    
    # Summarize results
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    all_ok = db_config_ok and patterns.get('joanna', {}).get('correct', False) and patterns.get('brent', {}).get('correct', False)
    
    if all_ok:
        print("\n✅ All critical fixes are in place and correct!")
        print("   - integrated_auto_update.py is using wordle_league.db")
        print("   - Joanna's pattern is correct (5 rows for 5/6)")
        print("   - Brent's pattern is correct (6 rows for 6/6)")
    else:
        print("\n⚠️ Some issues were found:")
        if not db_config_ok:
            print("   ❌ Database configuration issue in integrated_auto_update.py")
        if not patterns.get('joanna', {}).get('correct', False):
            print("   ❌ Joanna's pattern is incorrect")
        if not patterns.get('brent', {}).get('correct', False):
            print("   ❌ Brent's pattern is incorrect")
    
    # Minor issues
    if empty_patterns:
        print(f"\n⚠️ Found {len(empty_patterns)} scores with empty emoji patterns")
    if inconsistent:
        print(f"\n⚠️ Found {len(inconsistent)} scores with inconsistent row counts")
    
    print("\nThe system is " + ("ready" if all_ok else "NOT ready") + " for automated execution.")
    print("="*60)

if __name__ == "__main__":
    main()
