import os
import json
import shutil
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(message)s')

def restore_from_backup():
    """Restore website files from backups if they exist"""
    # Paths
    export_dir = "website_export"
    backup_dir = "website_export_backup"
    
    # Check if backup exists
    if not os.path.exists(backup_dir):
        logging.error(f"Backup directory {backup_dir} does not exist. Cannot restore.")
        return False
    
    try:
        # Remove current export directory
        if os.path.exists(export_dir):
            shutil.rmtree(export_dir)
            logging.info(f"Removed modified export directory: {export_dir}")
        
        # Copy backup to export directory
        shutil.copytree(backup_dir, export_dir)
        logging.info(f"Successfully restored website from backup: {backup_dir} → {export_dir}")
        return True
    except Exception as e:
        logging.error(f"Error restoring from backup: {e}")
        return False

def main():
    """Main execution function"""
    logging.info("Starting website restoration...")
    
    # Create backup directory if it doesn't exist
    backup_dir = "website_export_backup"
    export_dir = "website_export"
    
    # Check if backup exists, create if not
    if not os.path.exists(backup_dir):
        logging.info(f"Backup directory doesn't exist. Creating backup before restoration...")
        try:
            if os.path.exists(export_dir):
                shutil.copytree(export_dir, backup_dir)
                logging.info(f"Created backup: {export_dir} → {backup_dir}")
            else:
                logging.error(f"Export directory {export_dir} does not exist. Cannot create backup.")
                return
        except Exception as e:
            logging.error(f"Error creating backup: {e}")
            return
    
    # Restore from backup
    success = restore_from_backup()
    
    if success:
        logging.info("Website restoration complete!")
        logging.info("You can run an HTTP server to verify with: python -m http.server 8080 -d website_export")
    else:
        logging.error("Website restoration failed!")

if __name__ == "__main__":
    main()
