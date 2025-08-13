
# Modified by comprehensive_fix.py script on 2025-08-05 15:25:38 to fix landing page generation
# - Ensures exactly 5 leagues are shown without duplicates
# - Fixes player name from Ryan to Kinley in Wordle Party league
#!/usr/bin/env python3
"""
Multi-League Wordle Leaderboard Exporter
This script exports HTML files for multiple leagues based on league_config.json
"""

import os
import sys
import sqlite3
import json
import logging
import jinja2
from datetime import datetime, timedelta
from jinja2 import Template, Environment, FileSystemLoader

# Define paths first
script_dir = os.path.dirname(os.path.abspath(__file__))
default_db_path = os.path.join(script_dir, 'wordle_league.db')
WORDLE_DATABASE = os.getenv('DATABASE_URI', default_db_path).replace('sqlite:///', '')
EXPORT_DIR = os.getenv('EXPORT_DIR', 'website_export')
TEMPLATES_DIR = os.path.join(EXPORT_DIR, 'templates')

# Import from original export script
sys.path.append(script_dir)
from export_leaderboard import (
    calculate_wordle_number,
    get_recent_wordles,
    get_player_stats as get_weekly_stats,  # Use get_player_stats but rename it to match expected function
    export_static_files as get_templates,  # We'll use this to get the templates
    WEBSITE_URL,
    LEADERBOARD_PATH
)

# Import API export function
from export_api_json import export_league_data_to_json

# Define templates for HTML files
# Read templates from standard export script or define our own
try:
    # Try to read the templates from the export directory
    templates_dir = os.path.join(EXPORT_DIR, 'templates')
    if os.path.exists(os.path.join(templates_dir, 'index.html')):
        with open(os.path.join(templates_dir, 'index.html'), 'r', encoding='utf-8') as f:
            index_template = f.read()
        with open(os.path.join(templates_dir, 'wordle.html'), 'r', encoding='utf-8') as f:
            wordle_template = f.read()
    else:
        # Define basic templates if not found
        index_template = """<!DOCTYPE html>
<html>
<head>
    <title>Wordle League</title>
    <meta charset="utf-8">
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <h1>Wordle League</h1>
    <div id="content">
        <h2>Scores for Wordle {{ latest_wordle }}</h2>
        <table>
            <tr>
                <th>Player</th>
                <th>Score</th>
            </tr>
            {% for score in latest_scores %}
            <tr>
                <td>{{ score.name }}</td>
                <td>{{ score.score if score.has_score else '-' }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    <script>
    function scrollToTop() {
        // Use setTimeout to ensure this happens after the link navigation
        setTimeout(function() {
            window.scrollTo(0, 0);
        }, 0);
    }
    </script>
    <div id="back-to-top" style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #538d4e;
        color: white;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        text-align: center;
        line-height: 50px;
        cursor: pointer;
        display: none;
        z-index: 1000;
        font-weight: bold;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    ">↑</div>
    
    <script>
    // Show/hide the back to top button
    window.onscroll = function() {
        var backToTopBtn = document.getElementById("back-to-top");
        if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
            backToTopBtn.style.display = "block";
        } else {
            backToTopBtn.style.display = "none";
        }
    };
    
    // Scroll to top when clicked
    document.getElementById("back-to-top").onclick = function() {
        document.body.scrollTop = 0; // For Safari
        document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
    };
    </script>
</body>
</html>"""
        
        wordle_template = """<!DOCTYPE html>
<html>
<head>
    <title>Wordle {{ wordle_number }} - {{ league_name }}</title>
    <meta charset="utf-8">
    <link rel="stylesheet" href="../styles.css">
</head>
<body>
    <h1>Wordle {{ wordle_number }} - {{ league_name }}</h1>
    <div id="content">
        <h2>Scores for {{ today_formatted }}</h2>
        <table>
            <tr>
                <th>Player</th>
                <th>Score</th>
                <th>Pattern</th>
            </tr>
            {% for score in scores %}
            <tr>
                <td>{{ score.name }}</td>
                <td>{{ score.score if score.has_score else '-' }}</td>
                <td>{{ score.emoji_pattern if score.emoji_pattern else '' }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    <script>
    function scrollToTop() {
        // Use setTimeout to ensure this happens after the link navigation
        setTimeout(function() {
            window.scrollTo(0, 0);
        }, 0);
    }
    </script>
    <div id="back-to-top" style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #538d4e;
        color: white;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        text-align: center;
        line-height: 50px;
        cursor: pointer;
        display: none;
        z-index: 1000;
        font-weight: bold;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    ">↑</div>
    
    <script>
    // Show/hide the back to top button
    window.onscroll = function() {
        var backToTopBtn = document.getElementById("back-to-top");
        if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
            backToTopBtn.style.display = "block";
        } else {
            backToTopBtn.style.display = "none";
        }
    };
    
    // Scroll to top when clicked
    document.getElementById("back-to-top").onclick = function() {
        document.body.scrollTop = 0; // For Safari
        document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
    };
    </script>
</body>
</html>"""

except Exception as e:
    logging.error(f"Error loading templates: {e}")
    # Fall back to basic templates
    index_template = """<!DOCTYPE html><html><body><h1>Wordle League</h1>    <script>
    function scrollToTop() {
        // Use setTimeout to ensure this happens after the link navigation
        setTimeout(function() {
            window.scrollTo(0, 0);
        }, 0);
    }
    </script>
    <div id="back-to-top" style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #538d4e;
        color: white;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        text-align: center;
        line-height: 50px;
        cursor: pointer;
        display: none;
        z-index: 1000;
        font-weight: bold;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    ">↑</div>
    
    <script>
    // Show/hide the back to top button
    window.onscroll = function() {
        var backToTopBtn = document.getElementById("back-to-top");
        if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
            backToTopBtn.style.display = "block";
        } else {
            backToTopBtn.style.display = "none";
        }
    };
    
    // Scroll to top when clicked
    document.getElementById("back-to-top").onclick = function() {
        document.body.scrollTop = 0; // For Safari
        document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
    };
    </script>
</body>
</html>"""
    wordle_template = """<!DOCTYPE html><html><body><h1>Wordle Results</h1>    <script>
    function scrollToTop() {
        // Use setTimeout to ensure this happens after the link navigation
        setTimeout(function() {
            window.scrollTo(0, 0);
        }, 0);
    }
    </script>
    <div id="back-to-top" style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #538d4e;
        color: white;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        text-align: center;
        line-height: 50px;
        cursor: pointer;
        display: none;
        z-index: 1000;
        font-weight: bold;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    ">↑</div>
    
    <script>
    // Show/hide the back to top button
    window.onscroll = function() {
        var backToTopBtn = document.getElementById("back-to-top");
        if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
            backToTopBtn.style.display = "block";
        } else {
            backToTopBtn.style.display = "none";
        }
    };
    
    // Scroll to top when clicked
    document.getElementById("back-to-top").onclick = function() {
        document.body.scrollTop = 0; // For Safari
        document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
    };
    </script>
</body>
</html>"""

# Set up logging
log_file = 'export_multi_league.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Database path
WORDLE_DATABASE = 'wordle_league.db'
EXPORT_DIR = 'website_export'
TEMPLATES_DIR = os.path.join(EXPORT_DIR, 'templates')

def get_league_config():
    """Load league configuration from JSON file"""
    if not os.path.exists('league_config.json'):
        logging.error("league_config.json not found")
        return None
        
    try:
        with open('league_config.json', 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logging.error(f"Error loading league config: {e}")
        return None

def get_players_with_no_scores(league_id):
    """Get all players for a league and mark them as having no scores"""
    conn = None
    players_without_scores = []
    
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # Get all players in this league
        cursor.execute("""
        SELECT p.name, p.nickname 
        FROM players p
        WHERE p.league_id = ?
        """, (league_id,))
        
        results = cursor.fetchall()
        
        for row in results:
            name = row[1] if row[1] else row[0]  # Use nickname if available
            players_without_scores.append({
                'name': name,
                'has_score': False,  # Mark as no score
                'score': 'No Score',  # Show 'No Score' text
                'css_class': 'none',
                'emoji_pattern': None  # No emoji pattern
            })
        
        # Handle special case for Wordle PAL league (ID 3) - ensure "Pants" is included
        if league_id == 3:
            pants_found = False
            for player in players_without_scores:
                if player['name'].lower() == 'pants':
                    pants_found = True
                    break
            
            if not pants_found:
                players_without_scores.append({
                    'name': 'Pants',
                    'has_score': False,
                    'score': 'No Score',
                    'css_class': 'none',
                    'emoji_pattern': None
                })
                logging.info("Added missing player 'Pants' to PAL league display")
        
        return players_without_scores
        
    except Exception as e:
        logging.error(f"Error getting players for league {league_id}: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_scores_for_wordle_by_league(wordle_number, league_id):
    """Get all scores for a specific wordle number and league"""
    conn = None
    scores = []
    
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # Get all scores for this Wordle number for the specified league
        cursor.execute("""
        SELECT p.name, p.nickname, s.score, s.emoji_pattern
        FROM scores s
        JOIN players p ON s.player_id = p.id
        WHERE s.wordle_number = ? AND p.league_id = ?
        ORDER BY s.score
        """, (wordle_number, league_id))
        
        result = cursor.fetchall()
        
        for row in result:
            name = row[1] if row[1] else row[0]  # Use nickname if available
            score = row[2]
            emoji_pattern = row[3]
            
            # Process score for display
            has_score = True
            
            # Handle failed attempts (stored as 7 in DB) for display
            if score == 7 or score == '7':
                score_display = 'X'
                css_class = 'X'
            elif score in ('X', '-', 'None', ''):
                score_display = 'X'
                css_class = 'X'
            else:
                # Regular scores 1-6
                score_display = str(score)
                css_class = str(score)
            
            # Use emoji pattern directly from database or leave blank if not available
            processed_emoji_pattern = emoji_pattern
            
            # Log the emoji pattern to troubleshoot
            logging.info(f"Emoji pattern for {name}, score {score_display}: '{emoji_pattern}'")
            
            # Set to None if the emoji pattern is missing or empty
            if not processed_emoji_pattern or processed_emoji_pattern == 'None' or processed_emoji_pattern == '':
                processed_emoji_pattern = None
            scores.append({
                'name': name,
                'has_score': has_score,
                'score': score_display,
                'css_class': css_class,
                'emoji_pattern': processed_emoji_pattern
            })
            
        # Get all players in this league who don't have a score
        cursor.execute("""
        SELECT p.name, p.nickname 
        FROM players p
        WHERE p.league_id = ? AND p.id NOT IN (
            SELECT s.player_id FROM scores s 
            WHERE s.wordle_number = ?
        )
        """, (league_id, wordle_number))
        
        no_scores = cursor.fetchall()
        for row in no_scores:
            name = row[1] if row[1] else row[0]
            scores.append({
                'name': name,
                'has_score': False,
                'score': 'No Score',  # Show 'No Score' instead of null or X/6
                'emoji_pattern': None
            })
            
        return scores
        
    except Exception as e:
        logging.error(f"Error getting scores for Wordle {wordle_number}, league {league_id}: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_recent_wordles_by_league(league_id, limit=10):
    """Get recent wordles for a specific league"""
    conn = None
    wordles = []
    
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # Get most recent wordle numbers for this league
        cursor.execute("""
        SELECT DISTINCT s.wordle_number, s.timestamp 
        FROM scores s
        JOIN players p ON s.player_id = p.id
        WHERE p.league_id = ?
        ORDER BY s.wordle_number DESC
        LIMIT ?
        """, (league_id, limit))
        
        results = cursor.fetchall()
        
        for row in results:
            wordle_num = row[0]  # Keep variable name for compatibility
            timestamp_str = row[1]
            
            # Properly parse and format the date
            try:
                # Try to parse the timestamp string
                date_obj = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                # Format it as YYYY-MM-DD for consistency
                date = date_obj.strftime('%Y-%m-%d')
            except ValueError as e:
                logging.warning(f"Date parsing error for timestamp '{timestamp_str}': {e}")
                # Extract just the date part if possible
                if ' ' in timestamp_str:
                    date = timestamp_str.split(' ')[0]
                else:
                    # Fallback to current date
                    date = datetime.now().strftime('%Y-%m-%d')
            
            wordles.append({
                'wordle_number': wordle_num,
                'date': date
            })
            
        return wordles
        
    except Exception as e:
        logging.error(f"Error getting recent wordles for league {league_id}: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_weekly_wordle_range():
    """Get the Wordle number range for the current week (Monday-Sunday)"""
    # Get today's Wordle number
    today_wordle = calculate_wordle_number()
    
    # Get today's date and weekday (0 = Monday, 6 = Sunday)
    today = datetime.now()
    weekday = today.weekday()  # 0 = Monday, 6 = Sunday
    
    # Calculate the Wordle number for the start of the week (Monday)
    # If today is Monday (weekday=0), start is today's wordle
    # Otherwise, it's today's wordle minus weekday
    if weekday == 0:  # Monday
        start_wordle = today_wordle
    else:
        start_wordle = today_wordle - weekday
    
    # The end of the week is 6 Wordles after the start (Sunday)
    end_wordle = start_wordle + 6
    
    logging.info(f"Weekly Wordle range: {start_wordle} to {end_wordle}")
    return start_wordle, end_wordle

def get_weekly_stats_by_league(league_id):
    """Get weekly stats for a specific league"""
    # Get league name for logging
    league_name = f'Unknown League {league_id}'
    try:
        # Try to get league name from league_config.json
        with open(os.path.join(script_dir, 'league_config.json'), 'r') as f:
            league_config = json.load(f)
            # Properly access the 'leagues' key in the config
            for league in league_config.get('leagues', []):
                if league.get('league_id') == league_id:
                    league_name = league.get('name', f'League {league_id}')
                    break
    except Exception as e:
        logging.warning(f"Could not get league name: {e}")
    
    # Get the Wordle number range for this week
    start_wordle, end_wordle = get_weekly_wordle_range()

    conn = None
    stats = []
    
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # We already have the Wordle range for this week
        logging.info(f"Getting weekly stats for league {league_id} with Wordle range {start_wordle}-{end_wordle}")
        
        # Get all players registered to this league from the players table
        cursor.execute("""
        SELECT name FROM players 
        WHERE league_id = ?
        """, (league_id,))
        
        registered_players = cursor.fetchall()
        
        # If no players found in players table, fall back to scores table
        if not registered_players:
            cursor.execute("""
            SELECT DISTINCT player_name FROM scores
            WHERE league_id = ?
            """, (league_id,))
            registered_players = cursor.fetchall()
            
        # Check if Pants needs to be added for PAL league
        if league_id == 3 and not any(player[0] == 'Pants' for player in registered_players):
            registered_players.append(('Pants',))
        
        logging.info(f"Found {len(registered_players)} registered players for league {league_id} weekly stats")
        
        for player_row in registered_players:
            name = player_row[0]  # Use player name from players table
            
            # Get this player's scores for the current week using Wordle numbers
            # This ensures we're getting exactly this week's Wordles
            cursor.execute("""
            SELECT DISTINCT s.score, s.timestamp, date(s.timestamp) as score_date
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE p.name = ? AND p.league_id = ? AND s.wordle_number >= ? AND s.wordle_number <= ?
            GROUP BY s.wordle_number  -- Group by Wordle number to avoid duplicates
            ORDER BY s.score
            """, (name, league_id, start_wordle, end_wordle))
            
            # Process the scores we found
            scores_this_week = cursor.fetchall()
            logging.info(f"Player {name} in league {league_id} has {len(scores_this_week)} unique scores this week")
            weekly_scores = []
            
            # Initialize daily scores
            daily_scores = {0: None, 1: None, 2: None, 3: None, 4: None, 5: None, 6: None}  # Monday=0, Sunday=6
            
            for score_row in scores_this_week:
                score = score_row[0]
                timestamp = score_row[1]
                # Extract day of week (0=Monday, 6=Sunday) and store score
                if timestamp:
                    try:
                        # Parse the date and get the weekday (0=Monday, 6=Sunday)
                        dt = datetime.strptime(timestamp[:10], "%Y-%m-%d")
                        weekday = dt.weekday()  # Monday is 0
                        daily_scores[weekday] = score
                        logging.info(f"  Extracted weekday {weekday} with score {score}")
                    except Exception as e:
                        logging.error(f"Error extracting weekday from timestamp {timestamp}: {str(e)}")
                        # Keep daily_score as None for this day
                logging.info(f"Processing for weekly stats: {name} - Score: {score}, Timestamp: {timestamp}, Score Date: {score_row[2] if len(score_row) > 2 else 'Unknown date'}")
                
                # In new schema, score=7 or X indicates failed attempt (X)
                # Failed attempts don't count toward weekly score or used scores total
                if score == 7 or score == '7' or score == 'X' or score in ('-', 'None', '') or not score:
                    # Failed attempt doesn't count for weekly score
                    continue
                else:
                    try:
                        # For regular scores, use the actual score value
                        weekly_scores.append(int(score))
                    except (ValueError, TypeError):
                        # Skip invalid score values
                        logging.warning(f"Skipping invalid score value: {score}")
            
            # Top 5 scores count for weekly total
            weekly_scores.sort()
            top_scores = weekly_scores[:5]
            
            # Calculate weekly stats
            total_weekly = sum(top_scores) if top_scores else None
            used_scores = len(top_scores)
            thrown_out = len(weekly_scores) - used_scores if len(weekly_scores) > 5 else None
            
            # Count failed attempts for the week using Wordle numbers
            cursor.execute("""
            SELECT COUNT(*) FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE p.name = ? AND p.league_id = ? 
            AND s.wordle_number >= ? AND s.wordle_number <= ? 
            AND (s.score = 7 OR s.score = '7' OR s.score = 'X')
            """, (name, league_id, start_wordle, end_wordle))
            failed_count = cursor.fetchone()[0]
            
            # Always add the player's stats, handling special cases
            stats.append({
                'name': name,
                'weekly_score': total_weekly if total_weekly is not None else '-',
                'used_scores': used_scores if used_scores > 0 else 0,
                'failed_attempts': failed_count,  # Ensure this is always a number for later processing
                'failed': failed_count,           # Keep this for consistency
                'weekly_failed': failed_count,    # Add this to match the HTML template
                'thrown_out': thrown_out if thrown_out else '-',
                # Add daily scores
                'monday_score': daily_scores[0],
                'tuesday_score': daily_scores[1],
                'wednesday_score': daily_scores[2],
                'thursday_score': daily_scores[3],
                'friday_score': daily_scores[4],
                'saturday_score': daily_scores[5],
                'sunday_score': daily_scores[6]
            })
        
        # Sort by games played (most first), then by weekly score (lowest first)
        # First make sure all entries have numeric values for sorting
        for stat in stats:
            if stat['weekly_score'] is None or stat['weekly_score'] == '-':
                # Mark as infinity for sorting but will convert to '-' later
                stat['weekly_score'] = float('inf')
            if stat['used_scores'] is None:
                stat['used_scores'] = 0
                
        # Sort by games played (descending) then weekly score (ascending)
        stats.sort(key=lambda x: (
            # First handle None values (put them at the end)
            x['used_scores'] is None or x['weekly_score'] is None,
            # Then sort by games played in descending order (negative for descending)
            -(x['used_scores'] if x['used_scores'] is not None else 0),
            # Then sort by weekly score in ascending order
            x['weekly_score'] if x['weekly_score'] is not None else float('inf'),
            # Finally sort alphabetically by name for equal scores/games
            x['name']
        ))
        
        # Convert 'inf' to '-' but keep all players in the list
        for stat in stats:
            if stat['used_scores'] == 0 or stat['weekly_score'] == float('inf'):
                stat['weekly_score'] = '-'
                
        # No longer filtering players - keep all players in the weekly stats
        
        logging.info(f"DEBUG: Weekly stats for {league_id}: {len(stats)} items")
        if stats:
            logging.info(f"DEBUG: First weekly stat item: {stats[0]}")
        
        return stats
    
    except Exception as e:
        logging.error(f"Error getting weekly stats for league {league_id}: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_all_time_stats_by_league(league_id):
    """Get all-time statistics for a specific league, including all historical scores"""
    conn = None
    stats = []
    
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        logging.info(f"Getting all-time stats for league {league_id}")
        
        # Get all players registered to this league from the players table
        cursor.execute("""
        SELECT name FROM players 
        WHERE league_id = ?
        """, (league_id,))
        
        registered_players = cursor.fetchall()
        
        # If no players found in players table, fall back to scores table
        if not registered_players:
            cursor.execute("""
            SELECT DISTINCT player_name FROM scores
            WHERE league_id = ?
            """, (league_id,))
            registered_players = cursor.fetchall()
        
        logging.info(f"Found {len(registered_players)} registered players for league {league_id} all-time stats")
        
        for player_row in registered_players:
            name = player_row[0]  # Use player name from players or scores table
            
            # Get all of this player's scores
            # Include ALL scores for all-time stats
            cursor.execute("""
            SELECT DISTINCT s.score, s.timestamp, date(s.timestamp) as score_date 
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE p.name = ? AND p.league_id = ?
            GROUP BY date(s.timestamp)  -- Only count one score per day
            """, (name, league_id))
            
            scores = cursor.fetchall()
            
            # Initialize statistics variables
            all_scores = []
            all_score_values = []
            # Initialize counters for score distribution
            ones = twos = threes = fours = fives = sixes = 0
            numeric_scores = []
            valid_scores = []
            total_games = 0
            avg_score = None
            all_time_avg = None
            
            # Process scores
            if scores:
                # Calculate statistics
                all_scores = [score[0] for score in scores]
                
                # Filter out failed attempts (7 or 'X') and other invalid scores for score calculation
                valid_scores = [score for score in all_scores if score not in (7, '7', 'X', '-', 'None', '') and score is not None]
                
                # Keep all scores for counting purposes
                total_games = len(all_scores)
                
                # Count different score types
                ones = sum(1 for score in valid_scores if score == 1)
                twos = sum(1 for score in valid_scores if score == 2)
                threes = sum(1 for score in valid_scores if score == 3)
                fours = sum(1 for score in valid_scores if score == 4)
                fives = sum(1 for score in valid_scores if score == 5)
                sixes = sum(1 for score in valid_scores if score == 6)
                
                # Calculate average score (handling failed attempts as 7)
                numeric_scores = []
                for s in all_scores:
                    if s == 7 or s == '7' or s == 'X':
                        numeric_scores.append(7)  # Failed attempt counts as 7
                    elif s not in ('-', 'None', '') and s is not None:
                        try:
                            numeric_scores.append(int(s))
                        except (ValueError, TypeError):
                            pass  # Skip non-numeric values
                            
                avg_score = sum(numeric_scores) / len(numeric_scores) if numeric_scores else None
                
                # Calculate all-time average (including historical data if any)
                all_time_avg = avg_score  # For now, just use current period's average
            
            # Calculate failed attempts (score=7 or score='X')
            failed_count = sum(1 for score in all_scores if score == 7 or score == '7' or score == 'X')
            
            # Calculate total games (games played + failed attempts) for display
            if all_scores and total_games > 0 and valid_scores:
                display_games = total_games
                display_total_games = total_games + failed_count
            else:
                display_games = '-'
                display_total_games = '-'
                
            # Build stats object for this player
            # If player only has failed attempts but no valid scores
            if failed_count > 0 and not valid_scores:
                stats.append({
                    'name': name,
                    'games_played': 0,          # No valid games played
                    'total_games': failed_count, # Only failed attempts
                    'average': '-',             # No average for failed-only
                    'all_time_average': '-',    # No all-time average
                    'failed_attempts': failed_count,
                    'failed': failed_count,     # For backward compatibility
                })
            else:
                stats.append({
                    'name': name,
                    'games_played': len(valid_scores) if valid_scores else '-',
                    'total_games': total_games if total_games > 0 else '-',
                    'average': round(avg_score, 2) if avg_score else '-',
                    'all_time_average': round(all_time_avg, 2) if all_time_avg else '-',
                    'failed_attempts': failed_count if 'failed_count' in locals() else 0,
                    'failed': failed_count if 'failed_count' in locals() else 0,  # For backward compatibility
                    'ones': ones,
                    'twos': twos,
                    'threes': threes,
                    'fours': fours,
                    'fives': fives,
                    'sixes': sixes
                })
        
        # Sort by average score (lower is better), placing '-' values at the end
        def sort_key(x):
            # Put players with no average at the end, otherwise sort by average
            if x['average'] == '-':
                return float('inf')
            return x['average']
            
        stats.sort(key=sort_key)
        
        return stats
        
    except Exception as e:
        logging.error(f"Error getting all-time stats for league {league_id}: {e}")
        return []
    finally:
        if conn:
            conn.close()

def export_league_files(league):
    # Global variables for template rendering
    global html_template, wordle_template  # Store templates once loaded
    from jinja2 import Environment, StrictUndefined
    """Export HTML files for a specific league"""
    league_id = league['league_id']
    league_name = league['name']
    export_path = league.get('html_export_path', '')
    
    # Determine the export directory
    if league.get('is_default', False):
        # Default league goes to the main directory
        league_dir = EXPORT_DIR
    else:
        # Other leagues go to subdirectories
        league_dir = os.path.join(EXPORT_DIR, export_path)
        
    # Create league directory if it doesn't exist
    if not os.path.exists(league_dir):
        os.makedirs(league_dir)
    
    # Get today's Wordle number
    today_wordle = calculate_wordle_number()
    
    # Try to find the most recent Wordle with scores for this league
    conn = sqlite3.connect(WORDLE_DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT MAX(wordle_number) as latest_wordle
    FROM scores s
    JOIN players p ON s.player_id = p.id
    WHERE p.league_id = ?
    """, (league_id,))
    
    result = cursor.fetchone()
    if result and result[0]:
        latest_league_wordle = int(result[0])
        logging.info(f"Latest Wordle with scores for league {league_id}: {latest_league_wordle}")
    else:
        latest_league_wordle = None
        logging.info(f"No scores found for league {league_id}")
    
    # Check if the latest Wordle with scores is actually today's Wordle
    if latest_league_wordle == today_wordle:
        # If we have scores for today, show them
        logging.info(f"Found scores for today's Wordle {today_wordle} for league {league_id}")
        latest_scores = get_scores_for_wordle_by_league(today_wordle, league_id)
    else:
        # If the latest scores are NOT from today's Wordle, show empty scores for today
        logging.info(f"No scores yet for today's Wordle {today_wordle} for league {league_id}")
        # Get all players for this league but mark them as having no score
        latest_scores = get_players_with_no_scores(league_id)
    
    # Get recent wordles for this league
    recent_wordles = get_recent_wordles_by_league(league_id)
    
    # Get weekly and all-time stats for this league
    weekly_stats = get_weekly_stats_by_league(league_id)
    all_time_stats = get_all_time_stats_by_league(league_id)
    
    # Format today's date
    today = datetime.now()
    today_formatted = today.strftime("%B %d, %Y")
    
    # Generate index.html for this league
    try:
        # Get the HTML template file
        loader = jinja2.FileSystemLoader('./')
        env = jinja2.Environment(loader=loader)
        
        # Add custom filters
        def format_value(value):
            if value is None or value == float('inf'):
                return '-'
            return value
            
        def safe_int(value):
            """Safely convert a value to an integer for template use"""
            if isinstance(value, (int, float)):
                return int(value)
            if value == '-' or value is None:
                return 0
            try:
                return int(value)
            except (ValueError, TypeError):
                return 0
                
        # Add filters to environment
        env.filters['format_value'] = format_value
        env.filters['safe_int'] = safe_int
        
        # Add string conversion filter
        def to_str(value):
            if value is None:
                return ''
            return str(value)
            
        # Add integer conversion filter that's safer for templates
        def to_int(value):
            if value is None or value == '-' or value == '':
                return 0
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return 0
        
        # Add a safe join filter that can handle any type of input
        def safe_join(value, d=''):
            if value is None:
                return ''
            if isinstance(value, (int, float)):
                return str(value)  # If it's a single number, just return it as string
            try:
                # Try to join as normal
                return str(d).join(map(str, value))
            except TypeError:
                # If it's not iterable, just return as string
                return str(value)
                
        env.filters['to_str'] = to_str
        env.filters['to_int'] = to_int
        env.filters['safe_join'] = safe_join
        
        # Override the default join filter to use our safe_join
        env.filters['join'] = safe_join
        
        with open(os.path.join(league_dir, 'index.html'), 'w', encoding='utf-8') as f:
            # Use environment instead of direct Template to get access to our custom filters
            env.globals.update({
                'str': str,  # Make str function available in templates
                'int': int   # Make int function available in templates
            })
            template = env.from_string(index_template)
            
            # Update title to include league name if not default
            title = f"Wordle {league_name} League" if not league.get('is_default', False) else "Wordle League"
            
            # Debug code to print stats
            logging.info(f"DEBUG: Weekly stats for {league_name}: {len(weekly_stats)} items")
            if weekly_stats:
                logging.info(f"DEBUG: First weekly stat item: {weekly_stats[0]}")
                # Check if 'failed_attempts' attribute exists
                if 'failed_attempts' not in weekly_stats[0]:
                    logging.error(f"DEBUG: 'failed_attempts' missing, found these keys: {list(weekly_stats[0].keys())}")
                    
                    # Add the missing attribute to each stats item
                    for stat in weekly_stats:
                        stat['failed_attempts'] = stat['failed']
                
                # Process failed attempts for display in HTML
                logging.info(f"Pre-processing weekly stats for {league_name}")
                
                # CRITICAL FIX: Direct string conversion for failed attempts to ensure proper HTML display
                # This ensures that numeric values are properly converted to strings for the HTML template
                for stat in weekly_stats:
                    # Always explicitly convert all failed_attempts values
                    if isinstance(stat.get('failed', 0), (int, float)) and stat['failed'] > 0:
                        # Store as string for display
                        stat['failed_attempts'] = str(stat['failed'])
                        logging.info(f"Set failed_attempts for {stat['name']} to '{stat['failed_attempts']}'")
                    else:
                        # If no failed attempts, set to empty string for HTML display
                        stat['failed_attempts'] = ''
                
                # Debug verification
                for stat in weekly_stats:
                    if stat.get('name') == 'Evan':
                        logging.info(f"VERIFICATION - Evan's weekly stats: {stat}")
                
                logging.info(f"Finished processing failed attempts for {league_name}")
                # End of failed attempts processing
            
            # Debug the all-time stats to ensure we have averages
            logging.info(f"DEBUG: All-time stats for {league_name}: {len(all_time_stats)} items")
            if all_time_stats:
                logging.info(f"DEBUG: First all-time stat item: {all_time_stats[0]}")
                # Format the averages to 2 decimal places for display
                for stat in all_time_stats:
                    if 'average' in stat:
                        # Format the average to 2 decimal places if it's a number, otherwise keep as is
                        if isinstance(stat['average'], (int, float)):
                            formatted_avg = f"{stat['average']:.2f}"
                        else:
                            # If it's already a string (like "-"), use as is
                            formatted_avg = stat['average']
                            
                        # Set all possible format keys for templates
                        stat['avg'] = formatted_avg
                        stat['average_display'] = formatted_avg
                        stat['average_score'] = formatted_avg
                        # This is what the template is actually looking for
                        stat['all_time_average'] = formatted_avg
            
            # Define a function to sanitize all data for templates
            def sanitize_template_data(data):
                """Ensure all data is properly formatted for template rendering"""
                # Special handling for numeric comparison values
                # For stats - keep certain keys as numbers for template comparison operations
                numeric_keys = ['games_played', 'used_scores', 'total_games', 'weekly_score']
                
                # Handle dictionaries with special care for numeric values
                if isinstance(data, dict):
                    for key, value in data.items():
                        # Keep certain keys as integers for comparison operations
                        if key in numeric_keys:
                            if isinstance(value, str) and value.isdigit():
                                data[key] = int(value)
                            elif value == '-' or value is None:
                                data[key] = 0
                            # Leave actual numbers as is
                        else:
                            # For non-numeric keys, sanitize recursively
                            data[key] = sanitize_template_data(value)
                    return data
                
                # Handle lists
                if isinstance(data, list):
                    return [sanitize_template_data(item) for item in data]
                
                # Ensure None values are treated as empty strings
                if data is None:
                    return ''
                
                # Convert numbers to strings for display only (not for comparison)
                if isinstance(data, (int, float)) and not any(k in str(data) for k in numeric_keys):
                    return str(data)
                    
                # Return other types as is
                return data
                
            try:
                # Sanitize player data for template rendering to avoid type errors
                for player in all_time_stats:
                    # Ensure games_played and failed_attempts are consistent types
                    if player.get('games_played') == '-':
                        player['games_played'] = 0
                        
                    # Convert all numeric values to appropriate types
                    player['games_played'] = int(player['games_played']) if not isinstance(player['games_played'], str) else 0
                    player['failed_attempts'] = int(player.get('failed_attempts', 0)) if not isinstance(player.get('failed_attempts'), str) else 0
                
                # Make sure all numeric fields that might be used in calculations are integers
                for player in all_time_stats:
                    for field in ['ones', 'twos', 'threes', 'fours', 'fives', 'sixes', 'failed_attempts']:
                        if field in player:
                            try:
                                player[field] = int(player[field]) if player[field] not in [None, '-', ''] else 0
                            except (ValueError, TypeError):
                                player[field] = 0
                
                for player in weekly_stats:
                    for field in ['weekly_score', 'used_scores', 'failed_attempts', 'thrown_out']:
                        if field in player:
                            try:
                                player[field] = int(player[field]) if player[field] not in [None, '-', ''] else 0
                            except (ValueError, TypeError):
                                player[field] = 0
                
                # Add test data for season winners (we'll implement real calculation tomorrow)
                # This is just for UI testing
                test_season_winners = [
                    {
                        'name': 'Brent',
                        'weekly_wins': 1,  # Both players tied with 1 win
                        'winning_weeks': ['Aug 4th (14)']
                    },
                    {
                        'name': 'Malia',
                        'weekly_wins': 1,
                        'winning_weeks': ['Aug 4th (14)']
                    }
                    # Removing Joanna who had 0 weekly wins
                ]
                
                # Sanitize all data before sending to template
                template_data = {
                    'latest_wordle': today_wordle,
                    'latest_scores': latest_scores or [],  # Ensure it's a list
                    'recent_wordles': recent_wordles or [],  # Ensure it's a list
                    'player_stats': weekly_stats or [],  # Ensure it's a list
                    'all_time_stats': all_time_stats or [],  # Ensure it's a list
                    'season_winners': test_season_winners,  # Add test data for season winners
                    'today_formatted': today_formatted or '',
                    'title': title or '',
                    'league_name': league_name or ''
                }
                
                # Render template with sanitized data
                try:
                    # First attempt regular rendering
                    html_content = template.render(**template_data)
                except Exception as e:
                    logging.error(f"ERROR IN TEMPLATE RENDERING: {e}")
                    # Debug the exact error location
                    import traceback
                    logging.error(traceback.format_exc())
                    
                    # Plan B: Use a very simple fallback template if the main one fails
                    logging.info(f"Using fallback template for {league_name} (ID: {league_id})")
                    fallback_template = """
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <title>{{ title }}</title>
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                        <link rel="stylesheet" href="../styles.css">
                    </head>
                    <body>
                        <div class="container">
                            <h1>{{ league_name }} - Wordle League</h1>
                            <p>Latest Wordle: {{ latest_wordle }}</p>
                            <h2>Weekly Stats</h2>
                            <table class="leaderboard">
                                <thead>
                                    <tr>
                                        <th>Player</th>
                                        <th>Weekly Score</th>
                                    </tr>
                                </thead>
                                <tbody>
                                {% for player in player_stats %}
                                    <tr>
                                        <td>{{ player.name }}</td>
                                        <td>{{ player.weekly_score }}</td>
                                    </tr>
                                {% endfor %}
                                </tbody>
                            </table>
                            
                            <h2>All-Time Stats</h2>
                            <table class="leaderboard">
                                <thead>
                                    <tr>
                                        <th>Player</th>
                                        <th>Games Played</th>
                                        <th>Average</th>
                                    </tr>
                                </thead>
                                <tbody>
                                {% for player in all_time_stats %}
                                    <tr>
                                        <td>{{ player.name }}</td>
                                        <td>{{ player.games_played }}</td>
                                        <td>{{ player.all_time_average }}</td>
                                    </tr>
                                {% endfor %}
                                </tbody>
                            </table>
                            
                            <h2>Recent Games</h2>
                            <ul class="wordle-list">
                            {% for wordle in recent_wordles %}
                                <li><a href="wordles/{{ wordle }}.html">Wordle {{ wordle }}</a></li>
                            {% endfor %}
                            </ul>
                        </div>
                        <!-- No JavaScript needed for fallback template -->
                    </body>
                    </html>
                    """
                    
                    # Use the fallback template with minimal data
                    fallback_env = Environment(undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
                    fallback_template = fallback_env.from_string(fallback_template)
                    
                    try:
                        # Ensure the most basic data is strings to avoid further errors
                        basic_data = {
                            'latest_wordle': str(template_data.get('latest_wordle', '')),
                            'league_name': str(template_data.get('league_name', '')),
                            'title': str(template_data.get('title', '')),
                            'player_stats': [],
                            'all_time_stats': [],
                            'recent_wordles': []
                        }
                        
                        # Add simple player stats if available
                        if template_data.get('player_stats'):
                            for player in template_data['player_stats']:
                                try:
                                    basic_data['player_stats'].append({
                                        'name': str(player.get('name', '')),
                                        'weekly_score': str(player.get('weekly_score', '0'))
                                    })
                                except:
                                    pass
                                    
                        # Add simple all-time stats if available
                        if template_data.get('all_time_stats'):
                            for player in template_data['all_time_stats']:
                                try:
                                    basic_data['all_time_stats'].append({
                                        'name': str(player.get('name', '')),
                                        'games_played': str(player.get('games_played', '0')),
                                        'all_time_average': str(player.get('all_time_average', '0'))
                                    })
                                except:
                                    pass
                        
                        # Add recent wordles if available
                        if template_data.get('recent_wordles'):
                            for wordle in template_data['recent_wordles']:
                                try:
                                    basic_data['recent_wordles'].append(str(wordle))
                                except:
                                    pass
                        
                        html_content = fallback_template.render(**basic_data)
                        logging.info(f"Successfully rendered fallback template for {league_name} (ID: {league_id})")
                    except Exception as inner_e:
                        logging.error(f"FALLBACK TEMPLATE ALSO FAILED: {inner_e}")
                        # Last resort - generate very basic HTML
                        html_content = f"""
                        <!DOCTYPE html>
                        <html>
                        <head><title>{league_name} - Wordle League</title></head>
                        <body>
                            <h1>{league_name} - Wordle League</h1>
                            <p>Sorry, there was an issue generating this page. Please check back later.</p>
                        </body>
                        </html>
                        """
            except Exception as e:
                logging.error(f"UNHANDLED ERROR: {e}")
                raise Exception(f"Error exporting index.html for league {league_name} (ID: {league_id}): {e}") from e
            
            # Fix CSS path for non-default leagues
            if not league.get('is_default', False):
                html_content = html_content.replace('href="styles.css"', 'href="../styles.css"')
                html_content = html_content.replace('src="script.js"', 'src="../script.js"')
            
            f.write(html_content)
    except Exception as e:
        logging.error(f"Error exporting index.html for league {league_name} (ID: {league_id}): {e}")
    
    logging.info(f"Exported index.html for league {league_name} (ID: {league_id})")
    
    # Create daily directory for this league if it doesn't exist
    daily_dir = os.path.join(league_dir, 'daily')
    if not os.path.exists(daily_dir):
        os.makedirs(daily_dir)
    
    # Generate individual wordle pages for recent wordles
    for wordle in recent_wordles:
        wordle_number = wordle['wordle_number']
        scores = get_scores_for_wordle_by_league(wordle_number, league_id)
        
        # Get the date for this wordle
        wordle_date = datetime.strptime(wordle['date'], '%Y-%m-%d')
        wordle_date_formatted = wordle_date.strftime("%B %d, %Y")
        
        # Save to the daily folder
        with open(os.path.join(daily_dir, f'wordle-{wordle_number}.html'), 'w', encoding='utf-8') as f:
            # Create a template with the same filters
            loader = jinja2.FileSystemLoader('./')
            env = jinja2.Environment(loader=loader)
            
            # Add custom filters
            def format_value(value):
                if value is None or value == float('inf'):
                    return '-'
                return value
                
            def safe_int(value):
                """Safely convert a value to an integer for template use"""
                if isinstance(value, (int, float)):
                    return int(value)
                if value == '-' or value is None:
                    return 0
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return 0
            
            # Add filters to environment
            env.filters['format_value'] = format_value
            env.filters['safe_int'] = safe_int
            
            # Add global functions
            env.globals.update({
                'str': str,  # Make str function available in templates
                'int': int   # Make int function available in templates
            })
            
            # Use environment for template rendering
            template = env.from_string(wordle_template)
            
            # Make sure all numeric fields that might be used in calculations are integers
            for player in all_time_stats:
                for field in ['ones', 'twos', 'threes', 'fours', 'fives', 'sixes', 'failed_attempts', 'games_played']:
                    if field in player:
                        try:
                            player[field] = int(player[field]) if player[field] not in [None, '-', ''] else 0
                        except (ValueError, TypeError):
                            player[field] = 0
            
            for player in weekly_stats:
                for field in ['weekly_score', 'used_scores', 'failed_attempts', 'thrown_out']:
                    if field in player:
                        try:
                            player[field] = int(player[field]) if player[field] not in [None, '-', ''] else 0
                        except (ValueError, TypeError):
                            player[field] = 0
                            
            # For scores, ensure all score values are integers
            for score_entry in scores:
                if 'score' in score_entry:
                    try:
                        # Convert X to 7 for failed attempts
                        if score_entry['score'] == 'X':
                            score_entry['score'] = 7
                        else:
                            score_entry['score'] = int(score_entry['score']) if score_entry['score'] not in [None, '-', ''] else 0
                    except (ValueError, TypeError):
                        score_entry['score'] = 0
            
            # Sanitize all data before sending to template
            template_data = {
                'wordle_number': wordle_number,
                'scores': scores or [],  # Ensure it's a list
                'recent_wordles': recent_wordles or [],  # Ensure it's a list
                'today_formatted': wordle_date_formatted or '',
                'player_stats': weekly_stats or [],  # Ensure it's a list
                'all_time_stats': all_time_stats or [],  # Ensure it's a list
                'title': title or '',
                'league_name': league_name or ''
            }
            
            # Render template with sanitized data
            html_content = template.render(**template_data)
            
            # Write the rendered content to file
            f.write(html_content)
            
    # Create API directory if it doesn't exist
    api_dir = os.path.join(league_dir, 'api')
    if not os.path.exists(api_dir):
        os.makedirs(api_dir)
        
    # Export weekly stats as JSON
    with open(os.path.join(api_dir, 'weekly_stats.json'), 'w', encoding='utf-8') as f:
        json.dump(weekly_stats, f)
        
    # Export all-time stats as JSON
    with open(os.path.join(api_dir, 'all_time_stats.json'), 'w', encoding='utf-8') as f:
        json.dump(all_time_stats, f)
    
    logging.info(f"Exported all files for league {league_name} (ID: {league_id})")
    
    # Return whether we had any scores
    has_scores = len(latest_scores) > 0 and any(score['has_score'] for score in latest_scores)
    return has_scores

def export_all_leagues():
    """Export HTML files for all leagues"""
    config = get_league_config()
    if not config:
        logging.error("Failed to load league configuration")
        return False
    
    results = {}
    
    # Process each league
    for league in config['leagues']:
        league_id = league['league_id']
        league_name = league['name']
        
        # Skip disabled leagues
        if not league.get('enabled', True):
            logging.info(f"Skipping disabled league: {league_name} (ID: {league_id})")
            continue
        
        logging.info(f"Processing league: {league_name} (ID: {league_id})")
        has_scores = export_league_files(league)
        results[league_name] = has_scores
    
    # Generate landing page with links to all leagues
    generate_landing_page(config['leagues'], results)
    
    # Export all league data to JSON files for API
    try:
        if export_league_data_to_json(db_path=WORDLE_DATABASE, export_dir=EXPORT_DIR):
            logging.info("Successfully exported league data to JSON API files")
        else:
            logging.error("Failed to export league data to JSON API files")
    except Exception as e:
        logging.error(f"Error exporting league data to JSON API: {e}")
    
    return True

def generate_landing_page(leagues, results):
    """Generate a landing page with links to all leagues"""
    try:
        # Read the current landing.html file
        landing_file = os.path.join(EXPORT_DIR, 'landing.html')
        if os.path.exists(landing_file):
            try:
                # Try UTF-8 first
                with open(landing_file, 'r', encoding='utf-8') as f:
                    landing_content = f.read()
            except UnicodeDecodeError:
                try:
                    # Try with UTF-16 if UTF-8 fails
                    with open(landing_file, 'r', encoding='utf-16') as f:
                        landing_content = f.read()
                except UnicodeDecodeError:
                    # If both fail, create a new file
                    logging.warning(f"Landing page encoding issues detected. Creating new landing.html file.")
                    landing_content = None
        else:
            landing_content = None
            
        # If couldn't read or doesn't exist, use default template
        if landing_content is None:
            # Create a basic landing page template
            landing_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wordle Leagues</title>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <link rel="stylesheet" href="styles.css">
    <style>
        body {
            font-family: 'Clear Sans', 'Helvetica Neue', Arial, sans-serif;
            background-color: #121213;
            color: #d7dadc;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }
        
        .container {
            width: 100%;
            max-width: 500px;
            margin: 0 auto;
            padding: 10px;
        }
        
        header {
            text-align: center;
            padding: 10px 0;
            border-bottom: 1px solid #3a3a3c;
        }
        
        .title {
            font-weight: 700;
            font-size: 36px;
            letter-spacing: 0.2rem;
            text-transform: uppercase;
            margin-top: 0;
            margin-bottom: 10px;
        }
        
        .league-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
            margin-top: 20px;
        }
        
        .league-card {
            background-color: #1a1a1b;
            border-radius: 5px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            text-align: center;
        }
        
        .league-name {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #6aaa64;
        }
        
        .league-description {
            margin-bottom: 20px;
            color: #d7dadc;
        }
        
        .league-status {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 15px;
        }
        
        .status-active {
            background-color: rgba(106, 170, 100, 0.2);
            color: #6aaa64;
        }
        
        .status-inactive {
            background-color: rgba(120, 124, 126, 0.2);
            color: #787c7e;
        }
        
        .league-button {
            display: inline-block;
            padding: 10px 20px;
            background-color: #538d4e;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-weight: bold;
            transition: background-color 0.2s;
        }
        
        .league-button:hover {
            background-color: #6aaa64;
        }
        
        @media (min-width: 768px) {
            .league-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        @media (min-width: 1200px) {
            .league-grid {
                grid-template-columns: repeat(3, 1fr);
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1 class="title">Wordle Leagues</h1>
            <p>Select a league to view scores and leaderboards</p>
        </div>
    </header>
    
    <div class="container">
        <div class="league-grid">
            <!-- League cards will be generated here -->
        </div>
    </div>
    <script>
    function scrollToTop() {
        // Use setTimeout to ensure this happens after the link navigation
        setTimeout(function() {
            window.scrollTo(0, 0);
        }, 0);
    }
    </script>
    <div id="back-to-top" style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #538d4e;
        color: white;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        text-align: center;
        line-height: 50px;
        cursor: pointer;
        display: none;
        z-index: 1000;
        font-weight: bold;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    ">↑</div>
    
    <script>
    // Show/hide the back to top button
    window.onscroll = function() {
        var backToTopBtn = document.getElementById("back-to-top");
        if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
            backToTopBtn.style.display = "block";
        } else {
            backToTopBtn.style.display = "none";
        }
    };
    
    // Scroll to top when clicked
    document.getElementById("back-to-top").onclick = function() {
        document.body.scrollTop = 0; // For Safari
        document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
    };
    </script>
</body>
</html>"""
        
        # Format today's date for display
        today = datetime.now()
        today_formatted = today.strftime("%B %d, %Y")
        
        # Generate the league cards HTML
        league_cards_html = ""
        for league in leagues:
            if not league.get('enabled', True):
                continue
                
            league_name = league['name']
            league_desc = league.get('description', f"{league_name} League")
            league_path = '' if league.get('is_default', False) else league.get('html_export_path', '')
            
            # Determine league status based on results
            has_scores = results.get(league_name, False)
            status_class = "status-active" if has_scores else "status-inactive"
            status_text = "Active" if has_scores else "No scores yet"
            
            # Create the league card HTML
            card_html = f"""
            <div class="league-card">
                <div class="league-name">{league_name}</div>
                <div class="league-description">{league_desc}</div>
                <div class="league-status {status_class}">{status_text}</div>
                <a href="{league_path}/index.html" class="league-button" onclick="scrollToTop()">View League</a>
            </div>
            """
            
            league_cards_html += card_html
            
        # Insert league cards into the landing page
        if "<!-- League cards will be generated here -->" in landing_content:
            landing_content = landing_content.replace(
                "<!-- League cards will be generated here -->",
                league_cards_html
            )
        
        # Update the date if applicable
        landing_content = landing_content.replace("{{today_date}}", today_formatted)
        
        # Write the updated landing page
        with open(landing_file, 'w', encoding='utf-8') as f:
            f.write(landing_content)
            
        logging.info("Updated landing page with league links")
        
    except Exception as e:
        logging.error(f"Error generating landing page: {e}")

def main():
    """Main function"""
    logging.info("Starting multi-league leaderboard export")
    
    # Make sure the export directory exists
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)
    
    # Add debug code to print stats objects
    try:
        # Test with a sample league to see exactly what fails
        league_id = 1  # Wordle Warriorz
        logging.info(f"DEBUG: Testing weekly stats for league {league_id}")
        weekly_stats = get_weekly_stats_by_league(league_id)
        logging.info(f"DEBUG: Got {len(weekly_stats)} weekly stats")
        if weekly_stats:
            # Log the first stats object
            logging.info(f"DEBUG: First weekly stats object: {weekly_stats[0]}")
    except Exception as e:
        logging.error(f"DEBUG: Error in test code: {e}")
    
    # Export files for all leagues
    try:
        if export_all_leagues():
            # Generate week pages for the clickable links
            def generate_week_pages():
                logging.info("Generating week pages")
                
                # Create weeks directory if it doesn't exist
                weeks_dir = os.path.join("website_export", "weeks")
                if not os.path.exists(weeks_dir):
                    os.makedirs(weeks_dir)
                
                # Get the week template
                env = Environment(loader=FileSystemLoader("website_export/templates"))
                template = env.get_template("week.html")
                
                # For now, just generate test data for Aug 4th week
                week_data = {
                    'aug-4th-(14)': {
                        'title': 'Wordle League - Week of August 4, 2025',
                        'week_title': 'August 4, 2025',
                        'wordle_games': [
                            {'number': '1,507', 'date': 'August 4, 2025'},
                            {'number': '1,508', 'date': 'August 5, 2025'},
                            {'number': '1,509', 'date': 'August 6, 2025'},
                            {'number': '1,510', 'date': 'August 7, 2025'},
                            {'number': '1,511', 'date': 'August 8, 2025'},
                            {'number': '1,512', 'date': 'August 9, 2025'},
                            {'number': '1,513', 'date': 'August 10, 2025'}
                        ],
                        'winners': [
                            {'name': 'Brent', 'weekly_total': 19},
                            {'name': 'Malia', 'weekly_total': 19}
                        ]
                    }
                }
                
                # Generate pages for each week
                for week_slug, data in week_data.items():
                    output_path = os.path.join(weeks_dir, f"{week_slug}.html")
                    with open(output_path, 'w', encoding='utf-8') as f:
                        html_content = template.render(**data)
                        f.write(html_content)
                    logging.info(f"Generated week page for {week_slug}")
                
                return week_data

            # Generate day pages for each Wordle game
            def generate_day_pages(week_data):
                logging.info("Generating day pages for Wordle games")
                
                # Create days directory if it doesn't exist
                days_dir = os.path.join("website_export", "days")
                if not os.path.exists(days_dir):
                    os.makedirs(days_dir)
                
                # Get the day template
                env = Environment(loader=FileSystemLoader("website_export/templates"))
                template = env.get_template("day.html")
                
                # Generate pages for each day in each week
                for week_slug, week_info in week_data.items():
                    for game in week_info['wordle_games']:
                        # Clean the number for filename
                        clean_number = game['number'].replace(',', '')
                        
                        # Create test data for scores
                        day_data = {
                            'title': f'Wordle #{game["number"]} - {game["date"]}',
                            'wordle_number': game['number'],
                            'wordle_date': game['date'],
                            'week_slug': week_slug,
                            'scores': [
                                {
                                    'name': 'Brent',
                                    'has_score': True,
                                    'score': '3',
                                    'emoji_pattern': '⬛🟨🟨⬛⬛\n⬛🟩⬛🟩🟩\n🟩🟩🟩🟩🟩'
                                },
                                {
                                    'name': 'Malia',
                                    'has_score': True,
                                    'score': '4',
                                    'emoji_pattern': '⬛⬛🟨🟩⬛\n⬛🟩⬛🟩🟩\n🟨🟩⬛🟩🟩\n🟩🟩🟩🟩🟩'
                                },
                                {
                                    'name': 'Evan',
                                    'has_score': True,
                                    'score': '3',
                                    'emoji_pattern': '🟨⬛⬛⬛⬛\n🟨🟩🟩⬛⬛\n🟩🟩🟩🟩🟩'
                                },
                                {
                                    'name': 'Joanna',
                                    'has_score': True,
                                    'score': '5',
                                    'emoji_pattern': '⬛⬛⬛⬛🟨\n⬛⬛🟨⬛⬛\n⬛⬛🟩🟨🟩\n🟨⬛🟩🟩🟩\n🟩🟩🟩🟩🟩'
                                },
                                {
                                    'name': 'Nanna',
                                    'has_score': True,
                                    'score': '4',
                                    'emoji_pattern': '⬛🟨⬛🟨🟨\n🟨⬛🟨🟨🟨\n🟨🟩🟩⬛🟩\n🟩🟩🟩🟩🟩'
                                }
                            ]
                        }
                        
                        # For 1,508 let's have a failure example
                        if game['number'] == '1,508':
                            day_data['scores'].append({
                                'name': 'Keith',
                                'has_score': True,
                                'score': 'X/6',
                                'emoji_pattern': '⬛⬛⬛⬛🟨\n⬛⬛🟨⬛⬛\n⬛🟨⬛⬛⬛\n🟨⬛⬛🟩⬛\n🟨🟨⬛🟩🟩\n🟨🟨🟨🟩🟩'
                            })
                        
                        output_path = os.path.join(days_dir, f"wordle-{clean_number}.html")
                        with open(output_path, 'w', encoding='utf-8') as f:
                            html_content = template.render(**day_data)
                            f.write(html_content)
                        logging.info(f"Generated day page for Wordle #{game['number']}")

            # Call the functions to generate pages
            week_data = generate_week_pages()
            generate_day_pages(week_data)

            logging.info("Multi-league export completed successfully")
            return True  # Return True to indicate success to the integrated script
        else:
            logging.error("Failed to export all leagues")
            return False
    except Exception as e:
        logging.error(f"DEBUG: Error in export_all_leagues: {e}")
        return False
    
if __name__ == "__main__":
    main()
