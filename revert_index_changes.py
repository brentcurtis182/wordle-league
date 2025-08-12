#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import shutil
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Export directory
EXPORT_DIR = 'website_export'
BACKUP_DIR = 'website_export_backup'

def restore_backup_if_exists():
    """Restore from backup if it exists"""
    backup_index = os.path.join(BACKUP_DIR, "index.html")
    if os.path.exists(backup_index):
        logging.info("Found backup index.html, restoring it...")
        shutil.copy(backup_index, os.path.join(EXPORT_DIR, "index.html"))
        logging.info("Restored original index.html")
        return True
    return False

def get_league_config():
    """Load league configuration from JSON file"""
    if not os.path.exists('league_config.json'):
        logging.error("league_config.json not found")
        return None
        
    try:
        with open('league_config.json', 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logging.error(f"Error loading league config: {e}")
        return None

def revert_changes():
    """Revert changes made to index pages"""
    # First try to restore from backup
    if restore_backup_if_exists():
        return True
    
    # If no backup, we need to find the original index pages
    config = get_league_config()
    if not config:
        logging.error("Failed to load league configuration")
        return False
    
    # Remove the created league index pages
    for league in config.get('leagues', []):
        export_path = league.get('html_export_path', '')
        if export_path:
            league_index = os.path.join(EXPORT_DIR, export_path, "index.html")
            if os.path.exists(league_index):
                logging.info(f"Removing league index at {league_index}")
                os.remove(league_index)
    
    # Remove the leagues selection page
    leagues_page = os.path.join(EXPORT_DIR, "leagues.html")
    if os.path.exists(leagues_page):
        logging.info(f"Removing leagues selection page at {leagues_page}")
        os.remove(leagues_page)
    
    # Remove the templates directory
    templates_dir = os.path.join(EXPORT_DIR, "templates")
    if os.path.exists(templates_dir):
        logging.info(f"Removing templates directory at {templates_dir}")
        shutil.rmtree(templates_dir)
    
    return True

if __name__ == "__main__":
    logging.info("Reverting changes to index pages...")
    if revert_changes():
        logging.info("Successfully reverted changes")
    else:
        logging.error("Failed to revert changes")
