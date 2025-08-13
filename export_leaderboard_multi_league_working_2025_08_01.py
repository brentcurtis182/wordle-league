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
from jinja2 import Template

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
</body>
</html>"""

except Exception as e:
    logging.error(f"Error loading templates: {e}")
    # Fall back to basic templates
    index_template = """<!DOCTYPE html><html><body><h1>Wordle League</h1></body></html>"""
    wordle_template = """<!DOCTYPE html><html><body><h1>Wordle Results</h1></body></html>"""

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
        JOIN players p ON s.player_name = p.name AND s.league_id = p.league_id
        WHERE s.wordle_num = ? AND s.league_id = ?
        ORDER BY 
            CASE 
                WHEN s.score = 'X' THEN 7
                ELSE CAST(s.score AS INTEGER)
            END
        """, (wordle_number, league_id))
        
        result = cursor.fetchall()
        
        for row in result:
            name = row[1] if row[1] else row[0]  # Use nickname if available
            score = row[2]
            emoji_pattern = row[3]
            
            # Process score for display
            has_score = True
            score_value = score
            if score in ('X', '-', 'None', ''):
                score_value = 'X'
            
            scores.append({
                'name': name,
                'has_score': has_score,
                'score': score_value,
                'emoji_pattern': emoji_pattern
            })
            
        # Get all players in this league who don't have a score
        cursor.execute("""
        SELECT p.name, p.nickname 
        FROM players p
        WHERE p.league_id = ? AND p.name NOT IN (
            SELECT s.player_name FROM scores s 
            WHERE s.wordle_num = ? AND s.league_id = ?
        )
        """, (league_id, wordle_number, league_id))
        
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
        SELECT DISTINCT wordle_num, timestamp FROM scores 
        WHERE league_id = ?
        ORDER BY wordle_num DESC
        LIMIT ?
        """, (league_id, limit))
        
        results = cursor.fetchall()
        
        for row in results:
            wordle_num = row[0]
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

def get_weekly_stats_by_league(league_id):
    """Get weekly stats for a specific league"""
    # Get league name for logging
    league_name = f'Unknown League {league_id}'
    try:
        # Try to get league name from league_config.json
        with open(os.path.join(script_dir, 'league_config.json'), 'r') as f:
            league_config = json.load(f)
            for league in league_config:
                if league.get('id') == league_id:
                    league_name = league.get('name', f'League {league_id}')
                    break
    except Exception as e:
        logging.warning(f"Could not get league name: {e}")

    conn = None
    stats = []
    
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # Get the current week's start date (Monday)
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        start_date = start_of_week.strftime('%Y-%m-%d')
        
        logging.info(f"Getting weekly stats for league {league_id} starting from {start_date}")
        
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
            
            # Get this player's scores for the current week
            # Use distinct scores to avoid duplicates
            cursor.execute("""
            SELECT DISTINCT score, timestamp, date(timestamp) as score_date
            FROM scores
            WHERE player_name = ? AND league_id = ? AND timestamp >= ?
            GROUP BY date(timestamp)  -- Only count one score per day
            ORDER BY 
                CASE 
                    WHEN score = 'X' THEN 7
                    ELSE CAST(score AS INTEGER)
                END
            """, (name, league_id, start_date))
            
            # Process the scores we found
            scores_this_week = cursor.fetchall()
            logging.info(f"Player {name} in league {league_id} has {len(scores_this_week)} unique scores this week")
            weekly_scores = []
            
            for score_row in scores_this_week:
                score = score_row[0]
                date = score_row[1][:10] if len(score_row) > 1 and score_row[1] else 'Unknown date'
                score_date = score_row[2] if len(score_row) > 2 else 'Unknown date'
                logging.info(f"Processing for weekly stats: {name} - Score: {score}, Date: {date}, Score Date: {score_date}")
                
                if score in ('X', '-', 'None', '') or not score:
                    # Failed attempt doesn't count for weekly score
                    continue
                else:
                    try:
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
            
            # Count failed attempts
            cursor.execute("""
            SELECT COUNT(*) FROM scores
            WHERE player_name = ? AND league_id = ? AND timestamp >= ? AND score = 'X'
            """, (name, league_id, start_date))
            failed_count = cursor.fetchone()[0]
            
            stats.append({
                'name': name,
                'weekly_score': total_weekly,
                'used_scores': used_scores if used_scores > 0 else 0,
                'failed_attempts': failed_count,  # Using 'failed_attempts' to match standard export
                'failed': failed_count,  # Keep 'failed' for backward compatibility
                'thrown_out': thrown_out if thrown_out else '-'
            })
        
        # Sort by games played (most first), then by weekly score (lowest first)
        # First make sure all entries have numeric values for sorting
        for stat in stats:
            if stat['weekly_score'] is None:
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
    """Get statistics for a specific league, only counting scores from this week"""
    conn = None
    stats = []
    
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # Get the current week's start date (Monday)
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        start_date = start_of_week.strftime('%Y-%m-%d')
        
        logging.info(f"Getting all-time stats for league {league_id} starting from {start_date}")
        
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
            
            # Get this player's scores, grouping by date to avoid duplicates
            # Only include scores from this week
            cursor.execute("""
            SELECT DISTINCT score, timestamp, date(timestamp) as score_date 
            FROM scores
            WHERE player_name = ? AND league_id = ? AND timestamp >= ?
            GROUP BY date(timestamp)  -- Only count one score per day
            """, (name, league_id, start_date))
            
            scores = cursor.fetchall()
            
            # Initialize statistics variables
            all_scores = []
            all_score_values = []
            total_games = 0
            ones = twos = threes = fours = fives = sixes = 0
            avg_score = None
            all_time_avg = None
            
            # Only calculate stats if player has scores
            if scores:
                # Calculate statistics
                all_scores = [score[0] for score in scores]
                all_score_values = [score for score in all_scores if score not in ('X', '-', 'None', '')]
                
                total_games = len(all_scores)
                valid_scores = [score for score in all_scores]
                
                # Count different score types
                ones = sum(1 for score in valid_scores if score == 1)
                twos = sum(1 for score in valid_scores if score == 2)
                threes = sum(1 for score in valid_scores if score == 3)
                fours = sum(1 for score in valid_scores if score == 4)
                fives = sum(1 for score in valid_scores if score == 5)
                sixes = sum(1 for score in valid_scores if score == 6)
                
                # Calculate average score (handling X/6 as 7)
                avg_score = sum([7 if s == 'X' else int(s) for s in all_score_values]) / len(all_score_values) if all_score_values else None
                
                # Calculate all-time average (including historical data if any)
                all_time_avg = avg_score  # For now, just use current period's average
            
            # Calculate failed attempts
            failed_attempts = sum(1 for score in all_scores if score == 'X')
            
            # Calculate total games (games played + failed attempts) for display
            if len(all_score_values) > 0:
                display_games = total_games
                display_total_games = total_games + failed_attempts
            else:
                display_games = '-'
                display_total_games = '-'
                
            # Add all players, even those with no valid scores
            stats.append({
                'name': name,
                'games_played': display_games,
                'total_games': display_total_games,  # Pre-calculated total for template
                'average': round(avg_score, 2) if avg_score is not None else '-',
                'all_time_average': round(all_time_avg, 2) if all_time_avg is not None else '-',
                'failed_attempts': failed_attempts,
                'failed': failed_attempts,  # Keep for backward compatibility
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
    
    # Get scores for this league
    latest_scores = get_scores_for_wordle_by_league(today_wordle, league_id)
    
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
            
            try:
                # Sanitize player data for template rendering to avoid type errors
                for player in all_time_stats:
                    # Ensure games_played and failed_attempts are consistent types
                    if player['games_played'] == '-':
                        player['games_played'] = 0
                        
                    # Convert all numeric values to appropriate types
                    player['games_played'] = int(player['games_played']) if not isinstance(player['games_played'], str) else 0
                    player['failed_attempts'] = int(player['failed_attempts']) if not isinstance(player['failed_attempts'], str) else 0
                    
                # Render template with sanitized data
                html_content = template.render(
                    latest_wordle=str(today_wordle),  # Convert to string
                    latest_scores=latest_scores,
                    recent_wordles=recent_wordles,
                    player_stats=weekly_stats,
                    all_time_stats=all_time_stats,
                    today_formatted=today_formatted,
                    title=title,
                    league_name=league_name
                )
            except Exception as e:
                logging.error(f"ERROR IN TEMPLATE RENDERING: {e}")
                # Debug the exact error location
                import traceback
                logging.error(traceback.format_exc())      
            
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
            
            html_content = template.render(
                wordle_number=wordle_number,
                scores=scores,
                recent_wordles=recent_wordles,
                today_formatted=wordle_date_formatted,
                player_stats=weekly_stats,
                all_time_stats=all_time_stats,
                title=title,
                league_name=league_name
            )
            
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
                <form action="{league_path}/index.html" method="get" target="_top">
                    <button type="submit" class="league-button">View League</button>
                </form>
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
