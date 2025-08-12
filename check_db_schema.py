import sqlite3
import os

def check_database_tables():
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"Tables in database: {[table[0] for table in tables]}")
        
        # Check scores table structure (plural)
        print("\nChecking 'scores' table structure:")
        cursor.execute("PRAGMA table_info(scores)")
        columns = cursor.fetchall()
        print(f"Columns in 'scores': {[col[1] for col in columns]}")
        
        # Check score table structure (singular)
        print("\nChecking 'score' table structure:")
        cursor.execute("PRAGMA table_info(score)")
        columns = cursor.fetchall()
        print(f"Columns in 'score': {[col[1] for col in columns]}")
        
        # Get sample scores data
        print("\nSample scores data (plural):")
        cursor.execute("SELECT * FROM scores LIMIT 3")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
            
        # Get sample score data
        print("\nSample score data (singular):")
        cursor.execute("SELECT * FROM score LIMIT 3")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
        
        conn.close()
    except Exception as e:
        print(f"Error accessing database: {e}")

if __name__ == "__main__":
    check_database_tables()
