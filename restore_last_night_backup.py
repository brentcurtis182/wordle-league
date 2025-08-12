import os
import shutil
import datetime
import logging

# Setup logging
logging.basicConfig(
    filename='restore_last_night_backup.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def backup_current_file(file_path):
    """Create a backup of the current file before overwriting"""
    if os.path.exists(file_path):
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{file_path}.backup_{timestamp}"
        try:
            shutil.copy2(file_path, backup_path)
            logging.info(f"Backed up current file to {backup_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to backup {file_path}: {str(e)}")
            return False
    return True  # No need to backup if file doesn't exist

def restore_file(source_file, destination_file):
    """Restore a file from the backup to its original location"""
    if not os.path.exists(source_file):
        logging.error(f"Source file does not exist: {source_file}")
        return False
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(destination_file), exist_ok=True)
    
    # Backup current file
    if not backup_current_file(destination_file):
        return False
    
    try:
        shutil.copy2(source_file, destination_file)
        logging.info(f"Restored {source_file} to {destination_file}")
        return True
    except Exception as e:
        logging.error(f"Failed to restore {source_file} to {destination_file}: {str(e)}")
        return False

def main():
    # Define backup source directory and target export directory
    backup_dir = r"C:\Wordle-League\website_export_backup_Aug10_2025_1148pm_with_season_20250810_234948"
    export_dir = r"C:\Wordle-League\website_export"
    
    # Log start of restoration
    logging.info("Starting restoration from last night's backup (11:48 PM Aug 10)")
    print("Starting restoration from last night's backup (11:48 PM Aug 10)")
    
    # Files to restore - all league index.html files
    files_to_restore = [
        # Main league (Wordle Warriorz)
        {"source": os.path.join(backup_dir, "index.html"), 
         "dest": os.path.join(export_dir, "index.html")},
        
        # Wordle Gang
        {"source": os.path.join(backup_dir, "gang", "index.html"), 
         "dest": os.path.join(export_dir, "gang", "index.html")},
        
        # Wordle PAL
        {"source": os.path.join(backup_dir, "pal", "index.html"), 
         "dest": os.path.join(export_dir, "pal", "index.html")},
        
        # Wordle Party
        {"source": os.path.join(backup_dir, "party", "index.html"), 
         "dest": os.path.join(export_dir, "party", "index.html")},
        
        # Wordle Vball
        {"source": os.path.join(backup_dir, "vball", "index.html"), 
         "dest": os.path.join(export_dir, "vball", "index.html")},
        
        # Also restore other important files
        {"source": os.path.join(backup_dir, "styles.css"), 
         "dest": os.path.join(export_dir, "styles.css")},
        
        {"source": os.path.join(backup_dir, "script.js"), 
         "dest": os.path.join(export_dir, "script.js")},
        
        {"source": os.path.join(backup_dir, "landing.html"), 
         "dest": os.path.join(export_dir, "landing.html")}
    ]
    
    success_count = 0
    failure_count = 0
    
    # Restore each file
    for file_info in files_to_restore:
        source = file_info["source"]
        dest = file_info["dest"]
        
        print(f"Restoring {os.path.basename(source)} to {dest}...")
        if restore_file(source, dest):
            success_count += 1
        else:
            failure_count += 1
    
    # Log completion
    completion_message = f"Restoration complete: {success_count} files restored successfully, {failure_count} failures."
    logging.info(completion_message)
    print(completion_message)

if __name__ == "__main__":
    main()
