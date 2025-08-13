import sqlite3
import sys
import io

# Configure UTF-8 for output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def extract_wordle1500_patterns():
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get player information
        cursor.execute("SELECT id, name, phone_number FROM player")
        players = {row['id']: {'name': row['name'], 'phone': row['phone_number']} for row in cursor.fetchall()}
        
        print(f"Found {len(players)} players in database")
        
        # Check both tables: 'score' and 'scores' for Wordle 1500 data
        results = {}
        
        # Check 'score' table first (seems to be the main table from the memories)
        print("\nChecking 'score' table for Wordle #1500 patterns:")
        cursor.execute("""
            SELECT player_id, score, emoji_pattern 
            FROM score 
            WHERE wordle_id = 1500
        """)
        
        for row in cursor.fetchall():
            player_id = row['player_id']
            score = row['score']
            pattern = row['emoji_pattern']
            
            if player_id in players and pattern and pattern.strip():
                player_name = players[player_id]['name']
                print(f"\nFound pattern for {player_name} in 'score' table:")
                print(f"Score: {score}/6")
                print(f"Pattern:\n{pattern}")
                
                results[player_name] = {
                    'score': score,
                    'pattern': pattern,
                    'source': 'score table',
                    'rows': pattern.count('\n') + 1 if pattern else 0
                }
        
        # Also check 'scores' table
        print("\nChecking 'scores' table for Wordle #1500 patterns:")
        cursor.execute("""
            SELECT player_id, score, emoji_pattern 
            FROM scores 
            WHERE wordle_id = 1500
        """)
        
        for row in cursor.fetchall():
            player_id = row['player_id']
            score = row['score']
            pattern = row['emoji_pattern']
            
            if player_id in players and pattern and pattern.strip():
                player_name = players[player_id]['name']
                
                if player_name in results:
                    # Only show if different from the score table
                    if pattern != results[player_name]['pattern']:
                        print(f"\nFound DIFFERENT pattern for {player_name} in 'scores' table:")
                        print(f"Score: {score}/6")
                        print(f"Pattern:\n{pattern}")
                        results[player_name]['alt_pattern'] = pattern
                        results[player_name]['alt_source'] = 'scores table'
                else:
                    print(f"\nFound pattern for {player_name} in 'scores' table:")
                    print(f"Score: {score}/6")
                    print(f"Pattern:\n{pattern}")
                    
                    results[player_name] = {
                        'score': score,
                        'pattern': pattern,
                        'source': 'scores table',
                        'rows': pattern.count('\n') + 1 if pattern else 0
                    }
        
        # Print summary
        print("\n===== EXTRACTED PATTERNS FOR WORDLE #1500 =====")
        for player, data in results.items():
            print(f"\n{player} - Score: {data['score']}/6 ({data['rows']} rows) [Source: {data['source']}]")
            print(data['pattern'])
            
            if 'alt_pattern' in data:
                print(f"\nAlternate pattern [Source: {data['alt_source']}]:")
                print(data['alt_pattern'])
            
            print("-" * 20)
        
        # Print a summary in a format that can be used in code
        print("\n\nPATTERN SUMMARY FOR CODE USE:")
        print("patterns = {")
        for player, data in results.items():
            # Format the pattern for code (with proper escaping)
            pattern_code = repr(data['pattern'])
            print(f"    '{player}': {pattern_code},")
        print("}")
            
        conn.close()
        return results
        
    except Exception as e:
        print(f"Error accessing database: {e}")
        return {}

if __name__ == "__main__":
    print("Extracting Wordle #1500 patterns from database...\n")
    patterns = extract_wordle1500_patterns()
    
    if not patterns:
        print("\nNo patterns found in the database.")
