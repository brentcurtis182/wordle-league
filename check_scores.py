import sqlite3
import datetime

def check_scores():
    conn = sqlite3.connect('wordle_league.db')
    c = conn.cursor()
    
    print("Today's scores (Wordle #1504):")
    c.execute("SELECT player_name, wordle_num, score, league_id FROM scores WHERE wordle_num = 1504")
    for row in c.fetchall():
        print(f"{row[0]} (League {row[3]}): Score {row[2]}")
    
    print("\nYesterday's scores (Wordle #1503):")
    c.execute("SELECT player_name, wordle_num, score, league_id FROM scores WHERE wordle_num = 1503")
    for row in c.fetchall():
        print(f"{row[0]} (League {row[3]}): Score {row[2]}")
    
    print("\nScores by league:")
    for league_id in [1, 3]:  # Wordle Warriors and PAL leagues
        c.execute("SELECT COUNT(*) FROM scores WHERE league_id = ? AND wordle_num = 1504", (league_id,))
        count_today = c.fetchone()[0]
        print(f"League {league_id}: {count_today} scores for today (Wordle #1504)")
        
    conn.close()

if __name__ == "__main__":
    check_scores()
