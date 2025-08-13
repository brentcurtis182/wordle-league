#!/usr/bin/env python3
"""
Comprehensive Wordle League Backup Script
Created on August 10, 2025 at 9:41pm
"""
import os
import sys
import shutil
import datetime
import logging
import zipfile

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

# Items to exclude from backup
EXCLUDE = [
    "__pycache__",
    ".git",
    ".github",
    "venv",
    "node_modules",
    "backups"
]

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

def create_project_archive(backup_dir, timestamp):
    """Create ZIP archive of the entire project directory excluding certain folders"""
    archive_path = os.path.join(backup_dir, f"wordle_league_full_{timestamp}.zip")
    
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(SCRIPT_DIR):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE]
            
            # Make paths relative to project directory
            rel_dir = os.path.relpath(root, SCRIPT_DIR)
            if rel_dir == '.':
                rel_dir = ''
                
            for file in files:
                # Skip the backup zip itself and large/binary files
                if file.endswith('.zip') or file.endswith('.pyc') or file == archive_path:
                    continue
                    
                file_path = os.path.join(root, file)
                if os.path.getsize(file_path) > 50 * 1024 * 1024:  # Skip files > 50MB
                    logging.warning(f"Skipping large file: {file_path}")
                    continue
                    
                # Add file to archive with relative path
                archive_name = os.path.join(rel_dir, file)
                zipf.write(file_path, archive_name)
    
    logging.info(f"Project archive created at {archive_path}")
    return archive_path

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
        f.write(f"- Full project source code archive\n")
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
        
        # Create full project archive
        archive_path = create_project_archive(backup_dir, timestamp)
        
        # Create README
        readme_path = create_readme(backup_dir, timestamp)
        
        print("\nBackup completed successfully!")
        print(f"Backup location: {backup_dir}")
        print("\nBackup contents:")
        print(f"- Database: {'✅ Success' if db_path else '❌ Failed'}")
        print(f"- Website: {'✅ Success' if website_path else '❌ Failed'}")
        print(f"- Archive: {'✅ Success' if archive_path else '❌ Failed'}")
        print(f"- README: {'✅ Success' if readme_path else '❌ Failed'}")
        
    except Exception as e:
        logging.error(f"Backup failed: {e}")
        print(f"❌ Backup failed: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
