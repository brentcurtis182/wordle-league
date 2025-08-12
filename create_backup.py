#!/usr/bin/env python3
"""
Simplified Wordle League Backup Script
Created on August 10, 2025 at 9:41pm
"""
import os
import sys
import shutil
import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backup_log.log"),
        logging.StreamHandler()
    ]
)

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_ROOT = os.path.join(SCRIPT_DIR, "backups")
DB_PATH = os.path.join(SCRIPT_DIR, "wordle_league.db")
WEBSITE_EXPORT_DIR = os.path.join(SCRIPT_DIR, "website_export")

def get_timestamp():
    """Get current timestamp in format YYYYMMDD_HHMMSS"""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def create_backup_dir(timestamp):
    """Create backup directory with timestamp"""
    backup_dir = os.path.join(BACKUP_ROOT, f"wordle_league_backup_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir

def backup_database(backup_dir, timestamp):
    """Backup the SQLite database"""
    if os.path.exists(DB_PATH):
        db_backup_path = os.path.join(backup_dir, f"wordle_league_{timestamp}.db")
        shutil.copy2(DB_PATH, db_backup_path)
        logging.info(f"Database backed up to {db_backup_path}")
        return db_backup_path
    else:
        logging.error(f"Database not found at {DB_PATH}")
        return None

def backup_website(backup_dir, timestamp):
    """Backup the website export directory"""
    if os.path.exists(WEBSITE_EXPORT_DIR):
        website_backup_path = os.path.join(backup_dir, f"website_export_{timestamp}")
        shutil.copytree(WEBSITE_EXPORT_DIR, website_backup_path)
        logging.info(f"Website exported files backed up to {website_backup_path}")
        return website_backup_path
    else:
        logging.error(f"Website export directory not found at {WEBSITE_EXPORT_DIR}")
        return None

def backup_python_files(backup_dir, timestamp):
    """Back up all Python scripts in the root directory"""
    py_backup_dir = os.path.join(backup_dir, "python_scripts")
    os.makedirs(py_backup_dir, exist_ok=True)
    
    count = 0
    for file in os.listdir(SCRIPT_DIR):
        if file.endswith(".py"):
            source_path = os.path.join(SCRIPT_DIR, file)
            dest_path = os.path.join(py_backup_dir, file)
            shutil.copy2(source_path, dest_path)
            count += 1
            
    logging.info(f"Backed up {count} Python files to {py_backup_dir}")
    return py_backup_dir if count > 0 else None

def create_readme(backup_dir, timestamp):
    """Create a README file with backup information"""
    readme_path = os.path.join(backup_dir, "README.txt")
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(readme_path, 'w') as f:
        f.write(f"Wordle League Backup\n")
        f.write(f"===================\n\n")
        f.write(f"Created: {current_time}\n")
        f.write(f"Backup ID: {timestamp}\n\n")
        f.write(f"Contents:\n")
        f.write(f"- Python source files\n")
        f.write(f"- Website export files\n")
        f.write(f"- Database backup\n\n")
        f.write(f"Status at time of backup:\n")
        f.write(f"- All league pages have proper names\n")
        f.write(f"- Real emoji patterns are now shown instead of placeholders\n")
        f.write(f"- All CSS and JavaScript resources are properly linked\n")
        f.write(f"- Tab navigation is working on all league pages\n\n")
        f.write(f"This backup was created after fixing emoji patterns and league names on August 10, 2025.\n")
    
    logging.info(f"Backup README created at {readme_path}")
    return readme_path

def main():
    """Main backup function"""
    timestamp = get_timestamp()
    print(f"=== Creating Wordle League Backup ({timestamp}) ===")
    
    # Create backup directory
    try:
        os.makedirs(BACKUP_ROOT, exist_ok=True)
        backup_dir = create_backup_dir(timestamp)
        print(f"Backup directory created at: {backup_dir}")
        
        # Backup database
        db_path = backup_database(backup_dir, timestamp)
        
        # Backup website files
        website_path = backup_website(backup_dir, timestamp)
        
        # Backup Python files
        py_path = backup_python_files(backup_dir, timestamp)
        
        # Create README
        readme_path = create_readme(backup_dir, timestamp)
        
        print("\nBackup completed successfully!")
        print(f"Backup location: {backup_dir}")
        print("\nBackup contents:")
        print(f"- Database: {'Success' if db_path else 'Failed'}")
        print(f"- Website: {'Success' if website_path else 'Failed'}")
        print(f"- Python scripts: {'Success' if py_path else 'Failed'}")
        print(f"- README: {'Success' if readme_path else 'Failed'}")
        
    except Exception as e:
        logging.error(f"Backup failed: {e}")
        print(f"Backup failed: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
