import sqlite3
import sys

def check_table_schema(db_path, table_name):
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print(f"Schema for table '{table_name}':")
        for col in columns:
            print(f"  Column {col[0]}: {col[1]} (Type: {col[2]}, NotNull: {col[3]}, DefaultVal: {col[4]}, PK: {col[5]})")
        
        # Check sample data
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
        row = cursor.fetchone()
        if row:
            print(f"\nSample data from '{table_name}':")
            print(row)
        else:
            print(f"\nNo data in '{table_name}'")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    db_path = "wordle_league.db"
    check_table_schema(db_path, "scores")
    check_table_schema(db_path, "players")
    check_table_schema(db_path, "season_winners")
    check_table_schema(db_path, "latest_scores")
    check_table_schema(db_path, "settings")
