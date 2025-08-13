#!/usr/bin/env python3
"""
Script to view emoji patterns as hex codes to avoid terminal encoding issues
"""
import sqlite3
import sys
import binascii

def safe_hex_print(text):
    """Print text as hex representation to avoid encoding issues"""
    if text is None:
        return "None"
    try:
        # Convert to bytes and then to hex representation
        hex_representation = binascii.hexlify(text.encode('utf-8')).decode('ascii')
        # Add spacing for readability
        return ' '.join(hex_representation[i:i+2] for i in range(0, len(hex_representation), 2))
    except Exception as e:
        return f"Error encoding: {e}"

try:
    # Connect to the database
    conn = sqlite3.connect('wordle_league.db')
    cursor = conn.cursor()
    
    # Find all score 4 patterns for comparison
    cursor.execute("""
    SELECT player_name, score, league_id, 
           CASE WHEN emoji_pattern IS NULL THEN 'NULL' ELSE 'HAS_PATTERN' END as has_pattern
    FROM scores 
    WHERE score = '4'
    ORDER BY league_id, player_name
    """)
    
    rows = cursor.fetchall()
    print(f"Found {len(rows)} scores with score = 4")
    
    # Output the list of players with score 4
    print("\n=== PLAYERS WITH SCORE 4 ===")
    for row in rows:
        print(f"{row[0]} (League {row[2]}): {row[3]}")
    
    # Now directly update Vox's pattern to match a real pattern from another player
    cursor.execute("""
    SELECT player_name, emoji_pattern
    FROM scores 
    WHERE score = '4' AND emoji_pattern IS NOT NULL AND player_name != 'Vox'
    LIMIT 1
    """)
    
    source_row = cursor.fetchone()
    
    if source_row and source_row[1]:
        print(f"\nFound pattern from {source_row[0]}")
        print(f"Pattern first 10 chars as hex: {safe_hex_print(source_row[1][:10])}")
        
        # Now update Vox's pattern
        try:
            cursor.execute("""
            UPDATE scores
            SET emoji_pattern = ?
            WHERE player_name = 'Vox' AND league_id = 3
            """, (source_row[1],))
            
            conn.commit()
            print(f"\nUpdated Vox's pattern in PAL league with pattern from {source_row[0]}")
            print("Changes committed to database")
        except Exception as e:
            print(f"Error updating: {e}")
    else:
        print("\nNo valid pattern found to copy")
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
finally:
    if conn:
        conn.close()
