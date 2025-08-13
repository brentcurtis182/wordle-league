import sqlite3
import sys
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def fix_all_dates():
    """Update all dates in the database to match the correct dates for each Wordle number"""
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get all unique Wordle numbers
        cursor.execute("SELECT DISTINCT wordle_num FROM scores")
        wordle_nums = [row[0] for row in cursor.fetchall()]
        logging.info(f"Found {len(wordle_nums)} unique Wordle numbers to process")
        
        # Reference point: Wordle #1503 corresponds to July 31, 2025
        reference_date = datetime(2025, 7, 31).date()
        reference_wordle = 1503
        
        # Update each Wordle number with the correct date
        updates = 0
        for wordle_num_str in wordle_nums:
            # Handle comma-formatted numbers
            try:
                clean_wordle_num = int(str(wordle_num_str).replace(',', ''))
            except ValueError:
                logging.error(f"Could not parse Wordle number: {wordle_num_str}")
                continue
                
            # Calculate correct date based on reference point
            days_offset = clean_wordle_num - reference_wordle
            correct_date = reference_date + timedelta(days=days_offset)
            
            # Format as timestamp for the database (keep the original time)
            cursor.execute("""
            SELECT timestamp FROM scores WHERE wordle_num = ? LIMIT 1
            """, (wordle_num_str,))
            old_timestamp = cursor.fetchone()[0]
            
            # Extract the time portion from the old timestamp
            time_portion = old_timestamp.split()[1] if ' ' in old_timestamp else "00:00:00"
            
            # Create new timestamp with correct date but original time
            new_timestamp = f"{correct_date} {time_portion}"
            
            # Update all entries for this Wordle number
            cursor.execute("""
            UPDATE scores
            SET timestamp = ?
            WHERE wordle_num = ?
            """, (new_timestamp, wordle_num_str))
            
            affected = cursor.rowcount
            updates += affected
            logging.info(f"Updated Wordle #{wordle_num_str}: set date to {correct_date}, affected {affected} rows")
        
        conn.commit()
        logging.info(f"Successfully updated {updates} score entries with correct dates")
        
        # Verify the fix
        print("\n===== VERIFYING FIXES =====")
        # Check specific Wordle numbers
        for check_wordle in [1503, 1502, 1501]:
            cursor.execute("""
            SELECT wordle_num, timestamp, COUNT(*) 
            FROM scores 
            WHERE wordle_num = ? OR wordle_num = ?
            GROUP BY wordle_num
            """, (check_wordle, f"{check_wordle:,}"))
            
            for row in cursor.fetchall():
                wordle, timestamp, count = row
                date_str = timestamp.split()[0] if timestamp else "N/A"
                print(f"Wordle #{wordle}: {count} entries, date = {date_str}")
        
    except Exception as e:
        logging.error(f"Error fixing dates: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_all_dates()
