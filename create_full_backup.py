#!/usr/bin/env python3
import os
import shutil
import datetime
import sys

def create_full_backup(backup_name=None):
    """
    Create a full backup of the website_export directory
    
    Args:
        backup_name: Optional name for the backup. If not provided, timestamp will be used
    
    Returns:
        Path to the backup directory
    """
    # Source directory
    source_dir = 'website_export'
    
    # Create backup name
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if backup_name:
        backup_dir = f"website_export_backup_{backup_name}_{timestamp}"
    else:
        backup_dir = f"website_export_backup_{timestamp}"
    
    # Create backup
    try:
        shutil.copytree(source_dir, backup_dir)
        print(f"Backup created successfully at: {backup_dir}")
        return backup_dir
    except Exception as e:
        print(f"Error creating backup: {e}")
        return None

def restore_from_backup(backup_dir):
    """
    Restore website_export from a backup directory
    
    Args:
        backup_dir: Path to the backup directory
    
    Returns:
        Boolean indicating success
    """
    # Target directory
    target_dir = 'website_export'
    
    # Backup the current state before overwriting
    create_full_backup("pre_restore")
    
    # Delete current directory
    try:
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        
        # Copy backup to target
        shutil.copytree(backup_dir, target_dir)
        print(f"Successfully restored from backup: {backup_dir}")
        return True
    except Exception as e:
        print(f"Error restoring from backup: {e}")
        return False

def list_backups():
    """
    List all available backups
    """
    backups = []
    
    # Find all directories that match the backup pattern
    for item in os.listdir('.'):
        if os.path.isdir(item) and item.startswith('website_export_backup_'):
            backups.append(item)
    
    # Sort by creation time (newest first)
    backups.sort(reverse=True)
    
    if not backups:
        print("No backups found.")
        return
    
    print("Available backups:")
    for i, backup in enumerate(backups):
        print(f"{i+1}. {backup}")
    
    return backups

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python create_full_backup.py create [backup_name]")
        print("  python create_full_backup.py restore <backup_dir>")
        print("  python create_full_backup.py list")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'create':
        backup_name = sys.argv[2] if len(sys.argv) > 2 else None
        create_full_backup(backup_name)
    
    elif command == 'restore':
        if len(sys.argv) < 3:
            print("Error: Please specify a backup directory to restore from.")
            sys.exit(1)
        
        backup_dir = sys.argv[2]
        if not os.path.isdir(backup_dir):
            print(f"Error: {backup_dir} is not a valid directory.")
            sys.exit(1)
        
        restore_from_backup(backup_dir)
    
    elif command == 'list':
        list_backups()
    
    else:
        print(f"Unknown command: {command}")
        print("Available commands: create, restore, list")
        sys.exit(1)
