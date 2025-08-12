# Wordle League Backup - August 11th, 2025

This backup contains the complete state of the Wordle League website and code after fixing the weekly winner calculation in the Season tables.

## Fixed Issues

1. **Weekly Winner Calculation**: Updated to correctly use the 5 best (lowest) scores for determining weekly winners
   - Players must have at least 5 valid scores to be eligible
   - Winners are determined by the lowest sum of their 5 best scores
   - Ties are properly recognized (e.g., Brent, Malia, Joanna in Wordle Warriorz)
   - Winners and their scores are correctly displayed in the Season tables

2. **Correct Weekly Winners for Aug 4-10, 2025 (Wordle #1506-1513)**:
   - Wordle Warriorz: Brent, Malia, Joanna (tied at 14)
   - Wordle Gang: Brent (14)
   - Wordle PAL: Vox (14)
   - Wordle Party: Brent (14)
   - Wordle Vball: Brent (14)

## Files Included

- `website_export/`: Complete website files with updated HTML tables
- `*.py`: All Python scripts, including the fixed `update_season_winners.py`
- `wordle_league.db`: SQLite database with all player and score data

## Key Scripts

- `update_season_winners.py`: Updated to use the 5 best scores calculation
- `check_specific_week.py`: Verification script for the Aug 4-10 week scores
- `integrated_auto_update_multi_league.py`: Main extraction script for the system

## System Workflow

1. `scheduled_update.bat` calls `server_auto_update_multi_league.py`
2. `server_auto_update_multi_league.py` calls `integrated_auto_update_multi_league.py` for extraction
3. `export_leaderboard.py` is called to generate the website
4. `update_season_winners.py` is called to update the Season tables with weekly winners

This backup represents the complete and correct state of the website with the fixed weekly winner calculation.
