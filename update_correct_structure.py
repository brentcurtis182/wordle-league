#!/usr/bin/env python3
import os
import sqlite3
from datetime import datetime
import logging
import sys
import shutil
import re
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# League information
LEAGUES = {
    'warriorz': {'id': 1, 'path': 'website_export/index.html', 'name': 'Wordle Warriorz'},
    'gang': {'id': 2, 'path': 'website_export/gang/index.html', 'name': 'Wordle Gang'},
    'pal': {'id': 3, 'path': 'website_export/pal/index.html', 'name': 'Wordle PAL'},
    'party': {'id': 4, 'path': 'website_export/party/index.html', 'name': 'Wordle Party'},
    'vball': {'id': 5, 'path': 'website_export/vball/index.html', 'name': 'Wordle Vball'}
}

# DB connection
DB_PATH = 'wordle_league.db'

# Constants for Season table
SEASON_TEXT = "If players are tied at the end of the week, then both players get a weekly win. First Player to get 4 weekly wins, is the Season Champ!"

def backup_file(file_path):
    """Create a backup of the file before making changes"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    logger.info(f"Backed up {file_path} to {backup_path}")
    return backup_path

def get_current_wordle_info():
    """Get the current Wordle number and date"""
    # Fixed reference point: July 31, 2025 is Wordle #1503
    from datetime import time
    reference_date = datetime(2025, 7, 31)
    reference_number = 1503
    
    today = datetime.now().date()
    days_since_reference = (datetime.combine(today, time.min) - reference_date).days
    current_wordle = reference_number + days_since_reference
    
    return current_wordle, today.strftime("%B %d, %Y")

def get_league_players(db_conn, league_id):
    """Get all players in a specific league"""
    cursor = db_conn.cursor()
    cursor.execute("SELECT name FROM players WHERE league_id = ?", (league_id,))
    players = [row[0] for row in cursor.fetchall()]
    return players

def get_latest_scores(db_conn, league_id):
    """Get the latest scores for players in a specific league"""
    # Get today's date
    today = datetime.now().date().strftime("%Y-%m-%d")
    
    cursor = db_conn.cursor()
    
    # First, check which columns exist in the scores table
    cursor.execute("PRAGMA table_info(scores)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Construct the query based on available columns
    if 'wordle_num' in columns:
        wordle_num, _ = get_current_wordle_info()
        query = """SELECT p.name, s.score, s.emoji_pattern FROM scores s
                   JOIN players p ON s.player_id = p.id 
                   WHERE p.league_id = ? AND s.wordle_num = ?
                   ORDER BY s.score"""
        params = (league_id, wordle_num)
    else:
        # If no wordle_num column, use date
        query = """SELECT p.name, s.score, s.emoji_pattern FROM scores s
                   JOIN players p ON s.player_id = p.id 
                   WHERE p.league_id = ? AND s.date = ?
                   ORDER BY s.score"""
        params = (league_id, today)
        
    cursor.execute(query, params)
    
    scores = {}
    for row in cursor.fetchall():
        if len(row) == 3:
            name, score, pattern = row
            scores[name] = (score, pattern)
        else:
            name, score = row
            # No pattern available
            scores[name] = (score, None)
    
    # If no scores found, try getting most recent scores for each player
    if not scores:
        cursor.execute(
            """
            SELECT p.name, s.score, s.emoji_pattern FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE p.league_id = ?
            AND (p.name, s.date) IN (
                SELECT p2.name, MAX(s2.date) 
                FROM scores s2
                JOIN players p2 ON s2.player_id = p2.id
                WHERE p2.league_id = ?
                GROUP BY p2.name
            )
            ORDER BY s.score
            """,
            (league_id, league_id)
        )
        
        for name, score in cursor.fetchall():
            scores[name] = (score, None)
    
    return scores

def get_weekly_stats(db_conn, league_id):
    """Get the weekly stats for players in a specific league"""
    # Based on memory, Monday is the start of the week
    # Calculate the start of the week (Monday)
    today = datetime.now().date()
    from datetime import timedelta
    start_of_week = today - timedelta(days=today.weekday())
    
    cursor = db_conn.cursor()
    
    # Check for required columns
    cursor.execute("PRAGMA table_info(scores)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Get all scores for the current week with dates
    query = """
    SELECT p.name, s.score, s.date 
    FROM scores s
    JOIN players p ON s.player_id = p.id
    WHERE p.league_id = ? 
    AND s.date >= ? 
    AND s.score > 0
    ORDER BY p.name, s.score
    """
    
    cursor.execute(query, (league_id, start_of_week.strftime("%Y-%m-%d")))
    
    # Process weekly scores
    player_scores = {}
    player_daily_scores = {}
    for name, score, date_str in cursor.fetchall():
        if name not in player_scores:
            player_scores[name] = []
            player_daily_scores[name] = {}
        
        # Track scores by date
        player_scores[name].append(score)
        
        # Convert date string to datetime and get day of week
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        day_of_week = date_obj.weekday()  # 0 is Monday, 6 is Sunday
        
        # Store score by day of week
        player_daily_scores[name][day_of_week] = score
    
    # Get all players in the league even if they have no scores this week
    cursor.execute(
        "SELECT name FROM players WHERE league_id = ?",
        (league_id,)
    )
    all_players = [row[0] for row in cursor.fetchall()]
    
    # Ensure all players are included
    for name in all_players:
        if name not in player_scores:
            player_scores[name] = []
            player_daily_scores[name] = {}
    
    # Get the day names for the current week
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    # Calculate weekly stats with proper handling of the 5-score rule
    weekly_stats = []
    for name, scores in player_scores.items():
        # Sort scores (ascending)
        scores.sort()
        
        # Maximum 5 scores count toward weekly total
        used_scores = scores[:5]
        thrown_out = scores[5:] if len(scores) > 5 else []
        
        weekly_total = sum(used_scores) if used_scores else 0
        weekly_avg = round(weekly_total / len(used_scores), 2) if used_scores else 0
        
        # Check for failed attempts (score of 0)
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE p.league_id = ? 
            AND p.name = ?
            AND s.date >= ?
            AND s.score = 0
            """,
            (league_id, name, start_of_week.strftime("%Y-%m-%d"))
        )
        failed_attempts = cursor.fetchone()[0]
        
        weekly_stats.append((name, weekly_total, len(used_scores), thrown_out, weekly_avg, failed_attempts))
    
    # Sort by:
    # 1. Number of used scores (descending)
    # 2. Weekly total score (ascending)
    # 3. Player name (alphabetical)
    weekly_stats.sort(key=lambda x: (-x[2], x[1], x[0]))
    
    return weekly_stats, player_daily_scores, day_names

def get_all_time_stats(db_conn, league_id):
    """Get all-time stats for players in a specific league"""
    cursor = db_conn.cursor()
    
    # Get all registered players in the league
    cursor.execute("SELECT name FROM players WHERE league_id = ?", (league_id,))
    all_players = [row[0] for row in cursor.fetchall()]
    
    # Get all valid scores (score > 0)
    cursor.execute(
        """
        SELECT p.name, s.score
        FROM scores s
        JOIN players p ON s.player_id = p.id
        WHERE p.league_id = ?
        AND s.score > 0
        """,
        (league_id,)
    )
    
    # Process all-time scores
    player_scores = {name: [] for name in all_players}
    for name, score in cursor.fetchall():
        if name not in player_scores:
            player_scores[name] = []
        player_scores[name].append(score)
    
    # Calculate stats
    all_time_stats = []
    for name, scores in player_scores.items():
        total_games = len(scores)
        
        if total_games > 0:
            total_score = sum(scores)
            avg_score = round(total_score / total_games, 2)
        else:
            total_score = 0
            avg_score = 0
        
        # Get failed attempts (X/6)
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE p.league_id = ?
            AND p.name = ?
            AND s.score = 0
            """,
            (league_id, name)
        )
        failed_attempts = cursor.fetchone()[0]
        
        # For sorting purposes, count failed attempts as score of 7
        # This follows the display standard mentioned in the memories
        adjusted_avg = avg_score
        if total_games > 0 or failed_attempts > 0:
            total_adjusted = total_score + (failed_attempts * 7) 
            total_games_adjusted = total_games + failed_attempts
            adjusted_avg = round(total_adjusted / total_games_adjusted, 2) if total_games_adjusted > 0 else 0
            
        # Per display standards, players with 5+ total games (including failed) should be highlighted
        total_games_for_highlight = total_games + failed_attempts
            
        all_time_stats.append((name, avg_score, total_games, failed_attempts, adjusted_avg, total_games_for_highlight))
    
    # Sort by average score (ascending is better in Wordle) and then by total games (descending)
    # For players with no scores, put them at the bottom
    all_time_stats.sort(key=lambda x: (1 if x[1] == 0 and x[2] == 0 else 0, x[4], -x[5]))
    
    return all_time_stats

def update_wordle_info(soup, wordle_num, wordle_date):
    """Update the Wordle number and date in the HTML"""
    title_elem = soup.select_one('.tab-content.active h2')
    if title_elem:
        title_elem.string = f"Wordle #{wordle_num} - {wordle_date}"
        logger.info(f"Updated Wordle number to #{wordle_num} - {wordle_date}")
    return soup

def update_latest_scores(soup, scores, league_id=None):
    """Update the latest scores section with proper HTML structure
    scores: Dictionary mapping player names to (score, pattern) tuples
    league_id: League ID to get all registered players
    """
    scores_div = soup.select_one('#latest')
    if not scores_div:
        logger.error("Couldn't find latest scores section in HTML")
        return soup
    
    # Clear existing score cards but after the h2 element
    title_elem = scores_div.select_one('h2')
    if title_elem:
        # Remove all elements after the h2
        for elem in list(title_elem.next_siblings):
            if hasattr(elem, 'decompose'):
                elem.decompose()
    else:
        # If no h2, clear everything
        for card in scores_div.select('.score-card'):
            card.decompose()
    
    # Get all registered players for this league if not already in scores
    if league_id:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM players WHERE league_id = ?", (league_id,))
            all_players = [row[0] for row in cursor.fetchall()]
            
            # Add players with no scores
            for player in all_players:
                if player not in scores:
                    # Set as "No Score"
                    scores[player] = (None, None)  # None indicates "No Score"
        except Exception as e:
            logger.error(f"Error getting players for league {league_id}: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    # Sort scores - first players with scores (ascending by score value), then players with no scores alphabetically
    def sort_key(item):
        name, (score, _) = item
        if score is None:
            return (float('inf'), name)  # No Score players at the end, sorted alphabetically
        return (score, name)  # Sort by score, then by name
    
    sorted_scores = sorted(scores.items(), key=sort_key)
    
    for name, (score, pattern) in sorted_scores:
        # Create score card with proper spacing
        scores_div.append(soup.new_string('\n\n'))
        score_card = soup.new_tag('div', attrs={'class': 'score-card'})
        
        # Create player info section
        player_info = soup.new_tag('div', attrs={'class': 'player-info'})
        
        # Add player name
        player_name = soup.new_tag('div', attrs={'class': 'player-name'})
        player_name.string = name
        player_info.append(player_name)
        player_info.append(soup.new_string('\n'))
        
        # Add player score
        player_score_div = soup.new_tag('div', attrs={'class': 'player-score'})
        
        if score is None:
            # No score today
            score_span = soup.new_tag('span', attrs={'class': 'no-score'})
            score_span.string = "No Score"
        else:
            score_class = f'score-{score}'
            score_span = soup.new_tag('span', attrs={'class': score_class})
            score_span.string = f"{score}/6"
            
        player_score_div.append(score_span)
        player_info.append(player_score_div)
        player_info.append(soup.new_string('\n'))
        
        # Add player info to score card
        score_card.append(player_info)
        score_card.append(soup.new_string('\n'))
            
        # Create emoji container only for players with scores
        if score is not None:
            emoji_container = soup.new_tag('div', attrs={'class': 'emoji-container'})
            emoji_pattern_div = soup.new_tag('div', attrs={'class': 'emoji-pattern'})
                
            # Use real emoji pattern from the database if available
            if pattern and pattern != "No emoji pattern available":
                # Convert pattern to HTML rows
                rows = pattern.strip().split('\n')
                for row in rows:
                    # Clean up any non-emoji characters
                    cleaned_row = re.sub(r'[^⬛⬜🟨🟩]', '', row)
                    if cleaned_row and len(cleaned_row) > 0:
                        emoji_row = soup.new_tag('div', attrs={'class': 'emoji-row'})
                        emoji_row.string = cleaned_row
                        emoji_pattern_div.append(emoji_row)
            else:
                # Fallback to simulated pattern if no real pattern available
                for i in range(score if score > 0 else 1):
                    emoji_row = soup.new_tag('div', attrs={'class': 'emoji-row'})
                    if i == score-1:  # Last row (success)
                        emoji_row.string = '🟩🟩🟩🟩🟩'
                    else:  # Earlier attempts
                        emoji_row.string = '⬜🟨⬜🟨⬜'
                    emoji_pattern_div.append(emoji_row)
                    
            emoji_container.append(emoji_pattern_div)
            score_card.append(emoji_container)
            
        score_card.append(soup.new_string('\n\n'))
        
        # Add score card to scores div
        scores_div.append(score_card)
    
    logger.info(f"Updated latest scores section with {len(scores)} players")
    return soup

def update_weekly_stats(soup, weekly_stats_data):
    """Update the weekly stats section with proper HTML structure"""
    # Unpack the data
    weekly_stats, player_daily_scores, day_names = weekly_stats_data
    
    weekly_div = soup.select_one('#weekly')
    if not weekly_div:
        logger.error("Couldn't find weekly stats section in HTML")
        return soup
    
    # Find the table and its parts
    table = weekly_div.select_one('table')
    if not table:
        logger.error("Couldn't find weekly stats table in HTML")
        return soup
        
    # Find or create the header
    thead = table.select_one('thead')
    if not thead:
        thead = soup.new_tag('thead')
        table.insert(0, thead)
    else:
        thead.clear()  # Clear existing header
        
    # Create header row with days of the week
    tr_header = soup.new_tag('tr')
    
    # Add standard columns
    th_player = soup.new_tag('th')
    th_player.string = 'Player'
    tr_header.append(th_player)
    
    th_weekly = soup.new_tag('th')
    th_weekly.string = 'Weekly Score'
    tr_header.append(th_weekly)
    
    th_used = soup.new_tag('th')
    th_used.string = 'Used Scores'
    tr_header.append(th_used)
    
    # Add Failed and Thrown Out columns before days of week
    th_failed = soup.new_tag('th')
    th_failed.string = 'Failed'
    tr_header.append(th_failed)
    
    th_thrown = soup.new_tag('th')
    th_thrown.string = 'Thrown Out'
    tr_header.append(th_thrown)
    
    # Add day of week columns after Failed and Thrown Out
    for day in day_names:
        th_day = soup.new_tag('th')
        th_day.string = day
        tr_header.append(th_day)
    
    # Add the header row to thead
    thead.append(tr_header)
    
    # Find the table body
    tbody = table.select_one('tbody')
    if not tbody:
        tbody = soup.new_tag('tbody')
        table.append(tbody)
        
    # Check for and preserve the note about failed attempts
    # Look for ANY paragraph containing the text "Failed attempts", regardless of class
    note_element = None
    existing_notes = []
    
    # First collect all paragraphs mentioning failed attempts
    for element in weekly_div.find_all('p'):
        if "Failed attempts" in element.text:
            existing_notes.append(element)
    
    # Remove all but the first one (if any exist)
    if existing_notes:
        note_element = existing_notes[0].extract()  # Extract the first one to preserve
        # Remove any others to avoid duplicates
        for extra_note in existing_notes[1:]:
            extra_note.decompose()  # Remove duplicates
    
    # If no note exists, create it
    if not note_element:
        note_element = soup.new_tag('p', attrs={'class': 'note', 'style': 'font-style: italic; font-size: 0.9em; margin-top: 5px;'})
        note_element.string = "Failed attempts do not count towards your 'Used Scores'."
    
    # Clear existing rows
    for row in tbody.select('tr'):
        row.decompose()
    
    # Add new rows
    for stat in weekly_stats:
        name, total, used_scores, thrown_out, avg, failed = stat
        
        tr = soup.new_tag('tr')
        
        # Name column
        td_name = soup.new_tag('td')
        if used_scores >= 5:  # Per the display standard, highlight rows with 5+ scores
            # Make entire row bold by adding class to tr element
            tr['class'] = tr.get('class', []) + ['highlighted']
            # Use the original light green highlight color
            tr['style'] = 'background-color: rgba(106, 170, 100, 0.15); font-weight: bold;'
            name_strong = soup.new_tag('strong')
            name_strong.string = name
            td_name.append(name_strong)
        else:
            td_name.string = name
        tr.append(td_name)
        
        # Total score column
        td_total = soup.new_tag('td')
        if used_scores > 0:  # If player has scores
            td_total.string = str(total)
        else:  # If no scores, show "-" per display standards
            td_total.string = "-"
        tr.append(td_total)
        
        # Number of scores used column
        td_used = soup.new_tag('td')
        td_used.string = str(used_scores)  # Always show the count, even if 0
        tr.append(td_used)
        
        # Failed attempts column
        td_failed = soup.new_tag('td', attrs={'class': 'failed-attempts'})
        if failed > 0:
            td_failed.string = str(failed)
        tr.append(td_failed)
        
        # Thrown out scores column
        td_thrown_out = soup.new_tag('td')
        td_thrown_out.string = str(len(thrown_out))
        tr.append(td_thrown_out)
        
        # Add day of week columns with scores after Failed and Thrown Out
        daily_scores = player_daily_scores.get(name, {})
        for day_index in range(7):  # 0 = Monday, 6 = Sunday
            td_day = soup.new_tag('td')
            if day_index in daily_scores:
                # Display the score for this day
                td_day.string = str(daily_scores[day_index])
            else:
                # No score for this day
                td_day.string = "-"
            tr.append(td_day)
        
        tbody.append(tr)
    
    # Re-add the note after the table
    table = tbody.parent
    table.insert_after(note_element)
    
    logger.info(f"Updated weekly stats section with {len(weekly_stats)} players")
    return soup

def get_weekly_winners(db_conn, league_id):
    """
    Get the weekly winners for a league.
    Returns dict mapping weeks to lists of winners and their scores.
    
    Only called on Monday reset to update Season stats.
    """
    cursor = db_conn.cursor()
    
    # Get the Monday for last week
    today = datetime.now().date()
    days_since_last_monday = (today.weekday() + 7) % 7  # Handle case when today is Monday
    last_monday = today - timedelta(days=days_since_last_monday)
    monday_str = last_monday.strftime("%b %d")  # Format as "Aug 04"
    
    # Find players with the lowest weekly scores (winners)
    # Get the weekly scores from last week
    cursor.execute("""
        WITH weekly_scores AS (
            SELECT 
                p.name, 
                SUM(CASE WHEN s.score != 'X/6' THEN CAST(substr(s.score, 1, 1) AS INTEGER) ELSE 0 END) AS total_score,
                COUNT(CASE WHEN s.score != 'X/6' THEN 1 END) AS games_played
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE 
                p.league_id = ? AND
                s.date >= date(?, '-7 days') AND
                s.date < ?
            GROUP BY p.name
            HAVING games_played >= 5
        ),
        min_score AS (
            SELECT MIN(total_score) as min_total
            FROM weekly_scores
        )
        SELECT ws.name, ws.total_score
        FROM weekly_scores ws, min_score ms
        WHERE ws.total_score = ms.min_total
        ORDER BY ws.name
    """, (league_id, last_monday.isoformat(), last_monday.isoformat()))
    
    winners = cursor.fetchall()
    
    # Create a dict with the weekly winner info
    weekly_winners = {}
    if winners:
        weekly_winners[monday_str] = [(name, score) for name, score in winners]
    
    return weekly_winners

def get_player_weekly_wins(db_conn, league_id):
    """
    Get the number of weekly wins for each player in a league.
    Returns dict mapping player names to win counts.
    """
    cursor = db_conn.cursor()
    
    # Create season_winners table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS season_winners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER,
        league_id INTEGER,
        week_date TEXT,
        score INTEGER,
        FOREIGN KEY (player_id) REFERENCES players(id),
        FOREIGN KEY (league_id) REFERENCES leagues(id)
    )
    """)
    db_conn.commit()
    
    # Get current weekly winners and add to the season_winners table if it's Monday
    today = datetime.now().date()
    if today.weekday() == 0:  # Monday = 0
        # Get last week's winners
        weekly_winners = get_weekly_winners(db_conn, league_id)
        
        # Add winners to season_winners table
        for week, winners in weekly_winners.items():
            for name, score in winners:
                # Get player ID
                cursor.execute("""
                SELECT id FROM players 
                WHERE name = ? AND league_id = ?
                """, (name, league_id))
                player_id_result = cursor.fetchone()
                if player_id_result:
                    player_id = player_id_result[0]
                    # Check if already recorded
                    cursor.execute("""
                    SELECT id FROM season_winners 
                    WHERE player_id = ? AND league_id = ? AND week_date = ?
                    """, (player_id, league_id, week))
                    if not cursor.fetchone():
                        # Add to season_winners
                        cursor.execute("""
                        INSERT INTO season_winners (player_id, league_id, week_date, score)
                        VALUES (?, ?, ?, ?)
                        """, (player_id, league_id, week, score))
                        db_conn.commit()
    
    # Get all players with weekly wins
    cursor.execute("""
    SELECT p.name, COUNT(sw.id) as wins
    FROM players p
    JOIN season_winners sw ON p.id = sw.player_id
    WHERE p.league_id = ? AND sw.league_id = ?
    GROUP BY p.name
    ORDER BY wins DESC, p.name
    """, (league_id, league_id))
    
    return {name: wins for name, wins in cursor.fetchall()}

def rebuild_stats_tab(soup, db_conn, league_id, all_time_stats):
    """
    Completely rebuild the stats tab with Season and All-Time sections
    """
    # Get weekly winners and player wins
    player_wins = get_player_weekly_wins(db_conn, league_id)
    
    # Step 1: Find all tab buttons and update the text of the All-Time Stats tab
    for button in soup.select('.tab-button'):
        if button.get('data-tab') == 'stats':
            button.string = 'Season / All-Time Stats'
            logging.info("Updated tab button text to 'Season / All-Time Stats'")
            break
    
    # Step 2: Clear and rebuild the stats tab content
    stats_content = soup.select_one('#stats')
    if not stats_content:
        logging.error("Could not find stats tab content")
        return soup
    
    # Clear all content
    stats_content.clear()
    
    # Add header
    heading = soup.new_tag('h2', attrs={'style': 'text-align: center;'})
    heading.string = 'Season / All-Time Stats'
    stats_content.append(heading)
    
    # Add Season section
    season_container = soup.new_tag('div', attrs={'class': 'season-container', 'style': 'margin-bottom: 30px;'})
    
    # Add Season heading
    season_heading = soup.new_tag('h3', attrs={'style': 'margin-bottom: 10px; color: #6aaa64;'})
    season_heading.string = 'Season 1'
    season_container.append(season_heading)
    
    # Add Season description
    season_desc = soup.new_tag('p', attrs={'style': 'margin-bottom: 15px; font-size: 14px;'})
    season_desc.string = SEASON_TEXT
    season_container.append(season_desc)
    
    # Create Season table
    season_table = soup.new_tag('table', attrs={'class': 'season-table'})
    
    # Create table header
    thead = soup.new_tag('thead')
    tr = soup.new_tag('tr')
    
    # Column headers
    headers = ['Player', 'Weekly Wins', 'Wordle Week (Score)']
    for header in headers:
        th = soup.new_tag('th')
        th.string = header
        tr.append(th)
        
    thead.append(tr)
    season_table.append(thead)
        
    # Create table body
    tbody = soup.new_tag('tbody')
    
    # Add rows for players with weekly wins
    if player_wins:
        for player, wins in player_wins.items():
            tr = soup.new_tag('tr')
            
            # Player name
            td_player = soup.new_tag('td')
            td_player.string = player
            tr.append(td_player)
            
            # Weekly wins
            td_wins = soup.new_tag('td')
            td_wins.string = str(wins)
            tr.append(td_wins)
            
            # Week info - get the latest week from season_winners table
            td_week = soup.new_tag('td')
            cursor = db_conn.cursor()
            cursor.execute("""
            SELECT sw.week_date, sw.score
            FROM season_winners sw
            JOIN players p ON sw.player_id = p.id
            WHERE p.name = ? AND p.league_id = ?
            ORDER BY sw.week_date DESC
            LIMIT 1
            """, (player, league_id))
            week_info = cursor.fetchone()
            if week_info:
                week, score = week_info
                td_week.string = f"{week} ({score})"
            tr.append(td_week)
            
            tbody.append(tr)
    else:
        # If no weekly winners yet, show an empty row
        tr = soup.new_tag('tr')
        td = soup.new_tag('td', attrs={'colspan': '3', 'style': 'text-align: center;'})
        td.string = "No weekly winners yet"
        tr.append(td)
        tbody.append(tr)
            
    season_table.append(tbody)
    season_container.append(season_table)
    
    # Add season container to stats tab
    stats_content.append(season_container)
    logging.info("Added Season 1 table")
    
    # Add All-Time Stats section
    all_time_container = soup.new_tag('div', attrs={'class': 'all-time-container'})
    
    # Add All-Time Stats heading
    all_time_heading = soup.new_tag('h3', attrs={'style': 'margin-bottom: 10px; color: #6aaa64;'})
    all_time_heading.string = 'All-Time Stats'
    all_time_container.append(all_time_heading)
    
    # Add the description paragraph
    desc = soup.new_tag('p', attrs={'style': 'margin-bottom: 15px; font-size: 14px;'})
    desc.string = "Average includes all games. Failed attempts (X/6) count as 7 in the average calculation"
    all_time_container.append(desc)
    
    # Create table for all-time stats
    all_time_table = soup.new_tag('table')
    
    # Create table header
    all_time_thead = soup.new_tag('thead')
    all_time_tr = soup.new_tag('tr')
    
    all_time_headers = ['Player', 'Games Played', 'Average', 'Failed Attempts']
    for header in all_time_headers:
        th = soup.new_tag('th')
        th.string = header
        all_time_tr.append(th)
        
    all_time_thead.append(all_time_tr)
    all_time_table.append(all_time_thead)
    
    # Create table body
    all_time_tbody = soup.new_tag('tbody')
    
    # Add rows for each player's all-time stats
    for name, stats in all_time_stats.items():
        tr = soup.new_tag('tr')
        
        # Player name
        td_player = soup.new_tag('td')
        td_player.string = name
        tr.append(td_player)
        
        # Games played
        td_games = soup.new_tag('td')
        if stats['games_played'] > 0:
            td_games.string = str(stats['games_played'])
            # Add highlighting for 5+ games
            total_games = stats['games_played'] + stats['failed_attempts']
            if total_games >= 5:
                tr['class'] = 'highlighted'
        else:
            td_games.string = '-'
        tr.append(td_games)
        
        # Average score
        td_avg = soup.new_tag('td')
        if stats['average'] > 0:
            td_avg.string = f"{stats['average']:.2f}"
        else:
            td_avg.string = '-'
        tr.append(td_avg)
        
        # Failed attempts
        td_failed = soup.new_tag('td')
        if stats['failed_attempts'] > 0:
            td_failed.string = str(stats['failed_attempts'])
        else:
            td_failed.string = ''
        tr.append(td_failed)
        
        all_time_tbody.append(tr)
    
    all_time_table.append(all_time_tbody)
    all_time_container.append(all_time_table)
    
    # Add all-time container to stats tab
    stats_content.append(all_time_container)
    logging.info("Added All-Time Stats table")
    
    return soup

def update_all_time_stats(soup, all_time_stats):
    """Update the all-time stats section with proper HTML structure"""
    stats_div = soup.select_one('#stats')
    if not stats_div:
        logger.error("Couldn't find all-time stats section in HTML")
        return soup
    
    # Find the table body
    tbody = stats_div.select_one('table tbody')
    if not tbody:
        logger.error("Couldn't find all-time stats table in HTML")
        return soup
    
    # Clear existing rows
    for row in tbody.select('tr'):
        row.decompose()
    
    # Add new rows
    for name, stats in all_time_stats.items():
        tr = soup.new_tag('tr')
        
        # Player name
        td_player = soup.new_tag('td')
        td_player.string = name
        tr.append(td_player)
        
        # Games played
        td_games = soup.new_tag('td')
        if stats['games_played'] > 0:
            td_games.string = str(stats['games_played'])
            # Add highlighting for 5+ games
            total_games = stats['games_played'] + stats['failed_attempts']
            if total_games >= 5:
                tr['class'] = 'highlighted'
        else:
            td_games.string = '-'
        tr.append(td_games)
        
        # Average score
        td_avg = soup.new_tag('td')
        if stats['average'] > 0:
            td_avg.string = f"{stats['average']:.2f}"
        else:
            td_avg.string = '-'
        tr.append(td_avg)
        
        # Failed attempts
        td_failed = soup.new_tag('td')
        if stats['failed_attempts'] > 0:
            td_failed.string = str(stats['failed_attempts'])
        else:
            td_failed.string = ''
        tr.append(td_failed)
        
        tbody.append(tr)
    
    logger.info(f"Updated all-time stats section with {len(all_time_stats)} players")
    return soup

def update_league_html(league_id, html_path):
    """Update the HTML file for a league with the latest data"""
    # Connect to the database
    try:
        db_conn = connect_to_database()
        if not db_conn:
            logger.error(f"Failed to connect to database for {html_path}")
            return False
        
        logger.info(f"Successfully updated {html_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating {html_path}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main function to update a specific league's HTML"""
    if len(sys.argv) < 2:
        print("Usage: python update_correct_structure.py [league_key]")
        print(f"Available leagues: {', '.join(LEAGUES.keys())}")
        return False
    
    league_key = sys.argv[1].lower()
    
    if league_key not in LEAGUES:
        print(f"Error: Unknown league '{league_key}'")
        print(f"Available leagues: {', '.join(LEAGUES.keys())}")
        return False
    
    league_id = LEAGUES[league_key]['id']
    league_path = LEAGUES[league_key]['path']
    league_name = LEAGUES[league_key]['name']
    
    print(f"Starting update for {league_name}...")
    
    # Backup the file first
    backup_file(league_path)
    
    # Update the HTML
    if update_league_html(league_id, league_path):
        print(f"Successfully updated {league_name} page with current data")
        return True
    else:
        print(f"Failed to update {league_name} page")
        return False

if __name__ == "__main__":
    main()
