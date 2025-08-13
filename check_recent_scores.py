#!/usr/bin/env python3
import sqlite3
from datetime import datetime, timedelta

def main():
    # Connect to database
    conn = sqlite3.connect('wordle_league.db')
    cursor = conn.cursor()
    
    # Check today's scores
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"\nScores for TODAY ({today}):")
    cursor.execute('SELECT player_name, score, wordle_num, timestamp, league_id FROM scores WHERE timestamp LIKE ? ORDER BY league_id', (f'{today}%',))
    today_results = cursor.fetchall()
    print(f'Found {len(today_results)} scores for today')
    [print(f'Player: {r[0]}, Score: {r[1]}/6, Wordle #{r[2]}, League: {r[4]}') for r in today_results]
    
    # League specific counts for today
    cursor.execute('SELECT COUNT(*) FROM scores WHERE timestamp LIKE ? AND league_id = 1', (f'{today}%',))
    print(f'League 1 (Wordle Warriorz) scores today: {cursor.fetchone()[0]}')
    cursor.execute('SELECT COUNT(*) FROM scores WHERE timestamp LIKE ? AND league_id = 3', (f'{today}%',))
    print(f'League 3 (PAL) scores today: {cursor.fetchone()[0]}')
    
    # Check yesterday's scores
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    print(f"\nScores for YESTERDAY ({yesterday}):")
    cursor.execute('SELECT player_name, score, wordle_num, timestamp, league_id FROM scores WHERE timestamp LIKE ? ORDER BY league_id', (f'{yesterday}%',))
    yesterday_results = cursor.fetchall()
    print(f'Found {len(yesterday_results)} scores for yesterday')
    [print(f'Player: {r[0]}, Score: {r[1]}/6, Wordle #{r[2]}, League: {r[4]}') for r in yesterday_results]
    
    # League specific counts for yesterday
    cursor.execute('SELECT COUNT(*) FROM scores WHERE timestamp LIKE ? AND league_id = 1', (f'{yesterday}%',))
    print(f'League 1 (Wordle Warriorz) scores yesterday: {cursor.fetchone()[0]}')
    cursor.execute('SELECT COUNT(*) FROM scores WHERE timestamp LIKE ? AND league_id = 3', (f'{yesterday}%',))
    print(f'League 3 (PAL) scores yesterday: {cursor.fetchone()[0]}')
    
    # Check today's specific Wordle number
    today_wordle = 1503  # July 31, 2025 wordle number
    print(f"\nScores for Wordle #{today_wordle}:")
    cursor.execute('SELECT player_name, score, wordle_num, timestamp, league_id FROM scores WHERE wordle_num = ? ORDER BY league_id', (today_wordle,))
    wordle_results = cursor.fetchall()
    print(f'Found {len(wordle_results)} scores for Wordle #{today_wordle}')
    [print(f'Player: {r[0]}, Score: {r[1]}/6, Date: {r[3]}, League: {r[4]}') for r in wordle_results]
    
    # League specific counts for today's Wordle
    cursor.execute('SELECT COUNT(*) FROM scores WHERE wordle_num = ? AND league_id = 1', (today_wordle,))
    print(f'League 1 (Wordle Warriorz) scores for Wordle #{today_wordle}: {cursor.fetchone()[0]}')
    cursor.execute('SELECT COUNT(*) FROM scores WHERE wordle_num = ? AND league_id = 3', (today_wordle,))
    print(f'League 3 (PAL) scores for Wordle #{today_wordle}: {cursor.fetchone()[0]}')
    
    # Close connection
    conn.close()

if __name__ == "__main__":
    main()
