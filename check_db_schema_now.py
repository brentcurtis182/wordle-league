import sqlite3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

def check_database_schema():
    """Check the schema of all tables in the database"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        logging.info(f"Found {len(tables)} tables in wordle_league.db:")
        for table in tables:
            table_name = table[0]
            logging.info(f"\nTable: {table_name}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            logging.info(f"  Columns ({len(columns)}):")
            for col in columns:
                logging.info(f"    {col[0]}: {col[1]} ({col[2]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            logging.info(f"  Row count: {count}")
            
            # Show sample data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            rows = cursor.fetchall()
            if rows:
                logging.info(f"  Sample data (up to 3 rows):")
                for row in rows:
                    logging.info(f"    {row}")
        
        conn.close()
        
    except Exception as e:
        logging.error(f"Error checking database schema: {e}")

if __name__ == "__main__":
    check_database_schema()
