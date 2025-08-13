import sqlite3
import sys

def check_week_scores():
    conn = sqlite3.connect('wordle_league.db')
    cursor = conn.cursor()
    
    print("=== CHECKING SCORES FOR WORDLE WEEK 1506-1513 ===\n")
    print("Using 5 BEST (LOWEST) scores for weekly total\n")
    
    # Check all leagues
    for league_id in range(1, 6):
        # Get league name based on league_id
        league_names = {1: "Wordle Warriorz", 2: "Wordle Gang", 3: "Wordle PAL", 
                      4: "Wordle Party", 5: "Wordle Vball"}
        league_name = league_names.get(league_id, f"League {league_id}")
        
        print(f"\n=== LEAGUE {league_id} ({league_name}) ===")
        
        # Get all players in this league
        cursor.execute("SELECT id, name FROM players WHERE league_id = ?", (league_id,))
        players = cursor.fetchall()
        
        print(f"Found {len(players)} players")
        print("-" * 50)
        
        # Track lowest score and winners
        lowest_score = float('inf')
        eligible_players = []
        
        # Check each player's scores
        for player_id, player_name in players:
            # Get player scores for the specific week
            cursor.execute("""
                SELECT score, wordle_number 
                FROM scores 
                WHERE player_id = ? 
                AND wordle_number BETWEEN 1506 AND 1513
                AND score NOT IN ('X', 'X/6', '7')
                ORDER BY wordle_number
            """, (player_id,))
            scores = cursor.fetchall()
            
            # Calculate valid scores
            valid_scores = []
            for score, wordle_num in scores:
                try:
                    valid_scores.append((int(score), wordle_num))
                except ValueError:
                    # Skip non-numeric scores
                    pass
            
            # Display player info
            print(f"Player: {player_name}")
            print(f"  Total valid scores for Wordle 1506-1513: {len(valid_scores)}")
            
            if valid_scores:
                # Print each score
                print("  Individual scores:")
                for score, wordle_num in valid_scores:
                    print(f"    Wordle {wordle_num}: {score}")
                
                # Calculate weekly total using 5 best scores if they have 5+ scores
                if len(valid_scores) >= 5:
                    # Sort scores by value (lowest first) and take best 5
                    best_five_scores = sorted(valid_scores, key=lambda x: x[0])[:5]
                    weekly_total = sum(score for score, _ in best_five_scores)
                    
                    print("  Best 5 scores used for weekly total:")
                    for score, wordle_num in sorted(best_five_scores, key=lambda x: x[1]):
                        print(f"    Wordle {wordle_num}: {score}")
                    
                    print(f"  WEEKLY TOTAL: {weekly_total} (best 5 of {len(valid_scores)} scores)")
                    
                    # Track for winner determination
                    eligible_players.append((player_name, weekly_total, len(valid_scores)))
                    
                    # Update lowest score
                    if weekly_total < lowest_score:
                        lowest_score = weekly_total
                else:
                    print(f"  Not enough scores (min 5 required)")
            else:
                print(f"  No valid scores found in this range")
            
            print()
        
        # Display weekly winner(s)
        if eligible_players:
            winners = [p for p in eligible_players if p[1] == lowest_score]
            print(f"WEEKLY WINNERS FOR LEAGUE {league_id}:")
            for winner_name, total, count in winners:
                print(f"  {winner_name}: {total} from best 5 scores (had {count} valid scores)")
                
            # Show expected HTML output format
            winner_names = [w[0] for w in winners]
            winner_str = ', '.join(winner_names)
            print(f"\nHTML Season Table Entry Would Be:")
            print(f"<tr><td>{winner_str}</td><td>{len(winners)}</td><td>Aug 4th - ({lowest_score})</td></tr>")
        else:
            print(f"No eligible players with 5+ scores for league {league_id}")
        
        print("\n" + "=" * 50)

    conn.close()

if __name__ == "__main__":
    check_week_scores()
