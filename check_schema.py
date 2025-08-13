#!/usr/bin/env python3
import sqlite3
import sys

DB_PATH = 'wordle_league.db'

def get_table_info(table_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get table schema
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    print(f"\nSchema for table '{table_name}':")
    for col in columns:
        print(f"  {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] == 1 else ''}")
    
    conn.close()

def main():
    print(f"Database: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("\nTables in database:")
    for i, table in enumerate(tables):
        print(f"{i+1}. {table[0]}")
    
    conn.close()
    
    # Get schema for key tables
    get_table_info('scores')
    get_table_info('score')
    get_table_info('players')
    get_table_info('leagues')

if __name__ == "__main__":
    main()
