import os
import shutil
import glob
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set the source backup time
backup_time = "20250810_2334"

# Main directory
base_dir = os.path.dirname(os.path.abspath(__file__))
website_dir = os.path.join(base_dir, "website_export")

# Restore main index.html
main_backup = os.path.join(website_dir, "backups", f"index.html_{backup_time}*")
main_target = os.path.join(website_dir, "index.html")

try:
    main_backup_file = glob.glob(main_backup)[0]
    shutil.copy2(main_backup_file, main_target)
    logging.info(f"Restored main index.html from {os.path.basename(main_backup_file)}")
except (IndexError, FileNotFoundError) as e:
    logging.error(f"Failed to find main backup file: {e}")

# League directories to restore
leagues = ["gang", "pal", "party", "vball"]

# Restore each league's index.html
for league in leagues:
    league_dir = os.path.join(website_dir, league)
    if not os.path.exists(league_dir):
        logging.warning(f"League directory {league} not found, skipping")
        continue
        
    backup_pattern = os.path.join(league_dir, f"index.html.backup_{backup_time}*")
    target_file = os.path.join(league_dir, "index.html")
    
    try:
        backup_files = glob.glob(backup_pattern)
        if backup_files:
            newest_backup = max(backup_files, key=os.path.getmtime)
            shutil.copy2(newest_backup, target_file)
            logging.info(f"Restored {league}/index.html from {os.path.basename(newest_backup)}")
        else:
            logging.warning(f"No backup found for {league}")
    except Exception as e:
        logging.error(f"Error restoring {league}: {e}")

logging.info("Backup restoration complete")
