#!/usr/bin/env python3
# Enhanced version of integrated_auto_update.py with multi-league support
# This maintains all the functionality of the original while adding PAL league support

import os
import sys

import time
# Import hidden element extraction function
from direct_hidden_extraction import extract_with_hidden_elements
import logging
import inspect
import traceback
import subprocess
import sqlite3
import re
import json
import inspect
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Import enhanced functions
from enhanced_functions import update_website, push_to_github

# Import centralized phone mappings
from phone_mappings import get_player_name as get_player_from_phone

# Import our enhanced scrolling function
from scroll_in_thread import scroll_up_in_thread

# Import helper functions
from is_league_thread import is_league_thread
from robust_thread_click import click_thread_robustly

# Import direct URL navigation
from direct_url_only_navigation import navigate_to_thread_by_url
from fixed_extract_multi_league import extract_wordle_scores_multi_league as fixed_extract_multi_league
from run_extraction_fixed import run_extraction_with_fixed_method
from extract_scores_from_conversation import extract_scores_from_conversation

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("integrated_auto_update_multi_league.log"),
        logging.StreamHandler()
    ]
)

# League configuration 
LEAGUES = [
    {
        "league_id": 1, 
        "name": "Wordle Warriorz",
        "is_default": True
    },
    {
        "league_id": 2, 
        "name": "Wordle Gang",
        "is_default": False
    },
    {
        "league_id": 3, 
        "name": "Wordle PAL",
        "is_default": False
    },
    {
        "league_id": 4, 
        "name": "Wordle Party",
        "is_default": False
    },
    {
        "league_id": 5, 
        "name": "Wordle Vball",
        "is_default": False
    }
]


def click_conversation_thread(driver, thread, thread_info=None):
    """Click on a conversation thread with robust error handling
    
    Args:
        driver: Selenium WebDriver instance
        thread: Thread element to click
        thread_info: Optional description for logging
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not thread:
        logging.error("No thread provided to click")
        return False
        
    thread_desc = thread_info or "conversation thread"
    logging.info(f"Attempting to click {thread_desc}")
    
    # Take a screenshot before clicking
    driver.save_screenshot(f"before_click_{thread_desc.replace(' ', '_')}.png")
    
    # Try multiple click methods with proper waits
    methods = [
        {
            "name": "Scroll into view then click",
            "action": lambda: (
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thread),
                time.sleep(1),
                thread.click()
            )
        },
        {
            "name": "JavaScript click",
            "action": lambda: driver.execute_script("arguments[0].click();", thread)
        },
        {
            "name": "ActionChains click",
            "action": lambda: ActionChains(driver).move_to_element(thread).click().perform()
        }
    ]
    
    for method in methods:
        try:
            logging.info(f"Trying {method['name']}")
            method["action"]()
            time.sleep(3)  # Wait for thread to load
            
            # Check if thread loaded successfully using multiple possible DOM elements
            try:
                # Look for a variety of elements that would indicate a thread loaded
                css_selectors = [
                    "gv-message-input", 
                    "textarea.input",
                    "gv-message-list",
                    "div.message-item",
                    "gv-annotation",
                    "gv-thread-item",
                    "gv-message-thread-list-item"
                ]
                
                # Try each selector
                thread_loaded = False
                for selector in css_selectors:
                    try:
                        if driver.find_elements(By.CSS_SELECTOR, selector):
                            logging.info(f"Thread verified loaded by finding '{selector}'")
                            thread_loaded = True
                            break
                    except:
                        pass
                
                # Also check for any message content with Wordle in it
                if 'Wordle' in driver.page_source:
                    logging.info("Thread verified loaded by finding 'Wordle' in content")
                    thread_loaded = True
                
                if thread_loaded:
                    logging.info(f"{method['name']} successful!")
                    driver.save_screenshot(f"after_successful_click_{thread_desc.replace(' ', '_')}.png")
                    return True
                else:
                    logging.warning(f"{method['name']} didn't load thread completely, trying next method")
                    continue
            except Exception as e:
                logging.warning(f"{method['name']} verification error: {str(e)}")
                continue
                
        except Exception as e:
            logging.error(f"Error with {method['name']}: {str(e)}")
    
    logging.warning(f"All click methods failed verification for {thread_desc}, but thread may have opened successfully")
    driver.save_screenshot(f"verification_failed_but_assuming_success_{thread_desc.replace(' ', '_')}.png")
    return True  # Modified to assume success even when verification fails
def kill_chrome_processes():
    """Kill any running Chrome processes"""
    logging.info("Attempting to kill any running Chrome processes")
    try:
        # For Windows
        subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
        logging.info("Chrome processes terminated")
    except Exception as e:
        logging.error(f"Error killing Chrome processes: {e}")
    
    # Wait a moment for processes to fully terminate
    time.sleep(2)

def setup_driver():
    """Set up the Chrome driver with appropriate options"""
    logging.info("Setting up Chrome driver")
    try:
        # Kill any existing Chrome processes first
        kill_chrome_processes()
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Use existing Chrome profile to avoid login issues
        profile_path = os.path.join(os.getcwd(), "automation_profile")
        if os.path.exists(profile_path):
            chrome_options.add_argument(f"user-data-dir={profile_path}")
            logging.info(f"Using existing Chrome profile at {profile_path}")
        else:
            logging.warning(f"Chrome profile directory not found at {profile_path}, using default profile")
        
        # Initialize Chrome driver
        driver = webdriver.Chrome(options=chrome_options)
        
        return driver
    except Exception as e:
        logging.error(f"Error setting up Chrome driver: {e}")
        return None

def get_todays_wordle_number():
    """Get today's Wordle number dynamically based on the current date in Eastern Time
    
    Wordle puzzles reset at midnight Eastern Time, so we need to adjust based on that timezone.
    """
    # Wordle #1 was released on June 19, 2021
    wordle_start_date = datetime(2021, 6, 19).date()
    
    # Get current time and adjust for Eastern timezone
    # If it's before 9 PM Pacific (midnight Eastern), use today's date
    # Otherwise, use tomorrow's date
    now = datetime.now()
    hour = now.hour
    
    # For testing purposes, you can force a specific Wordle number if needed
    # return 1505  # Hardcoded value for testing
    
    if hour < 21:  # Before 9 PM Pacific (midnight Eastern)
        today = now.date()
    else:
        # After 9 PM Pacific, tomorrow's Wordle is already available
        today = (now + timedelta(days=1)).date()
    
    # Calculate days between start date and today
    days_since_start = (today - wordle_start_date).days
    
    # Wordle number is days since start + 1
    wordle_number = days_since_start + 1
    
    # For today, subtract 1 to get the current Wordle number
    # This is because the current Wordle is always the one from the previous day
    # until midnight Eastern (9 PM Pacific)
    if hour < 21:
        wordle_number -= 1
        
    logging.info(f"Calculated today's Wordle #{wordle_number} for date {today}")
    
    return wordle_number

def get_yesterdays_wordle_number():
    """Get yesterday's Wordle number dynamically based on yesterday's date in Eastern Time
    
    Simply returns one less than today's Wordle number.
    """
    # Simply one less than today's number
    today_wordle = get_todays_wordle_number()
    wordle_number = today_wordle - 1
    
    yesterday = (datetime.now() - timedelta(days=1)).date()
    logging.info(f"Calculated yesterday's Wordle #{wordle_number} for date {yesterday}")
    
    return wordle_number

def navigate_to_google_voice(driver):
    """Navigate to Google Voice and verify successful navigation"""
    try:
        # Navigate to Google Voice
        logging.info("Navigating to Google Voice...")
        driver.get("https://voice.google.com/messages")
        
        # Wait for the page to load
        time.sleep(5)
        
        # Take a screenshot to verify navigation
        driver.save_screenshot("google_voice_navigation.png")
        logging.info("Saved screenshot of Google Voice navigation")
        
        # Verify we're on the Google Voice page
        if "voice.google.com" in driver.current_url:
            logging.info("Successfully navigated to Google Voice")
            return True
        else:
            logging.error(f"Failed to navigate to Google Voice. Current URL: {driver.current_url}")
            return False
    except Exception as e:
        logging.error(f"Error navigating to Google Voice: {e}")
        return False

def find_conversation_threads(driver, league_id=1):
    """Find conversation threads for a specific league
    
    Args:
        driver: Selenium WebDriver instance
        league_id: League ID to find conversations for
        
    Returns:
        list: List of conversation thread elements or None if not found
    """
    try:
        # Wait for threads to appear
        logging.info(f"Looking for conversation threads for league {league_id}")
        
        # Take a screenshot to verify the state before searching
        driver.save_screenshot(f"before_thread_search_league_{league_id}.png")
        
        # Wait for thread items to be present with a longer timeout
        logging.info("Waiting for thread items to appear...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "gv-conversation-list gv-thread-item, div[role='button'].container, .mat-ripple.container"))
        )
        
        # Try multiple selector strategies to find conversation items
        selectors_to_try = [
            "div[role='button'].container",  # Most reliable selector based on testing
            "gv-conversation-list gv-thread-item",
            ".mat-ripple.container",
            "div.container[tabindex='0']",
            "gv-thread-item",
            "div.container.read"
        ]
        
        conversation_items = []
        for selector in selectors_to_try:
            try:
                items = driver.find_elements(By.CSS_SELECTOR, selector)
                if items:
                    logging.info(f"Found {len(items)} items with selector: {selector}")
                    conversation_items = items
                    break
            except Exception as e:
                logging.warning(f"Error with selector {selector}: {str(e)}")
        
        logging.info(f"Found {len(conversation_items)} total conversation threads")
        
        if len(conversation_items) == 0:
            logging.warning("No conversation threads found")
            driver.save_screenshot(f"no_threads_found_league_{league_id}.png")
            return None
            
        # If we're looking for Wordle Warriorz league (league_id 1)
        if league_id == 1:
            # Look for the thread with Wordle Warriorz identifiers
            for i, item in enumerate(conversation_items):
                try:
                    # Try to get the item's text content
                    item_text = item.text
                    logging.info(f"Thread {i+1} text: {item_text[:50].encode('ascii', 'replace').decode('ascii')}...")
                    
                    # Check if this has Wordle Warriorz participants - look for area code 310 which is unique to Warriorz
                    if any(identifier in item_text for identifier in ["(310)", "310", "Joanna", "Nanna", "Brent", "Malia", "Evan"]):
                        logging.info(f"Thread {i+1} appears to be the Wordle Warriorz league")
                        return [item]  # Return as a list for consistent handling
                except Exception as e:
                    logging.error(f"Error checking thread {i+1} for Warriorz: {e}")
            
        # If we're looking for PAL league (league_id 3)
        elif league_id == 3:
            # Look for the PAL thread with specific identifiers
            for i, item in enumerate(conversation_items):
                try:
                    # Try to get the item's text content
                    item_text = item.text
                    logging.info(f"Thread {i+1} text: {item_text[:50].encode('ascii', 'replace').decode('ascii')}...")
                    
                    # Check if this has PAL participants - look for area code 469 which is unique to PAL
                    if any(identifier in item_text for identifier in ["(469)", "469", "Fuzwuz", "Vox", "PAL", "Pants", "Starslider"]):
                        logging.info(f"Thread {i+1} appears to be the Wordle PAL league")
                        return [item]  # Return as a list for consistent handling
                except Exception as e:
                    logging.error(f"Error checking thread {i+1} for PAL: {e}")
        
        # If we reach here, we didn't find the right thread for the requested league
        logging.warning(f"Could not identify specific thread for league {league_id}")
        driver.save_screenshot(f"thread_identification_failed_league_{league_id}.png")
        
        # As a fallback, if we have exactly 2 threads total, use process of elimination
        if len(conversation_items) == 2:
            logging.info("Using process of elimination with 2 threads")
            # If we're looking for Warriorz and thread 1 has "310", return thread 1
            # If we're looking for PAL and thread 2 has "469", return thread 2
            # Otherwise return all threads
            for i, item in enumerate(conversation_items):
                item_text = item.text
                if league_id == 1 and "(310)" in item_text:
                    logging.info("Found Wordle Warriorz thread by area code 310")
                    return [item]
                elif league_id == 3 and "(469)" in item_text:
                    logging.info("Found PAL thread by area code 469")
                    return [item]
        
        # Last resort fallback
        logging.info("Returning all threads as a fallback")
        return conversation_items
        
    except Exception as e:
        logging.error(f"Error finding conversation threads: {str(e)}")
        driver.save_screenshot(f"thread_search_error_league_{league_id}.png")
        return None
            
        # If we're looking for Wordle Warriorz league (league_id 1)
        if league_id == 1:
            # Look for the thread with multiple participants
            for i, item in enumerate(conversation_items):
                try:
                    # Try to get the item's text content
                    item_text = item.text
                    logging.info(f"Thread {i+1} text: {item_text[:50].encode('ascii', 'replace').decode('ascii')}...")
                    
                    # Check if this has Wordle Warriorz participants
                    if any(phone in item_text for phone in ["310", "760", "949", "Joanna", "Nanna", "Brent", "Malia", "Evan"]):
                        logging.info(f"Thread {i+1} appears to be the Wordle Warriorz league")
                        return [item]  # Return as a list for consistent handling
                except Exception as e:
                    logging.error(f"Error checking thread {i+1} for Warriorz: {e}")
            
        # If we're looking for PAL league (league_id 3)
        elif league_id == 3:
            # Look for the PAL thread
            for i, item in enumerate(conversation_items):
                try:
                    # Try to get the item's text content
                    item_text = item.text
                    logging.info(f"Thread {i+1} text: {item_text[:50].encode('ascii', 'replace').decode('ascii')}...")
                    
                    # Check if this has PAL participants
                    if any(phone in item_text for phone in ["469", "858", "Fuzwuz", "Vox", "PAL", "Pants", "Starslider"]):
                        logging.info(f"Thread {i+1} appears to be the Wordle PAL league")
                        return [item]  # Return as a list for consistent handling
                except Exception as e:
                    logging.error(f"Error checking thread {i+1} for PAL: {e}")
        
        # If we reach here, we didn't find the right thread for the requested league
        logging.warning(f"Could not identify specific thread for league {league_id}")
        driver.save_screenshot(f"thread_identification_failed_league_{league_id}.png")
        
        # As a fallback, return all threads
        logging.info("Returning all threads as a fallback")
        return conversation_items
        
    except Exception as e:
        logging.error(f"Error finding conversation threads: {str(e)}")
        driver.save_screenshot(f"thread_search_error_league_{league_id}.png")
        return None

def get_player_by_phone_for_league(phone_number, league_id):
    """Get player name by phone number for a specific league"""
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Try to find player in the specified league
        cursor.execute("""
        SELECT name FROM players 
        WHERE phone_number = ? AND league_id = ?
        """, (phone_number, league_id))
        
        player = cursor.fetchone()
        
        if player:
            return player[0]
            
        # If not found, fallback to original lookup method for compatibility
        cursor.execute("SELECT name FROM players WHERE phone_number = ?", (phone_number,))
        player = cursor.fetchone()
        
        if player:
            logging.warning(f"Player {player[0]} ({phone_number}) found in default players table but not in league {league_id}")
            return player[0]
            
        return None
        
    except Exception as e:
        logging.error(f"Error finding player by phone: {e}")
        return None
    finally:
        if conn:
            conn.close()

def scroll_up_in_thread(driver, yesterday_wordle):
    """Scroll up in the conversation thread to load all messages including yesterday's Wordle scores.
    
    This function implements several scrolling strategies to ensure all messages are loaded:
    1. Fast scroll to top multiple times
    2. Slow incremental scrolling with checks for new content
    3. Explicit checks for messages containing yesterday's Wordle
    
    Args:
        driver: Selenium WebDriver instance
        yesterday_wordle: Yesterday's Wordle number to look for
    """
    logging.info(f"Starting advanced scrolling to load all messages including Wordle #{yesterday_wordle}")
    
    # Find the scrollable message container
    try:
        # Wait for the messages container to be present
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "gv-message-list"))
        )
        
        # Get the scrollable container
        message_container = driver.find_element(By.CSS_SELECTOR, "gv-message-list")
        
        # First strategy: Multiple rapid scrolls to the top to trigger loading
        logging.info("Strategy 1: Multiple rapid scrolls to top")
        for i in range(5):
            driver.execute_script("arguments[0].scrollTop = 0;", message_container)
            time.sleep(0.5)
        
        # Let the content load
        time.sleep(2)
        
        # Second strategy: Incremental scrolling with checks
        logging.info("Strategy 2: Incremental scrolling with content checks")
        
        # Get initial content height
        prev_content_height = driver.execute_script("return arguments[0].scrollHeight", message_container)
        
        # Try incremental scrolling with content checks
        max_scrolls = 10  # Limit scrolling attempts to avoid infinite loop
        for i in range(max_scrolls):
            # Scroll to top
            driver.execute_script("arguments[0].scrollTop = 0;", message_container)
            time.sleep(1)
            
            # Check if content height changed (new content loaded)
            current_height = driver.execute_script("return arguments[0].scrollHeight", message_container)
            
            if current_height <= prev_content_height:
                # If no new content after 2 consecutive attempts, we're likely at the top
                if i > 0:
                    logging.info(f"No new content loaded after scroll #{i+1}, assuming all content is loaded")
                    break
            else:
                logging.info(f"New content detected after scroll #{i+1} (height: {prev_content_height} → {current_height})")
            
            prev_content_height = current_height
        
        # Third strategy: Keyboard navigation to ensure focus is in the right place
        logging.info("Strategy 3: Using keyboard to ensure focus and additional scrolling")
        html_element = driver.find_element(By.TAG_NAME, "html")
        html_element.click()  # Ensure focus
        html_element.send_keys(Keys.HOME)  # Press Home key to go to top
        time.sleep(1)
        
        # Look for specific yesterday's Wordle number in page
        logging.info(f"Checking if messages containing Wordle #{yesterday_wordle} are visible")
        page_source = driver.page_source
        
        # Check for yesterday's Wordle with various formats
        wordle_patterns = [
            f"Wordle {yesterday_wordle}", 
            f"Wordle #{yesterday_wordle}",
            f"Wordle {yesterday_wordle:,}"  # Comma-formatted number
        ]
        
        if any(pattern in page_source for pattern in wordle_patterns):
            logging.info(f"Found messages containing yesterday's Wordle #{yesterday_wordle}")
        else:
            logging.warning(f"Could not find messages containing yesterday's Wordle #{yesterday_wordle} after scrolling")
            # One final aggressive scroll to top
            driver.execute_script("arguments[0].scrollTop = 0;", message_container)
            time.sleep(2)
        
        # Take a screenshot for verification
        try:
            driver.save_screenshot(f"conversation_loaded_{yesterday_wordle}.png")
            logging.info(f"Saved screenshot of loaded conversation to conversation_loaded_{yesterday_wordle}.png")
        except Exception as screenshot_error:
            logging.error(f"Error saving conversation screenshot: {screenshot_error}")
            
    except Exception as e:
        logging.error(f"Error during conversation scrolling: {e}")
        # Fallback: try a simple scroll if the container approach failed
        try:
            # Simple page scroll
            driver.execute_script("window.scrollTo(0, 0)")
            time.sleep(2)
        except Exception as scroll_error:
            logging.error(f"Fallback scrolling also failed: {scroll_error}")

def extract_player_name_from_phone(phone_number, league_id=1):
    """Extract player name from phone number for a specific league
    
    Args:
        phone_number: Phone number string to map to a player name
        league_id: League ID to check for player mapping
        
    Returns:
        str: Player name or None if not found
    """
    # Clean the phone number by removing Unicode directional characters
    if phone_number:
        # Remove Unicode directional characters (\u202a, \u202c, etc.)
        # and standardize phone number format
        cleaned_phone = ''
        for char in phone_number:
            if ord(char) < 128 and (char.isdigit() or char in '() -'):  # Only keep relevant ASCII characters
                cleaned_phone += char
        
        # Standardize format to just the digits for comparison
        digits = ''.join(c for c in cleaned_phone if c.isdigit())
        
        # For display, format to (xxx) xxx-xxxx if it's 10 digits
        if len(digits) == 10:
            display_number = f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
        elif len(digits) == 11 and digits[0] == '1':  # Handle US country code
            display_number = f"({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
        else:
            display_number = cleaned_phone.strip()
            
        logging.info(f"Cleaned phone number: '{display_number}' (digits: {digits})")
        
        # Return the digits-only version for comparison in the database lookup
        phone_number = digits
    
    # Try the database lookup first
    player_name = get_player_by_phone_for_league(phone_number, league_id)
    if player_name:
        logging.info(f"Found player {player_name} for phone {phone_number} in league {league_id}")
        return player_name

    # Fallback to the centralized phone mappings
    player_name = get_player_from_phone(phone_number, league_id)
    if player_name:
        logging.info(f"Found player {player_name} for phone {phone_number} in league {league_id} using centralized mappings")
        return player_name
    return None

def extract_player_name(conversation_text, league_id=1):
    """Extract player name from conversation for a specific league"""
    logging.info(f"Extracting player name from conversation for league {league_id}")
    
    # First try using phone_mappings.py for more accurate mapping
    try:
        name = extract_player_name_from_phone(conversation_text, league_id)
        if name:
            logging.info(f"Found player {name} using phone_mappings.py in league {league_id}")
            return name
    except Exception as e:
        logging.error(f"Error using extract_player_name_from_phone: {e}")
    
    # Fallback: try to find a phone number and map it to a name
    phone_pattern = re.compile(r'\(\d{3}\)\s*\d{3}-\d{4}')
    phone_matches = phone_pattern.findall(conversation_text)
    
    for phone in phone_matches:
        player_name = extract_player_name_from_phone(phone, league_id)
        if player_name:
            logging.info(f"Found player {player_name} for phone {phone} in league {league_id}")
            return player_name
    
    # Another attempt with a different phone format
    alt_phone_pattern = re.compile(r'\d{3}[\s\.-]?\d{3}[\s\.-]?\d{4}')
    alt_phone_matches = alt_phone_pattern.findall(conversation_text)
    
    for phone in alt_phone_matches:
        player_name = extract_player_name_from_phone(phone, league_id)
        if player_name:
            logging.info(f"Found player {player_name} for phone {phone} in league {league_id}")
            return player_name
    
    logging.warning(f"Could not extract player name from conversation in league {league_id}")
    return None


def capture_dom_snapshot(driver, filename):
    """Save a DOM snapshot to a file
    
    Args:
        driver: Selenium WebDriver instance
        filename: Name of file to save the DOM snapshot
    """
    try:
        # Create a directory for diagnostics if it doesn't exist
        os.makedirs("dom_captures", exist_ok=True)
        filepath = os.path.join("dom_captures", filename)
        
        # Get the page source and save it
        page_source = driver.page_source
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(page_source)
        logging.info(f"DOM snapshot saved to {filepath}")
    except Exception as e:
        logging.error(f"Error saving DOM snapshot: {e}")


def capture_hidden_elements(driver, filename):
    """Capture all .cdk-visually-hidden elements and save their text to a file
    
    Args:
        driver: Selenium WebDriver instance
        filename: Name of file to save the hidden elements
    """
    try:
        # Create a directory for diagnostics if it doesn't exist
        os.makedirs("dom_captures", exist_ok=True)
        filepath = os.path.join("dom_captures", filename)
        
        # First try to find gv-annotation elements with class='preview' (most reliable based on DOM structure)
        annotation_elements = driver.find_elements(By.CSS_SELECTOR, "gv-annotation.preview")
        logging.info(f"Found {len(annotation_elements)} gv-annotation.preview elements")
        
        # Also check aria-label attributes as they often contain the full text
        aria_elements = driver.find_elements(By.CSS_SELECTOR, "[aria-label*='Wordle']")
        logging.info(f"Found {len(aria_elements)} elements with Wordle in aria-label")
        
        # Combine our potential sources with most reliable first
        message_elements = annotation_elements + aria_elements
        
        # Fall back to traditional message elements if needed
        if not message_elements:
            message_elements = driver.find_elements(By.CSS_SELECTOR, ".message-item, gv-message-item")
            logging.info(f"Falling back to message-item elements: found {len(message_elements)} elements")
        logging.info(f"Found {len(message_elements)} message elements to capture in {filename}")
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Hidden elements capture - {datetime.now()}\n")
            f.write(f"Found {len(message_elements)} message elements\n\n")
            
            wordle_found = 0
            
            for i, element in enumerate(hidden_elements):
                try:
                    text = element.text.strip()
                    f.write(f"Element {i+1}:\n{text}\n")
                    f.write("-" * 50 + "\n\n")
                    
                    # Check if this is a Wordle score
                    if "Wordle" in text and ("/6" in text or "X/6" in text):
                        f.write(f"*** WORDLE SCORE FOUND ***\n\n")
                        logging.info(f"DIAGNOSTIC: Found Wordle score in element {i+1}: {text}")
                        wordle_found += 1
                except Exception as e:
                    f.write(f"Error getting text for element {i+1}: {e}\n")
            
            f.write(f"\nSummary: Found {wordle_found} elements containing Wordle scores")
        
        logging.info(f"Captured {len(hidden_elements)} hidden elements with {wordle_found} Wordle scores to {filepath}")
    except Exception as e:
        logging.error(f"Error capturing hidden elements: {e}")


def extract_all_current_scores(driver, today_wordle, yesterday_wordle, league_id, league_name):
    """Extract all currently visible scores during scrolling
    
    This function is called repeatedly during scrolling to capture scores that become
    visible at different scroll positions.
    
    Args:
        driver: Selenium WebDriver instance
        today_wordle: Today's Wordle number
        yesterday_wordle: Yesterday's Wordle number
        league_id: League ID for player mapping
        league_name: Name of the league for logging
    """
    logging.info(f"Extracting scores currently visible for {league_name}")
    
    try:
        # Find all visually hidden elements that might contain Wordle scores
        hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
        logging.info(f"Found {len(hidden_elements)} hidden elements in {league_name}")
        
        # Define today's Wordle as a string with and without commas for comparison
        today_wordle_str = f"Wordle {today_wordle}"
        today_wordle_comma_str = f"Wordle {today_wordle:,}"
        yesterday_wordle_str = f"Wordle {yesterday_wordle}"
        yesterday_wordle_comma_str = f"Wordle {yesterday_wordle:,}"
        
        logging.info(f"Looking for today's Wordle: '{today_wordle_str}' or '{today_wordle_comma_str}'")
        logging.info(f"Looking for yesterday's Wordle: '{yesterday_wordle_str}' or '{yesterday_wordle_comma_str}'")
        
        # Regular expressions to match Wordle scores
        wordle_regex = re.compile(r'Wordle ([\d,]+)(?: #([\d,]+)?)? ([1-6X])/6')
        
        scores_found = 0
        today_scores_found = 0
        
        for element in hidden_elements:
            try:
                text = element.text.strip()
                
                # Skip any reactions like "Loved" or "Liked" 
                if text.startswith("Loved ") or text.startswith("Liked ") or "reacted with" in text.lower() or "reacted to" in text.lower():
                    continue
                
                # Skip non-Wordle messages or ones without scores
                if not text.lstrip().startswith("Wordle") or ("/6" not in text and "X/6" not in text):
                    continue
                
                # Extract text from the "Message from" prefix through the end
                message_start = text.find("Message from")
                if message_start >= 0:
                    message_content = text[message_start:]
                    logging.info(f"Processing message: {message_content[:100]}...")
                else:
                    message_content = text
                
                # We'll validate the Wordle number after extracting it properly with regex
                
                # Now extract the Wordle details - need to be very precise here
                match = wordle_regex.search(message_content)
                if not match:
                    logging.debug(f"Regex didn't match despite Wordle text: {message_content[:50]}...")
                    continue
                    
                # Extract wordle number (handle commas)
                wordle_num_str = match.group(1)
                if wordle_num_str:
                    # Log the original string for debugging
                    logging.info(f"Found Wordle number string: '{wordle_num_str}'")
                    
                    # Remove commas and strictly convert to integer
                    cleaned_num_str = wordle_num_str.replace(',', '')
                    try:
                        wordle_num = int(cleaned_num_str)
                        logging.info(f"Converted to integer: {wordle_num}")
                    except ValueError:
                        logging.warning(f"Could not convert Wordle number to int: {wordle_num_str}")
                        continue
                else:
                    continue
                
                # Very strict checking of the Wordle number
                if wordle_num == today_wordle:
                    logging.info(f"VALIDATED: This is today's Wordle #{today_wordle}")
                elif wordle_num == yesterday_wordle:
                    logging.info(f"VALIDATED: This is yesterday's Wordle #{yesterday_wordle}")
                else:
                    logging.info(f"REJECTED: Wordle #{wordle_num} is neither today's ({today_wordle}) nor yesterday's ({yesterday_wordle})")
                    continue
                
                # Extract score
                score_str = match.group(3)
                if score_str == 'X':
                    score = 7  # X = 7 in our system
                else:
                    score = int(score_str)
                
                # Extract emoji pattern if available
                emoji_pattern = None
                if '\n' in message_content:
                    lines = message_content.split('\n')
                    # Look for emoji pattern in the next few lines after the Wordle score line
                    emoji_lines = []
                    in_emoji_pattern = False
                    
                    # Search through the lines to find and collect all emoji pattern lines
                    for i in range(1, min(len(lines), 15)):  # Extended range to catch all potential emoji lines
                        pattern_part = lines[i]
                        # Check for any of the Wordle emoji colors
                        if '🟩' in pattern_part or '⬛' in pattern_part or '⬜' in pattern_part or '🟨' in pattern_part:
                            emoji_lines.append(pattern_part)
                            in_emoji_pattern = True
                        elif in_emoji_pattern:
                            # If we've already found emoji lines and now hit a non-emoji line, stop
                            # This prevents collecting text that follows the emoji pattern
                            break
                    
                    # Join all emoji lines into a single pattern
                    if emoji_lines:
                        emoji_pattern = '\n'.join(emoji_lines)
                        logging.info(f"Extracted complete emoji pattern with {len(emoji_lines)} lines")
                
                # Find phone number for player mapping
                phone_match = re.search(r'Message from (\d[\s\d-]+\d)', message_content)
                phone = None
                
                if phone_match:
                    phone = phone_match.group(1)
                    phone = re.sub(r'[\s\-\(\)]+', '', phone)
                    if phone.startswith('+1'):
                        phone = phone[2:]  # Remove +1 country code
                else:
                    # Try alternate formats
                    phone_matches = re.findall(r'\((\d{3})\)[\s-]*(\d{3})[\s-]*(\d{4})', message_content)
                    if phone_matches:
                        phone = f"{phone_matches[0][0]}{phone_matches[0][1]}{phone_matches[0][2]}"
                
                if not phone:
                    logging.warning(f"Could not extract phone number from message")
                    continue
                    
                logging.info(f"Extracted phone: {phone} for Wordle {wordle_num}")
                
                # Get player name from phone number
                player = get_player_by_phone_for_league(phone, league_id)
                
                if player:
                    logging.info(f"Player {player} scored {score} on Wordle #{wordle_num} in {league_name}")
                    
                    # Save the score to database
                    result = save_score_to_db(player, wordle_num, score, emoji_pattern, league_id)
                    
                    if result == 'new':
                        scores_found += 1
                        if wordle_num == today_wordle:
                            today_scores_found += 1
                            logging.info(f"*** FOUND TODAY'S SCORE: {player} - Wordle #{wordle_num} - {score}/6 ***")
                        elif wordle_num == yesterday_wordle:
                            logging.info(f"Found yesterday's score: {player} - Wordle #{wordle_num} - {score}/6")
                    
                    logging.info(f"Score save result: {result} for {player} in {league_name}")
                else:
                    logging.warning(f"Could not identify player for phone {phone} in {league_name}")
            except Exception as elem_error:
                logging.error(f"Error processing element text in {league_name}: {elem_error}")
                continue
        
        logging.info(f"Found {scores_found} new scores total, {today_scores_found} new scores for today's Wordle #{today_wordle} in {league_name}")
        return scores_found
    
    except Exception as e:
        logging.error(f"Error extracting current scores from {league_name}: {e}")
        return 0


def extract_wordle_scores_multi_league():
    """Extract Wordle scores from multiple leagues
    
    Returns:
        bool: True if any scores were extracted, False otherwise
    """
    logging.info("Starting multi-league Wordle score extraction")
    
    driver = None
    any_scores_extracted = False
    
    try:
        # Set up Chrome driver
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Use existing Chrome profile to avoid login issues
        profile_path = os.path.join(os.getcwd(), "automation_profile")
        if os.path.exists(profile_path):
            chrome_options.add_argument(f"user-data-dir={profile_path}")
            logging.info(f"Using existing Chrome profile at {profile_path}")
        else:
            logging.warning(f"Chrome profile not found at {profile_path}")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # Extract scores from all leagues configured in LEAGUES list
        leagues_to_extract = [
            {"id": 1, "name": "Wordle Warriorz"},
            {"id": 2, "name": "Wordle Gang"},
            {"id": 3, "name": "PAL"},
            {"id": 4, "name": "Wordle Party"},
            {"id": 5, "name": "Wordle Vball"}
        ]
        
        for league in leagues_to_extract:
            league_id = league["id"]
            league_name = league["name"]
            
            logging.info(f"Starting extraction for {league_name} (league_id: {league_id})")
            
            # Use direct navigation to the correct thread by URL
            logging.info(f"Using direct URL navigation for {league_name} (league_id: {league_id})")
            
            # Navigate directly to thread using URL from league_config.json
            thread_navigation_success = navigate_to_thread_by_url(driver, league_id)
            
            if not thread_navigation_success:
                logging.warning(f"Failed to navigate to thread for {league_name} using direct URL")
                driver.save_screenshot(f"direct_nav_failed_{league_name.replace(' ', '_')}.png")
                continue
                
            # Take a screenshot of successfully loaded thread
            driver.save_screenshot(f"thread_loaded_{league_name.replace(' ', '_')}.png")
            logging.info(f"Successfully navigated to thread for {league_name}")
            
            # Wait for conversation to load completely
            time.sleep(3)
            
            # Extract scores
            try:
                hidden_scores = extract_with_hidden_elements(driver, league_id, league_name)
                logging.info(f"Hidden element extraction found {hidden_scores} scores")
                scores_extracted = hidden_scores
            except Exception as e:
                logging.error(f"Hidden element extraction failed: {e}")
                scores_extracted = 0
            
            if scores_extracted:
                logging.info(f"Successfully extracted scores from {league_name}")
                any_scores_extracted = True
            else:
                logging.warning(f"No scores extracted from {league_name}")
            
            # Take a screenshot after extraction
            driver.save_screenshot(f"after_extraction_{league_name.replace(' ', '_')}.png")
            
            logging.info(f"Completed extraction for {league_name}")
            
        # Return overall status after processing all leagues
        return any_scores_extracted
            
    except Exception as e:
        logging.error(f"Error in multi-league extraction: {str(e)}")
        if driver:
            driver.save_screenshot("multi_league_extraction_error.png")
        return False
        
    finally:
        # Clean up
        if driver:
            try:
                driver.quit()
            except:
                pass


# Execute the extraction when run directly
if __name__ == "__main__":
    logging.info("Starting Wordle score extraction for multiple leagues")
    try:
        # Run the extraction
        success = extract_wordle_scores_multi_league()
        
        if success:
            logging.info("Successfully extracted scores from one or more leagues")
        else:
            logging.warning("No scores extracted from any league")
            
    except Exception as e:
        logging.error(f"Error during execution: {e}")
        traceback.print_exc()