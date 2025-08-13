import sqlite3
import os
import sys

# Database configuration
script_dir = os.path.dirname(os.path.abspath(__file__))
default_db_path = os.path.join(script_dir, 'wordle_league.db')
DB_PATH = os.getenv('DATABASE_URI', f'sqlite:///{default_db_path}').replace('sqlite:///', '')

# List of real players to keep
REAL_PLAYERS = [
    'Brent',
    'Joanna',
    'Evan',
    'Malia',
    'Nanna'
]

def connect_to_db():
    """Connect to the SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def cleanup_database():
    """Remove fake players and their scores from the database"""
    conn = connect_to_db()
    if not conn:
        print("Failed to connect to database")
        return
    
    try:
        cursor = conn.cursor()
        
        # Get all players
        cursor.execute("SELECT id, name FROM player")
        all_players = cursor.fetchall()
        
        # Identify fake players (those not in our REAL_PLAYERS list)
        fake_players = []
        for player in all_players:
            if player['name'] not in REAL_PLAYERS:
                fake_players.append(player)
        
        if not fake_players:
            print("No fake players found in the database.")
            return
        
        print(f"Found {len(fake_players)} fake players to remove:")
        for player in fake_players:
            print(f"  - {player['name']} (ID: {player['id']})")
        
        # Automatically proceed with deletion
        print("\nAutomatically removing fake players...")
        # No confirmation needed - we're sure we want to remove these fake players
        
        # Delete scores for fake players
        for player in fake_players:
            cursor.execute("DELETE FROM score WHERE player_id = ?", (player['id'],))
            print(f"Deleted scores for player: {player['name']}")
        
        # Delete fake players
        for player in fake_players:
            cursor.execute("DELETE FROM player WHERE id = ?", (player['id'],))
            print(f"Deleted player: {player['name']}")
        
        # Commit changes
        conn.commit()
        print("\nDatabase cleanup completed successfully.")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print(f"Using database at: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database file not found at {DB_PATH}")
        sys.exit(1)
    
    cleanup_database()
