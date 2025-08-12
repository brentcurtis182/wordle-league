import sqlite3

def print_table_schema(table_name):
    print(f"\n=== {table_name.upper()} TABLE SCHEMA ===")
    conn = sqlite3.connect('wordle_league.db')
    cursor = conn.cursor()
    
    # Get table schema
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    print(f"Columns in {table_name} table:")
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
    
    # Get sample data (first row)
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
    row = cursor.fetchone()
    if row:
        print(f"\nSample row from {table_name}:")
        for i, col in enumerate(columns):
            try:
                print(f"- {col[1]}: {row[i]}")
            except:
                print(f"- {col[1]}: <ERROR>")
    
    conn.close()

print_table_schema('scores')
print_table_schema('players')
print_table_schema('leagues')
