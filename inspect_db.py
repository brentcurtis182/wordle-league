import sqlite3
import os
import sys

def inspect_database(db_path):
    """Inspect the database structure and content"""
    print(f"Inspecting database: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"Database contains {len(tables)} tables:")
    for table in tables:
        table_name = table[0]
        print(f"  - {table_name}")
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        print(f"    Columns ({len(columns)}):")
        for col in columns:
            print(f"      {col[1]} ({col[2]})")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        row_count = cursor.fetchone()[0]
        print(f"    Row count: {row_count}")
        
        # Sample data (first 3 rows)
        if row_count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            sample_rows = cursor.fetchall()
            print(f"    Sample data (max 3 rows):")
            for row in sample_rows:
                # Safely print row data, skipping emoji characters if needed
                safe_row = []
                for item in row:
                    if isinstance(item, str) and any(ord(c) > 127 for c in item):
                        safe_row.append('[contains emoji/unicode]')
                    else:
                        safe_row.append(item)
                print(f"      {safe_row}")
        
        print()  # Add a blank line between tables
    
    conn.close()

def fix_database(db_path):
    """Fix database by ensuring scores are only in the 'scores' table"""
    print(f"Fixing database: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if 'score' table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='score';")
    score_table_exists = cursor.fetchone() is not None
    
    if score_table_exists:
        print("Found 'score' table - this is likely causing data inconsistencies.")
        
        # Option to migrate any missing data to 'scores' table
        cursor.execute("SELECT * FROM score")
        old_scores = cursor.fetchall()
        print(f"Found {len(old_scores)} records in 'score' table")
        
        if old_scores:
            migrate = input("Do you want to migrate any missing scores to the 'scores' table? (y/n): ")
            if migrate.lower() == 'y':
                # Implementation would depend on the schema of both tables
                print("Migration would be implemented here based on schema")
        
        # Option to drop the old table
        drop_table = input("Do you want to drop the 'score' table? (y/n): ")
        if drop_table.lower() == 'y':
            cursor.execute("DROP TABLE score")
            conn.commit()
            print("'score' table dropped successfully")
    else:
        print("No 'score' table found - database structure appears correct")
    
    conn.close()

if __name__ == "__main__":
    db_path = "wordle_league.db"  # Default path
    
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    inspect_database(db_path)
    
    fix_option = input("\nDo you want to fix any database issues? (y/n): ")
    if fix_option.lower() == 'y':
        fix_database(db_path)
