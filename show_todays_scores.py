import sqlite3
import datetime

# Connect to the database
conn = sqlite3.connect('wordle_league.db')
c = conn.cursor()

# Get today's and yesterday's dates
today = datetime.date(2025, 7, 31)
yesterday = today - datetime.timedelta(days=1)
today_str = today.strftime('%Y-%m-%d')
yesterday_str = yesterday.strftime('%Y-%m-%d')

# Query for recent scores across all leagues (today and yesterday)
c.execute('''
    SELECT player_name, wordle_num, score, league_id, emoji_pattern, timestamp 
    FROM scores 
    WHERE date(timestamp) = ? OR date(timestamp) = ?
    ORDER BY league_id, player_name
''', (today_str, yesterday_str))

results = c.fetchall()

# Display the results
print(f"Today's Wordle Scores ({today_str}):")
print("=" * 50)

if not results:
    print("No scores found for today!")
else:
    # Group by league for better organization
    league_scores = {}
    for player_name, wordle_num, score, league_id, emoji, timestamp in results:
        if league_id not in league_scores:
            league_scores[league_id] = []
        league_scores[league_id].append((player_name, wordle_num, score, emoji, timestamp))

    # Map league IDs to names
    league_names = {
        1: "Wordle Warriorz",
        2: "Wordle Gang",
        3: "PAL League"
    }
    
    # Display scores by league
    for league_id, scores in league_scores.items():
        league_name = league_names.get(league_id, f"League {league_id}")
        print(f"\n🏆 {league_name} 🏆")
        print("-" * 50)
        
        for player_name, wordle_num, score, emoji, timestamp in scores:
            score_display = "X/6" if score == 7 else f"{score}/6"
            print(f"Player: {player_name}")
            print(f"Wordle #{wordle_num}: {score_display}")
            print(f"Submitted: {timestamp}")
            print("Emoji Pattern:")
            if emoji:
                print(emoji)
            else:
                print("No emoji pattern saved")
            print("-" * 30)

# Close the connection
conn.close()
