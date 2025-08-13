import sqlite3

def check_vox_scores():
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Check Vox's Wordle #1503 scores
        cursor.execute("""
        SELECT id, player_name, wordle_num, score, timestamp, league_id
        FROM scores
        WHERE player_name = 'Vox' AND (wordle_num = '1503' OR wordle_num = '1,503')
        """)
        
        print("===== VOX'S WORDLE #1503 SCORES =====")
        scores = cursor.fetchall()
        if scores:
            for id, player, wordle, score, timestamp, league_id in scores:
                league_name = "Warriorz" if league_id == 1 else "PAL" if league_id == 3 else f"League {league_id}"
                print(f"ID: {id}, League: {league_name}, Wordle: {wordle}, Score: {score}/6, Date: {timestamp}")
            print(f"\nTotal: {len(scores)} records found")
        else:
            print("No Wordle #1503 scores found for Vox")
            
        # Also check for duplicates
        cursor.execute("""
        SELECT player_name, wordle_num, COUNT(*) as count
        FROM scores
        WHERE player_name = 'Vox'
        GROUP BY player_name, wordle_num
        HAVING count > 1
        """)
        
        duplicates = cursor.fetchall()
        if duplicates:
            print("\n===== DUPLICATE SCORES FOR VOX =====")
            for player, wordle, count in duplicates:
                print(f"Wordle #{wordle}: {count} duplicate entries")
        else:
            print("\nNo duplicate entries found for Vox")
            
    except Exception as e:
        print(f"Error checking scores: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_vox_scores()
