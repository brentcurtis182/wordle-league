#!/usr/bin/env python3
"""
Script to fix the all-time stats in the PAL league page to include all players
"""
import sqlite3
import os
import sys
import json
import re
from datetime import datetime
from jinja2 import Template

# HTML template for the stats section
STATS_TEMPLATE = """
<div id="stats" class="tab-content">
    <h2 style="margin-top: 5px; margin-bottom: 10px;">All-Time Stats</h2>
    <p style="margin-top: 0; margin-bottom: 10px; font-size: 0.9em; font-style: italic;">Average includes all games. Failed attempts (X/6) count as 7 in the average calculation.</p>
    
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>Player</th>
                    <th>Average</th>
                    <th>Games</th>
                    <th>1's</th>
                    <th>2's</th>
                    <th>3's</th>
                    <th>4's</th>
                    <th>5's</th>
                    <th>6's</th>
                    <th>X's</th>
                </tr>
            </thead>
            <tbody>
                {% for player in all_time_stats %}
                <tr>
                    <td>{{ player.name }}</td>
                    <td class="average">{{ "%.2f"|format(player.average) if player.games > 0 else '-' }}</td>
                    <td class="games">{{ player.games }}</td>
                    <td class="ones">{{ player.ones }}</td>
                    <td class="twos">{{ player.twos }}</td>
                    <td class="threes">{{ player.threes }}</td>
                    <td class="fours">{{ player.fours }}</td>
                    <td class="fives">{{ player.fives }}</td>
                    <td class="sixes">{{ player.sixes }}</td>
                    <td class="fails">{{ player.fails }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
"""

def get_all_players_in_league(league_id):
    """Get all players in the PAL league"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT name, nickname FROM players
        WHERE league_id = ?
        """, (league_id,))
        
        players = cursor.fetchall()
        conn.close()
        
        # Return list of (name, nickname or name if no nickname)
        return [(p[0], p[1] if p[1] else p[0]) for p in players]
    except Exception as e:
        print(f"Error getting players: {e}", file=sys.stderr)
        return []

def get_player_all_time_stats(player_name, league_id):
    """Get all-time stats for a player"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT score FROM scores
        WHERE player_name = ? AND league_id = ?
        """, (player_name, league_id))
        
        scores = cursor.fetchall()
        conn.close()
        
        total_score = 0
        games_played = len(scores)
        ones = 0
        twos = 0
        threes = 0
        fours = 0
        fives = 0
        sixes = 0
        fails = 0
        
        for score_row in scores:
            score = score_row[0]
            if score == 'X':
                fails += 1
                total_score += 7  # X counts as 7 for average
            else:
                total_score += int(score)
                # Count score distribution
                if score == '1':
                    ones += 1
                elif score == '2':
                    twos += 1
                elif score == '3':
                    threes += 1
                elif score == '4':
                    fours += 1
                elif score == '5':
                    fives += 1
                elif score == '6':
                    sixes += 1
        
        # Calculate average score if there are games played
        avg_score = round(total_score / games_played, 2) if games_played > 0 else 0
        
        return {
            'name': player_name,
            'average': avg_score,
            'games': games_played,
            'ones': ones,
            'twos': twos,
            'threes': threes,
            'fours': fours,
            'fives': fives,
            'sixes': sixes,
            'fails': fails
        }
    except Exception as e:
        print(f"Error getting stats for {player_name}: {e}", file=sys.stderr)
        return {
            'name': player_name,
            'average': 0,
            'games': 0,
            'ones': 0,
            'twos': 0,
            'threes': 0,
            'fours': 0,
            'fives': 0,
            'sixes': 0,
            'fails': 0
        }

def fix_pal_all_time_stats():
    """Fix the all-time stats in the PAL league page"""
    # PAL league ID is 3
    league_id = 3
    
    # Get all players in the PAL league
    players = get_all_players_in_league(league_id)
    
    # Get stats for each player
    all_time_stats = []
    for player_name, display_name in players:
        stats = get_player_all_time_stats(player_name, league_id)
        # Use display name instead of internal name
        stats['name'] = display_name
        all_time_stats.append(stats)
    
    # Sort by average score (lower is better), but put players with 0 games at the bottom
    all_time_stats.sort(key=lambda x: (x['games'] == 0, x['average']))
    
    # Render the all-time stats HTML
    template = Template(STATS_TEMPLATE)
    stats_html = template.render(all_time_stats=all_time_stats)
    
    # Read the existing PAL index file
    pal_index_path = 'website_export/pal/index.html'
    with open(pal_index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the stats div with our new one
    pattern = r'<div id="stats" class="tab-content">.*?</div>\s*</div>\s*</div>'
    new_content = re.sub(pattern, stats_html + '\n        </div>\n    </div>', content, 
                         flags=re.DOTALL)
    
    # Write back the updated file
    with open(pal_index_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Updated all-time stats in {pal_index_path} with {len(all_time_stats)} players")
    for player in all_time_stats:
        print(f"- {player['name']}: {player['games']} games, avg: {player['average']}")

if __name__ == "__main__":
    fix_pal_all_time_stats()
