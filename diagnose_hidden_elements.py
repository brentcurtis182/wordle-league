#!/usr/bin/env python3
"""
Diagnostic script to examine hidden elements in Google Voice and compare 
extraction between different leagues
"""
import os
import sys
import time
import logging
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def extract_player_name_from_phone(phone_number, league_id=1):
    """Extract player name from phone number for a specific league"""
    logging.info(f"Looking up phone number {phone_number} for league {league_id}")
    
    # Clean phone number to digits-only for consistency
    digits_only = ''.join(filter(str.isdigit, phone_number))
    logging.info(f"Cleaned phone number: '{phone_number}' (digits: {digits_only})")
    
    # Main league mappings
    if league_id == 1:
        # Main league mappings - using digits-only phone numbers
        phone_to_name = {
            "3109263555": "Joanna",
            "9492304472": "Nanna",
            "8587359353": "Brent",
            "7603341190": "Malia",
            "7608462302": "Evan"
        }
        
        if digits_only in phone_to_name:
            player_name = phone_to_name[digits_only]
            logging.info(f"Found player {player_name} for phone {digits_only} in main league mapping")
            return player_name
    
    # PAL league mappings
    elif league_id == 3:
        # PAL league mappings - using digits-only phone numbers (standardized with main league)
        phone_to_name = {
            "8587359353": "Vox",  # Map Brent's number to Vox in PAL league
            "7604206113": "Fuzwuz",
            "7605830059": "Pants",
            "4698345364": "Starslider"
        }
        
        if digits_only in phone_to_name:
            player_name = phone_to_name[digits_only]
            logging.info(f"Found player {player_name} for phone {digits_only} in PAL league mapping")
            return player_name
    
    return None

def create_driver():
    """Create and configure Chrome webdriver"""
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    # chrome_options.add_argument("--headless")  # Uncomment to run headless
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def login_to_google_voice(driver):
    """Login to Google Voice with credentials"""
    # Load credentials from environment variables
    email = os.environ.get('GOOGLE_EMAIL')
    password = os.environ.get('GOOGLE_PASSWORD')
    
    if not email or not password:
        logging.error("Google credentials not found in environment variables")
        sys.exit(1)
    
    try:
        # Navigate to Google Voice
        driver.get("https://voice.google.com")
        logging.info("Navigating to Google Voice")
        
        # Wait for the login page
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "identifierId"))
        )
        
        # Enter email
        driver.find_element(By.ID, "identifierId").send_keys(email)
        driver.find_element(By.ID, "identifierNext").click()
        
        # Wait for password field and enter password
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "Passwd"))
        )
        time.sleep(1)  # Brief pause for stability
        driver.find_element(By.NAME, "Passwd").send_keys(password)
        driver.find_element(By.ID, "passwordNext").click()
        
        # Wait for Google Voice to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "gv-side-nav"))
        )
        logging.info("Successfully logged into Google Voice")
        return True
    except Exception as e:
        logging.error(f"Login failed: {e}")
        return False

def find_conversation_for_league(driver, league_name, league_id):
    """Find the conversation thread for a specific league"""
    try:
        # Wait for conversations to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "gv-conversation-list"))
        )
        time.sleep(2)  # Brief pause for stability
        
        # Get all conversation threads
        threads = driver.find_elements(By.CSS_SELECTOR, "div[role='listitem']")
        logging.info(f"Found {len(threads)} conversation threads")
        
        # Look for thread with participant annotations
        threads_with_annotations = []
        for i, thread in enumerate(threads):
            try:
                annotation = thread.find_element(By.CSS_SELECTOR, "div.annotation-content")
                annotation_text = annotation.text
                threads_with_annotations.append((i, thread, annotation_text))
                logging.info(f"Thread {i+1} participants: {annotation_text}")
            except:
                pass
        
        logging.info(f"Found {len(threads_with_annotations)} conversation threads with participant annotations")
        
        # Find the league's thread (would be based on participants in real code)
        # For diagnostic purposes, just take the first thread
        if threads_with_annotations:
            i, thread, _ = threads_with_annotations[0]
            logging.info(f"Found thread {i+1} for {league_name} (ID: {league_id})")
            thread.click()
            time.sleep(3)  # Wait for conversation to load
            return True
        
        return False
    except Exception as e:
        logging.error(f"Error finding conversation for {league_name}: {e}")
        return False

def analyze_hidden_elements(driver, league_id):
    """Analyze the hidden elements for the current conversation"""
    # Pattern to match Wordle results like "Wordle 789 3/6"
    wordle_pattern = re.compile(r'Wordle\s+(\d+)\s+([1-6]|X)/6')
    
    try:
        logging.info("Looking for visually hidden elements containing score data")
        hidden_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".cdk-visually-hidden"))
        )
        
        logging.info(f"Found {len(hidden_elements)} visually hidden elements")
        
        # Take a screenshot for debugging
        driver.save_screenshot(f"conversation_{league_id}_screenshot.png")
        
        # Analyze each hidden element
        for i, element in enumerate(hidden_elements):
            try:
                text = element.text
                # Log a truncated version to avoid flooding logs
                logging.info(f"Element {i+1} text (truncated): {text[:100]}...")
                
                # Look for phone number
                phone_match = re.search(r'(?:\+?1[-\s]?)?\(?([0-9]{3})\)?[-\s]?([0-9]{3})[-\s]?([0-9]{4})', text)
                if phone_match:
                    full_match = phone_match.group(0)
                    digits_only = ''.join(filter(str.isdigit, full_match))
                    if len(digits_only) >= 10:  # Ensure it's a valid number
                        logging.info(f"Element {i+1} contains phone: {full_match} (digits: {digits_only})")
                        
                        # Look for player name
                        player_name = extract_player_name_from_phone(digits_only, league_id)
                        if player_name:
                            logging.info(f"Element {i+1} phone maps to player: {player_name}")
                        
                        # Look for Wordle score
                        match = wordle_pattern.search(text)
                        if match:
                            wordle_num = match.group(1)
                            score = match.group(2)
                            logging.info(f"Element {i+1} contains Wordle {wordle_num} with score {score}/6")
                            
                            # Check for emoji pattern
                            has_emoji = any(emoji in text for emoji in ['\u2b1b', '\u2b1c', '\ud83d\udfe8', '\ud83d\udfe9'])
                            if has_emoji:
                                logging.info(f"Element {i+1} contains emoji pattern")
                                
                                # Full player-score association
                                if player_name:
                                    logging.info(f"FOUND FULL MATCH: Player {player_name} has Wordle {wordle_num} {score}/6 in league {league_id}")
            except Exception as e:
                logging.error(f"Error processing element {i+1}: {e}")
                
        return True
    except Exception as e:
        logging.error(f"Error analyzing hidden elements: {e}")
        return False

def main():
    """Main diagnostic function"""
    driver = create_driver()
    
    try:
        if login_to_google_voice(driver):
            # Define leagues
            leagues = [
                {"name": "Wordle Warriorz", "id": 1},
                {"name": "Wordle PAL", "id": 3}
            ]
            
            # Process each league
            for league in leagues:
                logging.info(f"\n\n======= PROCESSING LEAGUE: {league['name']} (ID: {league['id']}) =======")
                if find_conversation_for_league(driver, league['name'], league['id']):
                    logging.info(f"Analyzing hidden elements for {league['name']}")
                    analyze_hidden_elements(driver, league['id'])
                    time.sleep(2)  # Brief pause between leagues
    finally:
        # Always close the driver
        driver.quit()

if __name__ == "__main__":
    main()
