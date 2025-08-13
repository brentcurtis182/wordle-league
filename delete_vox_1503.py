import sqlite3

def delete_vox_false_score():
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # First check current state
        cursor.execute("""
        SELECT id, player_name, wordle_num, score, timestamp, league_id
        FROM scores
        WHERE player_name = 'Vox' AND (wordle_num = '1503' OR wordle_num = '1,503')
        """)
        
        print("===== VOX'S WORDLE #1503 SCORES BEFORE CLEANUP =====")
        scores = cursor.fetchall()
        if scores:
            for id, player, wordle, score, timestamp, league_id in scores:
                league_name = "Warriorz" if league_id == 1 else "PAL" if league_id == 3 else f"League {league_id}"
                print(f"ID: {id}, League: {league_name}, Wordle: {wordle}, Score: {score}/6, Date: {timestamp}")
        else:
            print("No Wordle #1503 scores found for Vox")

        # Delete the erroneous entry - Vox has not submitted a score for Wordle #1503
        cursor.execute("""
        DELETE FROM scores 
        WHERE player_name = 'Vox' AND (wordle_num = '1503' OR wordle_num = '1,503')
        """)
        
        deleted_count = cursor.rowcount
        print(f"\nDeleted {deleted_count} erroneous Wordle #1503 scores for Vox")
        
        # Verify Vox's Wordle #1502 score (should be preserved)
        cursor.execute("""
        SELECT id, player_name, wordle_num, score, timestamp, league_id
        FROM scores
        WHERE player_name = 'Vox' AND (wordle_num = '1502' OR wordle_num = '1,502')
        """)
        
        print("\n===== VOX'S WORDLE #1502 SCORES AFTER CLEANUP =====")
        scores = cursor.fetchall()
        if scores:
            for id, player, wordle, score, timestamp, league_id in scores:
                league_name = "Warriorz" if league_id == 1 else "PAL" if league_id == 3 else f"League {league_id}"
                print(f"ID: {id}, League: {league_name}, Wordle: {wordle}, Score: {score}/6, Date: {timestamp}")
        else:
            print("No Wordle #1502 scores found for Vox")
            
        # Commit the changes
        conn.commit()
        print("\nChanges committed successfully")
            
    except Exception as e:
        print(f"Error cleaning up scores: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    delete_vox_false_score()
