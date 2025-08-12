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
    
    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print(f"Tables in database: {[table[0] for table in tables]}")
    
    # Check if there's a players table
    if ('players',) in tables:
        print("\nPlayers Table Structure:")
        cursor.execute("PRAGMA table_info(players)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        print("\nLeagues in system:")
        cursor.execute("SELECT DISTINCT league_id FROM scores")
        leagues = cursor.fetchall()
        for league in leagues:
            print(f"League ID: {league[0]}")
            
            # Get players in this league
            print(f"\nPlayers in League {league[0]}:")
            cursor.execute("SELECT DISTINCT player_name FROM scores WHERE league_id = ?", (league[0],))
            players = cursor.fetchall()
            for player in players:
                print(f"  {player[0]}")
                
            # Check if Pants is in this league
            cursor.execute("SELECT COUNT(*) FROM scores WHERE player_name = 'Pants' AND league_id = ?", (league[0],))
            pants_count = cursor.fetchone()[0]
            print(f"Pants has {pants_count} entries in League {league[0]}")

    
    # Check for scores table
    for table_name in [row[0] for row in tables]:
        # Get schema for this table
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"\nTable: {table_name}")
        print(f"Columns: {[col[1] for col in columns]}")
        
        # Sample data
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
        rows = cursor.fetchall()
        print(f"Sample data: {rows}")
    
    # Close connection
    conn.close()

except Exception as e:
    print(f"Error accessing database: {e}")
