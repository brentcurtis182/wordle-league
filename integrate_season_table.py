#!/usr/bin/env python3
"""
Season Table Integration Script for Wordle League
This script ensures that the Season table feature is properly maintained in the
automated scheduler scripts by modifying the appropriate update functions.
"""

import os
import re
import shutil
from datetime import datetime

def backup_file(file_path):
    """Create a backup of a file before modifying it"""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup: {backup_path}")
    return backup_path

def check_file_for_season_code(file_path):
    """Check if a file already has Season table code"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Check for season-related code markers
    has_season_container = 'season-container' in content
    has_season_table = 'season-table' in content
    has_season_winners = 'season_winners' in content
    
    if has_season_container and has_season_table:
        print(f"File already has Season table code: {file_path}")
        return True
    else:
        print(f"File needs Season table code integration: {file_path}")
        return False

def modify_update_correct_structure(file_path):
    """Add Season table code to update_correct_structure.py if needed"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
        
    # Check if file already has Season table code
    if check_file_for_season_code(file_path):
        return True
        
    # Create a backup before modifying
    backup_path = backup_file(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add season_winners table creation if not present
    if 'CREATE TABLE IF NOT EXISTS season_winners' not in content:
        db_setup_pattern = r'def setup_database\(\):'
        season_table_code = '''def setup_database():
    # Create season_winners table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS season_winners (
        id INTEGER PRIMARY KEY,
        player_id INTEGER,
        league_id INTEGER,
        week_date TEXT,
        score INTEGER,
        FOREIGN KEY (player_id) REFERENCES players (id),
        FOREIGN KEY (league_id) REFERENCES leagues (id)
    )
    """)
    conn.commit()'''
        
        content = re.sub(db_setup_pattern, season_table_code, content)
    
    # Add weekly reset logic for season winners
    if 'season_winners' not in content or 'is_monday' not in content:
        reset_pattern = r'def check_for_weekly_reset\(\):'
        weekly_reset_code = '''def check_for_weekly_reset():
    """Check if today is Monday and we need to reset weekly stats"""
    today = datetime.now()
    is_monday = today.weekday() == 0  # Monday is 0
    
    if is_monday:
        # Get current weekly winners and add to the season_winners table if it's Monday
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all leagues
        cursor.execute("SELECT id FROM leagues")
        leagues = cursor.fetchall()
        
        for league in leagues:
            league_id = league['id']
            
            # Get weekly winners (players with the lowest average score this week)
            cursor.execute("""
                SELECT p.id, p.name, MIN(weekly_avg) as best_avg
                FROM (
                    SELECT player_id, AVG(score) as weekly_avg
                    FROM scores s
                    JOIN players p ON s.player_id = p.id
                    WHERE p.league_id = ?
                    AND s.date >= date('now', '-7 day')
                    AND s.score < 7  -- Exclude failed attempts
                    GROUP BY player_id
                    HAVING COUNT(score) >= 3  -- At least 3 scores this week
                ) weekly_stats
                JOIN players p ON weekly_stats.player_id = p.id
                GROUP BY p.id
            """, (league_id,))
            
            winners = cursor.fetchall()
            
            for winner in winners:
                player_id = winner['id']
                
                # Check if already recorded for this week
                cursor.execute("""
                    SELECT id FROM season_winners 
                    WHERE player_id = ? AND league_id = ? AND week_date >= date('now', '-7 day')
                """, (player_id, league_id))
                
                if cursor.fetchone() is None:
                    # Add to season_winners
                    cursor.execute("""
                        INSERT INTO season_winners (player_id, league_id, week_date, score)
                        VALUES (?, ?, date('now'), ?)
                    """, (player_id, league_id, winner['best_avg']))
                    conn.commit()
                    print(f"Added season win for player {winner['name']} in league {league_id}")
                
        conn.close()
        return True
    else:
        return False'''
        
        content = re.sub(reset_pattern, weekly_reset_code, content)
    
    # Add Season table creation in rebuild_stats_tab
    if 'rebuild_stats_tab' not in content or 'season_container' not in content:
        stats_pattern = r'def rebuild_stats_tab\(soup, db_conn, league_id, all_time_stats\):'
        stats_code = '''def rebuild_stats_tab(soup, db_conn, league_id, all_time_stats):
    """Rebuild the Season and All-Time Stats tab content"""
    # Find the stats div
    stats_div = soup.find('div', {'id': 'stats'})
    if not stats_div:
        return soup
    
    # Update tab name if needed
    stats_button = soup.find('button', {'data-tab': 'stats'})
    if stats_button and stats_button.string != "Season / All-Time Stats":
        stats_button.string = "Season / All-Time Stats"
    
    # Clear existing stats content but keep the h2 title
    h2_title = stats_div.find('h2')
    stats_div.clear()
    if h2_title:
        stats_div.append(h2_title)
    
    # 1. Create Season container
    season_container = soup.new_tag('div', attrs={'class': 'season-container', 'style': 'margin-bottom: 30px;'})
    
    # Add Season heading
    season_heading = soup.new_tag('h3', attrs={'style': 'margin-bottom: 10px; color: #6aaa64;'})
    season_heading.string = 'Season 1'
    season_container.append(season_heading)
    
    # Add Season description
    SEASON_TEXT = "If players are tied at the end of the week, then both players get a weekly win. First Player to get 4 weekly wins, is the Season Champ!"
    season_desc = soup.new_tag('p', attrs={'style': 'margin-bottom: 15px; font-size: 14px;'})
    season_desc.string = SEASON_TEXT
    season_container.append(season_desc)
    
    # Create Season table
    season_table = soup.new_tag('table', attrs={'class': 'season-table'})
    
    # Create table header
    thead = soup.new_tag('thead')
    tr = soup.new_tag('tr')
    
    for header in ['Player', 'Weekly Wins', 'Wordle Week (Score)']:
        th = soup.new_tag('th')
        th.string = header
        tr.append(th)
    
    thead.append(tr)
    season_table.append(thead)
    
    # Create table body
    tbody = soup.new_tag('tbody')
    
    # Get season winners data from database
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT p.name, COUNT(*) as weekly_wins, MAX(sw.week_date) as latest_week, MIN(sw.score) as best_score
        FROM players p
        JOIN season_winners sw ON p.id = sw.player_id
        WHERE p.league_id = ?
        GROUP BY p.name
        ORDER BY weekly_wins DESC, best_score ASC
    """, (league_id,))
    
    season_winners = cursor.fetchall()
    
    if season_winners:
        # Add rows for each winner
        for winner in season_winners:
            tr = soup.new_tag('tr')
            
            # Player name
            td_player = soup.new_tag('td')
            td_player.string = winner[0]  # player name
            tr.append(td_player)
            
            # Weekly wins
            td_wins = soup.new_tag('td')
            td_wins.string = str(winner[1])  # weekly_wins
            tr.append(td_wins)
            
            # Week info - get the latest week from season_winners table
            td_week = soup.new_tag('td')
            cursor.execute("""
                SELECT w.wordle_num
                FROM season_winners sw
                JOIN wordles w ON sw.week_date = w.date
                WHERE sw.week_date = ?
            """, (winner[2],))  # latest_week
            
            wordle_info = cursor.fetchone()
            week_info = f"#{wordle_info[0]}" if wordle_info else winner[2]
            score_info = f" ({winner[3]:.2f})" if winner[3] is not None else ""
            td_week.string = f"{week_info}{score_info}"
            tr.append(td_week)
            
            tbody.append(tr)
    else:
        # No winners yet
        tr = soup.new_tag('tr')
        td = soup.new_tag('td', attrs={'colspan': '3', 'style': 'text-align: center;'})
        td.string = "No weekly winners yet"
        tr.append(td)
        tbody.append(tr)
    
    season_table.append(tbody)
    season_container.append(season_table)
    
    # Add season container to stats div
    stats_div.append(season_container)
    
    # 2. Create All-Time Stats container
    all_time_container = soup.new_tag('div', attrs={'class': 'all-time-container'})
    
    # Add All-Time Stats heading
    all_time_heading = soup.new_tag('h3', attrs={'style': 'margin-top: 20px; margin-bottom: 10px; color: #6aaa64;'})
    all_time_heading.string = 'All-Time Stats'
    all_time_container.append(all_time_heading)
    
    # Add All-Time Stats description
    all_time_desc_text = "Average includes all games. Failed attempts (X/6) count as 7 in the average calculation."
    all_time_desc = soup.new_tag('p', attrs={'style': 'margin-bottom: 15px; font-size: 14px;'})
    all_time_desc.string = all_time_desc_text
    all_time_container.append(all_time_desc)
    
    # Create table container
    table_container = soup.new_tag('div', attrs={'class': 'table-container'})
    
    # Create All-Time Stats table
    table = soup.new_tag('table')
    
    # Create table header
    thead = soup.new_tag('thead')
    tr = soup.new_tag('tr')
    
    for header in ['Player', 'Games Played', 'Average Score', 'Failed Attempts']:
        th = soup.new_tag('th')
        th.string = header
        tr.append(th)
    
    thead.append(tr)
    table.append(thead)
    
    # Create table body
    tbody = soup.new_tag('tbody')
    
    # Find the best average score to highlight
    best_avg = float('inf')
    best_player = None
    
    for name, stats in all_time_stats.items():
        avg = stats.get('average', '-')
        if avg != '-' and float(avg) < best_avg:
            best_avg = float(avg)
            best_player = name
    
    # Add rows for each player
    for name, stats in all_time_stats.items():
        tr = soup.new_tag('tr')
        
        # Highlight the player with the lowest average score
        if name == best_player:
            tr['class'] = tr.get('class', []) + ['highlight']
            tr['style'] = 'background-color: rgba(106, 170, 100, 0.2);'
        
        # Player name
        td_player = soup.new_tag('td')
        td_player.string = name
        tr.append(td_player)
        
        # Games played
        td_games = soup.new_tag('td')
        td_games.string = str(stats.get('games_played', '-'))
        tr.append(td_games)
        
        # Average score
        td_avg = soup.new_tag('td')
        td_avg.string = str(stats.get('average', '-'))
        tr.append(td_avg)
        
        # Failed attempts
        td_failed = soup.new_tag('td')
        td_failed.string = str(stats.get('failed_attempts', ''))
        tr.append(td_failed)
        
        tbody.append(tr)
    
    table.append(tbody)
    table_container.append(table)
    all_time_container.append(table_container)
    
    # Add All-Time container to stats div
    stats_div.append(all_time_container)
    
    return soup'''
        
        content = re.sub(stats_pattern, stats_code, content)
    
    # Update the update_league_html function to use rebuild_stats_tab
    update_pattern = r'def update_league_html\([^)]*\):'
    if 'rebuild_stats_tab' not in content or 'update_league_html' not in content:
        update_code = '''def update_league_html(league_id, html_path):
    """Update the HTML file for a given league"""
    try:
        if not os.path.exists(html_path):
            print(f"Error: {html_path} does not exist")
            return False
            
        db_conn = connect_to_db()
        
        # Read the HTML file
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        soup = BeautifulSoup(content, 'html.parser')
        
        # Get current Wordle info
        wordle_num, wordle_date = get_current_wordle(db_conn)
        
        # Get latest scores for this league
        latest_scores = get_latest_scores(db_conn, league_id)
        
        # Get weekly stats
        weekly_stats_data = get_weekly_stats(db_conn, league_id)
        
        # Get all-time stats
        all_time_stats = get_all_time_stats(db_conn, league_id)
        
        # Update Wordle info
        soup = update_wordle_info(soup, wordle_num, wordle_date)
        
        # Update latest scores
        soup = update_latest_scores(soup, latest_scores, league_id)
        
        # Update weekly stats
        soup = update_weekly_stats(soup, weekly_stats_data)
        
        # Rebuild both Season and All-Time Stats sections
        soup = rebuild_stats_tab(soup, db_conn, league_id, all_time_stats)
        
        # Save the updated HTML
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        db_conn.close()
        print(f"Successfully updated {html_path}")
        return True
    except Exception as e:
        print(f"Error updating {html_path}: {e}")
        import traceback
        traceback.print_exc()
        return False'''
        
        content = re.sub(update_pattern, update_code, content)
    
    # Write the modified content back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Updated {file_path} with Season table code")
    return True

def main():
    print("Integrating Season Table feature with automated scripts...")
    
    # Define file paths
    update_script = "update_correct_structure.py"
    
    # Update the main update script
    if os.path.exists(update_script):
        modify_update_correct_structure(update_script)
        print(f"Successfully integrated Season table into {update_script}")
    else:
        print(f"Warning: {update_script} not found")
    
    print("\nIntegration complete!")
    print("\nThe Season table feature is now properly integrated with the automated scheduler.")
    print("Weekly winners will be tracked in the season_winners table and displayed on the website.")
    print("The first player to reach 4 weekly wins will be crowned the Season Champion!")
    
if __name__ == "__main__":
    main()
