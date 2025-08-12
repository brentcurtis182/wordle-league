#!/usr/bin/env python3
# Minimal modification of integrated_auto_update_multi_league.py to show DOM elements

import sys
import os
import integrated_auto_update_multi_league as main_script

# Override the save_score_to_db function to just print scores instead of saving them
def print_score(player, wordle_num, score, emoji_pattern=None, league_id=1):
    print(f"\n{'='*50}")
    print(f"SCORE FOUND: Wordle #{wordle_num}")
    print(f"{'='*50}")
    print(f"Player: {player}")
    print(f"Score: {score}/6")
    print(f"League: {league_id}")
    if emoji_pattern:
        print(f"Emoji Pattern:")
        print(emoji_pattern)
    print(f"{'='*50}")
    return "printed"

# Patch the original function to use our printing function instead
main_script.save_score_to_db = print_score

# Just run the main extraction function
if __name__ == "__main__":
    print("\nRunning score extraction to print DOM elements for today's scores...")
    main_script.extract_wordle_scores_multi_league()
    print("\nDone!")
