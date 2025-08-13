import sqlite3

def check_all_tables():
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("ALL TABLES IN DATABASE:")
        for table in tables:
            table_name = table[0]
            print(f"\n=== TABLE: {table_name} ===")
            
            # Get schema for table
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print("SCHEMA:")
            for col in columns:
                print(f"  {col[1]}: {col[2]}, {'NOT NULL' if col[3] else 'NULL'}, Default: {col[4]}")
            
            # Check for phone number related columns
            phone_cols = [col[1] for col in columns if 'phone' in col[1].lower()]
            if phone_cols:
                print(f"\nPHONE RELATED COLUMNS: {', '.join(phone_cols)}")
                
                # Show sample data for phone columns
                for col in phone_cols:
                    cursor.execute(f"SELECT DISTINCT {col} FROM {table_name} LIMIT 5")
                    samples = cursor.fetchall()
                    print(f"  Sample {col} values: {[s[0] for s in samples]}")
            
        conn.close()
        return True
    except Exception as e:
        print(f"Error checking schema: {e}")
        return False

if __name__ == "__main__":
    check_all_tables()
