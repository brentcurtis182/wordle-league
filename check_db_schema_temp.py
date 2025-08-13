import sqlite3
import sys

def check_schema():
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get schema for scores table
        cursor.execute("PRAGMA table_info(scores)")
        columns = cursor.fetchall()
        
        print("SCORES TABLE SCHEMA:")
        for col in columns:
            print(f"  {col[1]}: {col[2]}, {'NOT NULL' if col[3] else 'NULL'}, Default: {col[4]}")
        
        # Check sample data
        cursor.execute("SELECT * FROM scores LIMIT 1")
        sample = cursor.fetchone()
        if sample:
            cursor.execute("PRAGMA table_info(scores)")
            cols = [col[1] for col in cursor.fetchall()]
            print("\nSAMPLE SCORES ROW:")
            for i, col in enumerate(cols):
                print(f"  {col}: {sample[i]}")
                
        conn.close()
        return True
    except Exception as e:
        print(f"Error checking schema: {e}")
        return False

if __name__ == "__main__":
    check_schema()
