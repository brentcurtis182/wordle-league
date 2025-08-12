#!/usr/bin/env python3
"""
Update Table References

This script finds all references to the old 'score' table and updates them
to use the new unified 'scores' table across the codebase.
"""

import os
import re
import shutil
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=f"table_migration_{datetime.now().strftime('%Y%m%d%H%M%S')}.log"
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

def backup_file(file_path):
    """Create a backup of a file before modifying it"""
    backup_path = f"{file_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
    try:
        shutil.copy2(file_path, backup_path)
        logging.info(f"Created backup: {backup_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to create backup of {file_path}: {e}")
        return False

def find_files_with_table_reference(directory, table_name="score"):
    """Find all Python files that reference the specified table name"""
    py_files = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Look for SQL queries with the table name
                        if f"FROM {table_name}" in content or f"from {table_name}" in content or \
                           f"INTO {table_name}" in content or f"into {table_name}" in content or \
                           f"UPDATE {table_name}" in content or f"update {table_name}" in content:
                            py_files.append(file_path)
                except Exception as e:
                    logging.warning(f"Could not read {file_path}: {e}")
    
    return py_files

def update_table_references(files, old_table="score", new_table="scores"):
    """Update references from old table to new table in the specified files"""
    pattern_pairs = [
        # SQL queries
        (re.compile(f"FROM\\s+{old_table}\\b", re.IGNORECASE), f"FROM {new_table}"),
        (re.compile(f"INTO\\s+{old_table}\\b", re.IGNORECASE), f"INTO {new_table}"),
        (re.compile(f"UPDATE\\s+{old_table}\\b", re.IGNORECASE), f"UPDATE {new_table}"),
        (re.compile(f"DELETE\\s+FROM\\s+{old_table}\\b", re.IGNORECASE), f"DELETE FROM {new_table}"),
        (re.compile(f"INSERT\\s+INTO\\s+{old_table}\\b", re.IGNORECASE), f"INSERT INTO {new_table}"),
        (re.compile(f"CREATE\\s+TABLE\\s+{old_table}\\b", re.IGNORECASE), f"CREATE TABLE {new_table}"),
        (re.compile(f"ALTER\\s+TABLE\\s+{old_table}\\b", re.IGNORECASE), f"ALTER TABLE {new_table}"),
        (re.compile(f"DROP\\s+TABLE\\s+{old_table}\\b", re.IGNORECASE), f"DROP TABLE {new_table}"),
        (re.compile(f"JOIN\\s+{old_table}\\b", re.IGNORECASE), f"JOIN {new_table}")
    ]
    
    modified_count = 0
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
                
            modified_content = original_content
            replace_count = 0
            
            # Apply all replacement patterns
            for pattern, replacement in pattern_pairs:
                result_content = pattern.sub(replacement, modified_content)
                if result_content != modified_content:
                    replace_count += 1
                    modified_content = result_content
            
            # Only save if we made changes
            if replace_count > 0:
                # Backup the file first
                if backup_file(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(modified_content)
                    logging.info(f"Updated {replace_count} references in {file_path}")
                    modified_count += 1
        
        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")
    
    return modified_count

def main():
    """Main function to find and update table references"""
    directory = os.getcwd()  # Current directory
    
    logging.info(f"Scanning directory: {directory}")
    
    # Find files that reference the old table
    files = find_files_with_table_reference(directory, "score")
    logging.info(f"Found {len(files)} files with references to the 'score' table")
    
    if files:
        # Display the files we'll be updating
        print("\nFiles to update:")
        for file in files:
            print(f"- {os.path.basename(file)}")
        
        # Ask for confirmation before proceeding
        confirm = input("\nUpdate these files? (y/n): ")
        if confirm.lower() != 'y':
            print("Operation cancelled.")
            return
        
        # Update the references
        modified = update_table_references(files, "score", "scores")
        logging.info(f"Updated {modified} files")
        print(f"\nSuccessfully updated {modified} files.")
    else:
        print("No files found with references to the 'score' table.")

if __name__ == "__main__":
    print("Table Reference Migration Tool")
    print("This will update references from 'score' to 'scores' in SQL queries")
    print("=" * 60)
    main()
