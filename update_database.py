import sqlite3
import os
import sys

def update_database(db_path):
    """Add player_name column to scores table and display schema information."""
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables in database: {[t[0] for t in tables]}")
        
        # Check if scores table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scores'")
        if cursor.fetchone():
            # Get current schema of scores table
            cursor.execute("PRAGMA table_info(scores)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            print(f"Current columns in scores table: {column_names}")
            
            # Check if player_name column already exists
            if 'player_name' not in column_names:
                print("Adding player_name column to scores table...")
                cursor.execute("ALTER TABLE scores ADD COLUMN player_name TEXT")
                conn.commit()
                print("Column added successfully!")
            else:
                print("player_name column already exists in scores table.")
                
            # Display updated schema
            cursor.execute("PRAGMA table_info(scores)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            print(f"Updated columns in scores table: {column_names}")
        else:
            print("scores table does not exist. Creating it...")
            cursor.execute("""
                CREATE TABLE scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT,
                    wordle_number TEXT,
                    score TEXT,
                    date_added TEXT
                )
            """)
            conn.commit()
            print("scores table created with player_name column!")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating database: {e}")
        return False

if __name__ == "__main__":
    # Default database path
    db_path = os.path.join(os.getcwd(), "wordle.db")
    
    # Allow custom path from command line
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    print(f"Updating database at: {db_path}")
    success = update_database(db_path)
    
    if success:
        print("Database update completed successfully!")
    else:
        print("Database update failed!")
