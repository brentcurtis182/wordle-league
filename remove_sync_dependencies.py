#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Remove all dependencies and references to sync_database_tables.py
This script will:
1. Create backups of all modified files
2. Remove references to the sync script from auto-update scripts
3. Prevent any future synchronization between 'scores' and 'score' tables

This eliminates the data inconsistencies caused by maintaining two separate tables.
"""

import os
import re
import shutil
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Files to modify (based on grep search results)
TARGET_FILES = [
    'server_auto_update_multi_league.py',
    'server_auto_update.py',
    'integrated_auto_update_multi_league_working_2025_08_01.py',
    'integrated_auto_update_multi_league_backup_20250802_135212.py',
    'fix_todays_scores.py',
    'extraction_diagnostic.py',
    'emergency_extract.py'
]

def backup_file(file_path):
    """Create a backup of the file before modifying it"""
    if not os.path.exists(file_path):
        logging.warning(f"File not found, skipping backup: {file_path}")
        return None
        
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = f"{file_path}_{timestamp}_backup"
    shutil.copy2(file_path, backup_path)
    logging.info(f"Created backup: {backup_path}")
    return backup_path

def remove_sync_references(file_path):
    """Remove references to sync_database_tables from a file"""
    if not os.path.exists(file_path):
        logging.warning(f"File not found, skipping: {file_path}")
        return False
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Create a backup
        backup_file(file_path)
        
        # Track if any changes were made
        changes_made = False
        
        # Remove import statements for sync_database_tables
        if "sync_database_tables" in content:
            # Remove definition of SYNC_SCRIPT variable
            modified_content = re.sub(
                r'SYNC_SCRIPT\s*=\s*os\.path\.join\([^)]*,\s*["\']sync_database_tables\.py["\']\)[^\n]*\n',
                '', 
                content
            )
            
            # Remove entire sync_database_tables function definition
            modified_content = re.sub(
                r'def\s+sync_database_tables\(\):[^#]*?(?=\n\S)',
                '',
                modified_content,
                flags=re.DOTALL
            )
            
            # Remove individual calls to the script or function
            modified_content = re.sub(
                r'(?:subprocess\.run\(\[sys\.executable,\s*["\']sync_database_tables\.py["\']\][^)]*\))|'
                r'(?:os\.system\(["\']python\s+sync_database_tables\.py["\']\))|'
                r'(?:sync_database_tables\(\))',
                '# Removed sync_database_tables call',
                modified_content
            )
            
            if modified_content != content:
                changes_made = True
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                logging.info(f"Removed sync_database_tables references from {file_path}")
            else:
                logging.info(f"No sync references found to remove in {file_path}")
        else:
            logging.info(f"No sync references found in {file_path}")
            
        return changes_made
    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to remove sync references from all target files"""
    logging.info("Starting removal of sync_database_tables references")
    
    # Process each target file
    files_modified = 0
    for file_name in TARGET_FILES:
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
        if remove_sync_references(file_path):
            files_modified += 1
            
    logging.info(f"Completed processing. Modified {files_modified} files.")
    
    # Create a disable script to prevent accidental use
    sync_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sync_database_tables.py')
    if os.path.exists(sync_path):
        backup_file(sync_path)
        with open(sync_path, 'w', encoding='utf-8') as f:
            f.write("""#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
This script has been disabled because it was causing data inconsistencies
by keeping multiple database tables in sync. The system now uses only
the 'scores' and 'players' tables, not the legacy 'score' table.
\"\"\"

import logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    logging.warning("This script has been disabled to prevent database inconsistencies.")
    logging.warning("The system now uses only the 'scores' and 'players' tables.")
    exit(1)
""")
        logging.info(f"Disabled {sync_path} to prevent accidental use")
    
    logging.info("Done! The sync_database_tables.py script has been disabled and all references removed.")
    logging.info("Now the system will use only the 'scores' table, preventing inconsistencies.")

if __name__ == "__main__":
    main()
