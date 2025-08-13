import sqlite3

def check_table_schema():
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Check score table schema
        print("SCORE TABLE SCHEMA:")
        cursor.execute("PRAGMA table_info(score)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[0]}: {col[1]} ({col[2]})")
        
        # Check scores table schema
        print("\nSCORES TABLE SCHEMA:")
        cursor.execute("PRAGMA table_info(scores)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[0]}: {col[1]} ({col[2]})")
            
        # Sample data from score
        print("\nSAMPLE FROM SCORE TABLE:")
        cursor.execute("SELECT * FROM score LIMIT 3")
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"  {row}")
        else:
            print("  No data in score table")
        
        # Sample data from scores
        print("\nSAMPLE FROM SCORES TABLE:")
        cursor.execute("SELECT * FROM scores LIMIT 3")
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"  {row}")
        else:
            print("  No data in scores table")
        
        conn.close()
    except Exception as e:
        print(f"Error checking schema: {e}")

if __name__ == "__main__":
    check_table_schema()
