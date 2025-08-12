import sqlite3
import os

# Get database path
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'wordle_league.db')

print(f"Checking database at: {db_path}")
print(f"Database exists: {os.path.exists(db_path)}")

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\nTables in database: {[table[0] for table in tables]}")
    
    # For each table, show structure and sample data
    for table_name in [row[0] for row in tables]:
        print(f"\n--- Table: {table_name} ---")
        
        # Get table structure
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"Columns: {[col[1] for col in columns]}")
        
        # Get sample data (first 3 rows)
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        rows = cursor.fetchall()
        for i, row in enumerate(rows):
            print(f"Row {i+1}: {row}")
    
    # Close connection
    conn.close()

except Exception as e:
    print(f"Error accessing database: {e}")
