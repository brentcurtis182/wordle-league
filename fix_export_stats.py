import sqlite3
import os
import sys
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('fix_export_stats.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

DATABASE_PATH = 'wordle_league.db'

def check_database_schema():
    """Check what tables and columns actually exist in the database"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        logging.info(f"Found tables: {tables}")
        
        # Check columns in the scores table
        if 'scores' in tables:
            cursor.execute("PRAGMA table_info(scores)")
            columns = [row[1] for row in cursor.fetchall()]
            logging.info(f"Columns in scores table: {columns}")
        
        return tables
    except Exception as e:
        logging.error(f"Error checking database schema: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_all_players():
    """Get a list of all players from the scores table"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get distinct player names from the scores table
        cursor.execute("SELECT DISTINCT player_name FROM scores")
        players = [row[0] for row in cursor.fetchall()]
        logging.info(f"Found {len(players)} players: {players}")
        
        return players
    except Exception as e:
        logging.error(f"Error getting players: {e}")
        return []
    finally:
        if conn:
            conn.close()

def calculate_weekly_stats():
    """Calculate weekly stats for all players by querying the scores table directly"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Calculate the start of the week (Monday)
        today = datetime.now()
        days_since_monday = today.weekday()
        start_of_week = today - timedelta(days=days_since_monday)
        start_date = start_of_week.strftime('%Y-%m-%d')
        
        # Go back an additional 2 days to be safe and catch any Monday scores
        adjusted_start_date = (start_of_week - timedelta(days=2)).strftime('%Y-%m-%d')
        logging.info(f"Using start date for weekly stats: {start_date} (adjusted to {adjusted_start_date})")
        
        # Get all players
        players = get_all_players()
        
        # Calculate weekly stats for each player
        weekly_stats = []
        for player in players:
            # Get all scores for this player this week
            cursor.execute("""
                SELECT wordle_num, score, emoji_pattern, timestamp 
                FROM scores 
                WHERE player_name = ? AND timestamp >= ? 
                ORDER BY wordle_num
            """, (player, adjusted_start_date))
            
            scores = cursor.fetchall()
            logging.info(f"Player {player} has {len(scores)} scores this week from {adjusted_start_date}")
            
            # Calculate totals
            valid_scores = []
            failed_attempts = 0
            for score_row in scores:
                wordle_num, score_val, emoji_pattern, date = score_row
                logging.info(f"  - Wordle #{wordle_num}: Score {score_val}, Date {date}")
                
                # Convert score to int if possible
                try:
                    if score_val not in ('X', 'x', None):
                        score_int = int(score_val)
                        valid_scores.append(score_int)
                    else:
                        failed_attempts += 1
                except (ValueError, TypeError):
                    logging.warning(f"Invalid score value: {score_val} for player {player}")
            
            # Calculate weekly score (sum of valid scores)
            weekly_score = sum(valid_scores) if valid_scores else 0
            
            weekly_stats.append({
                'player': player,
                'weekly_score': weekly_score,
                'used_scores': len(valid_scores),
                'failed_attempts': failed_attempts
            })
            
            logging.info(f"Player {player} weekly stats: Score {weekly_score}, Used {len(valid_scores)}, Failed {failed_attempts}")
        
        return weekly_stats
    except Exception as e:
        logging.error(f"Error calculating weekly stats: {e}")
        return []
    finally:
        if conn:
            conn.close()

def calculate_all_time_stats():
    """Calculate all-time stats for all players by querying the scores table directly"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get all players
        players = get_all_players()
        
        # Calculate all-time stats for each player
        all_time_stats = []
        for player in players:
            # Get all scores for this player
            cursor.execute("""
                SELECT wordle_num, score, emoji_pattern, timestamp 
                FROM scores 
                WHERE player_name = ? 
                ORDER BY wordle_num
            """, (player,))
            
            scores = cursor.fetchall()
            logging.info(f"Player {player} has {len(scores)} total scores")
            
            # Calculate totals
            valid_scores = []
            failed_attempts = 0
            for score_row in scores:
                wordle_num, score_val, emoji_pattern, date = score_row
                
                # Convert score to int if possible
                try:
                    if score_val not in ('X', 'x', None):
                        score_int = int(score_val)
                        valid_scores.append(score_int)
                    else:
                        failed_attempts += 1
                except (ValueError, TypeError):
                    logging.warning(f"Invalid score value: {score_val} for player {player}")
            
            # Calculate average score (include failed attempts as 7)
            all_scores = valid_scores + [7] * failed_attempts
            average_score = sum(all_scores) / len(all_scores) if all_scores else 0
            
            all_time_stats.append({
                'player': player,
                'games_played': len(valid_scores),
                'average_score': round(average_score, 2),
                'failed_attempts': failed_attempts
            })
            
            logging.info(f"Player {player} all-time stats: Games {len(valid_scores)}, Avg {round(average_score, 2)}, Failed {failed_attempts}")
        
        return all_time_stats
    except Exception as e:
        logging.error(f"Error calculating all-time stats: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_index_html():
    """Update the index.html file with the correct weekly and all-time stats"""
    try:
        # Calculate stats
        weekly_stats = calculate_weekly_stats()
        all_time_stats = calculate_all_time_stats()
        
        # Read the current index.html file
        index_path = os.path.join('website_export', 'index.html')
        with open(index_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Find the weekly stats section
        weekly_start = html_content.find('<div id="weekly-stats"')
        weekly_end = html_content.find('</div>', html_content.find('</table>', weekly_start))
        
        # Find the all-time stats section
        all_time_start = html_content.find('<div id="stats"')
        all_time_end = html_content.find('</div>', html_content.find('</table>', all_time_start))
        
        # Generate new weekly stats HTML
        weekly_html = '<div id="weekly-stats" class="tab-content active">\n'
        weekly_html += '    <h2 style="margin-top: 5px; margin-bottom: 10px;">Weekly Stats</h2>\n'
        weekly_html += '    <div class="table-container">\n'
        weekly_html += '        <table>\n'
        weekly_html += '            <thead>\n'
        weekly_html += '                <tr>\n'
        weekly_html += '                    <th>Player</th>\n'
        weekly_html += '                    <th>Weekly Score</th>\n'
        weekly_html += '                    <th>Used Scores</th>\n'
        weekly_html += '                    <th>Failed Attempts</th>\n'
        weekly_html += '                    <th>Thrown Out</th>\n'
        weekly_html += '                </tr>\n'
        weekly_html += '            </thead>\n'
        weekly_html += '            <tbody>\n'
        
        # Sort weekly stats by weekly score (ascending)
        weekly_stats.sort(key=lambda x: x['weekly_score'] if x['used_scores'] > 0 else float('inf'))
        
        for player_stats in weekly_stats:
            player = player_stats['player']
            weekly_score = player_stats['weekly_score']
            used_scores = player_stats['used_scores']
            failed_attempts = player_stats['failed_attempts']
            
            # Highlight players with 5+ scores
            highlight = ' class="highlighted"' if used_scores >= 5 else ''
            
            weekly_html += f'                <tr{highlight}>\n'
            weekly_html += f'                    <td>{player}</td>\n'
            weekly_html += f'                    <td class="weekly-score">{weekly_score if used_scores > 0 else "-"}</td>\n'
            weekly_html += f'                    <td class="used-scores">{used_scores}</td>\n'
            weekly_html += f'                    <td class="failed-attempts">{failed_attempts}</td>\n'
            weekly_html += f'                    <td class="thrown-out">-</td>\n'
            weekly_html += f'                </tr>\n'
        
        weekly_html += '            </tbody>\n'
        weekly_html += '        </table>\n'
        weekly_html += '        <p style="margin-top: 10px; font-size: 0.9em; font-style: italic; text-align: center;">Failed attempts do not count towards your \'Used Scores\'</p>\n'
        weekly_html += '    </div>\n'
        weekly_html += '</div>'
        
        # Generate new all-time stats HTML
        all_time_html = '<div id="stats" class="tab-content">\n'
        all_time_html += '    <h2 style="margin-top: 5px; margin-bottom: 10px;">All-Time Stats</h2>\n'
        all_time_html += '    <p style="margin-top: 0; margin-bottom: 10px; font-size: 0.9em; font-style: italic;">Average includes all games. Failed attempts (X/6) count as 7 in the average calculation.</p>\n'
        all_time_html += '    <div class="table-container">\n'
        all_time_html += '        <table>\n'
        all_time_html += '            <thead>\n'
        all_time_html += '                <tr>\n'
        all_time_html += '                    <th>Player</th>\n'
        all_time_html += '                    <th>Games</th>\n'
        all_time_html += '                    <th>Avg</th>\n'
        all_time_html += '                </tr>\n'
        all_time_html += '            </thead>\n'
        all_time_html += '            <tbody>\n'
        
        # Sort all-time stats by average score (ascending)
        all_time_stats.sort(key=lambda x: x['average_score'] if x['games_played'] > 0 else float('inf'))
        
        for player_stats in all_time_stats:
            player = player_stats['player']
            games = player_stats['games_played']
            avg = player_stats['average_score']
            
            # Highlight players with 5+ games
            total_games = games + player_stats['failed_attempts']
            highlight = ' class="highlighted"' if total_games >= 5 else ''
            
            all_time_html += f'                <tr{highlight}>\n'
            all_time_html += f'                    <td>{player}</td>\n'
            all_time_html += f'                    <td>{games if games > 0 else "-"}</td>\n'
            all_time_html += f'                    <td>{avg if games > 0 else "-"}</td>\n'
            all_time_html += f'                </tr>\n'
        
        all_time_html += '            </tbody>\n'
        all_time_html += '        </table>\n'
        all_time_html += '    </div>\n'
        all_time_html += '</div>'
        
        # Replace sections in the HTML
        new_html = (
            html_content[:weekly_start] + 
            weekly_html + 
            html_content[weekly_end+6:all_time_start] + 
            all_time_html + 
            html_content[all_time_end+6:]
        )
        
        # Write the updated HTML back to the file
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(new_html)
        
        logging.info("Successfully updated index.html with correct weekly and all-time stats")
        
        # Also update the index.html in the root website folder
        try:
            with open('index.html', 'w', encoding='utf-8') as f:
                f.write(new_html)
            logging.info("Also updated root index.html")
        except Exception as e:
            logging.warning(f"Could not update root index.html: {e}")
        
        return True
    except Exception as e:
        logging.error(f"Error updating index.html: {e}")
        return False

def publish_to_github():
    """Push the updated files to GitHub"""
    try:
        os.chdir('website_export')
        os.system('git add .')
        os.system('git commit -m "Update weekly and all-time stats with fixed calculation"')
        os.system('git push origin gh-pages')
        os.chdir('..')
        logging.info("Successfully pushed changes to GitHub")
        return True
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False

if __name__ == "__main__":
    print("Starting fix for export stats...")
    
    # Check what tables and columns we actually have
    tables = check_database_schema()
    
    # Update index.html with correct stats
    if update_index_html():
        print("Successfully updated index.html with correct weekly and all-time stats")
        
        # Push changes to GitHub
        if publish_to_github():
            print("Successfully pushed changes to GitHub")
        else:
            print("Failed to push changes to GitHub")
    else:
        print("Failed to update index.html")
