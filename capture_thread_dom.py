#!/usr/bin/env python3
# Diagnostic script to open threads and capture DOM elements

import os
import sys
import time
import logging
import re
import json
import subprocess
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("capture_thread_dom.log"),
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
        "league_id": 3, 
        "name": "Wordle PAL",
        "is_default": False
    }
]

def get_todays_wordle_number():
    """Get today's Wordle number dynamically based on the current date"""
    # Wordle #1 was released on June 19, 2021
    wordle_start_date = datetime(2021, 6, 19).date()
    today = datetime.now().date()
    
    # Calculate days between start date and today
    days_since_start = (today - wordle_start_date).days
    
    # Wordle number is days since start + 1
    wordle_number = days_since_start + 1
    logging.info(f"Calculated today's Wordle #{wordle_number} for date {today}")
    
    return wordle_number

def capture_thread_elements():
    """Open threads and capture DOM elements for diagnostic purposes"""
    
    logging.info("Starting thread DOM capture")
    
    # Get today's Wordle number for reference
    today_wordle = get_todays_wordle_number()
    logging.info(f"Looking for Wordle #{today_wordle} scores")
    
    # Chrome driver setup with persistent profile
    chrome_options = Options()
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Use a dedicated profile for automation
    chrome_options.add_argument("user-data-dir=./automation_profile")
    
    # Initialize Chrome driver
    logging.info("Initializing Chrome driver with persistent profile")
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Set implicit wait for elements
        driver.implicitly_wait(5)
        
        # Navigate to Google Voice
        driver.get("https://voice.google.com")
        logging.info("Navigated to Google Voice")
        
        # Wait for the page to load
        time.sleep(3)
        
        # Ensure we're logged in by checking for "Google Voice" text
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Google Voice')]"))
            )
            logging.info("Successfully logged into Google Voice")
        except TimeoutException:
            logging.error("Not logged into Google Voice, please ensure your automation_profile has valid credentials")
            driver.save_screenshot("login_error.png")
            return False
        
        # Go to messages
        driver.get("https://voice.google.com/messages")
        logging.info("Navigated to messages page")
        time.sleep(5)
        
        # Phone number patterns that identify each league
        main_league_phones = ["(310) 926-3555", "(760) 334-1190", "(949) 230-4472", "(858) 735-9353", "(760) 846-2302"]
        # Make sure PAL league phones includes Vox's number (858) 735-9353 as a priority
        pal_league_phones = ["(858) 735-9353", "(469) 834-5364", "(760) 420-6113", "(760) 583-0059"]
        
        # Process one league at a time
        for league in LEAGUES:
            league_id = league['league_id']
            league_name = league['name']
            
            logging.info(f"Processing league: {league_name} (ID: {league_id})")
            
            # Make sure we're on the messages page
            driver.get("https://voice.google.com/messages")
            time.sleep(5)
            
            try:
                # Wait for threads to be visible
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "gv-annotation.participants"))
                )
                
                # Find clickable conversation threads
                logging.info("Searching for thread container elements...")
                threads = driver.find_elements(By.CSS_SELECTOR, "gv-thread-list-item .container[role='button']")
                
                # Fallback to alternate selectors if needed
                if not threads:
                    logging.info("No threads found with primary selector, trying alternates...")
                    alternate_selectors = [
                        "div[shifthover][matripple].container[role='button']", 
                        "gv-annotation.participants",
                        ".item.thread", 
                        ".thread-list .thread"
                    ]
                    for selector in alternate_selectors:
                        threads = driver.find_elements(By.CSS_SELECTOR, selector)
                        if threads:
                            logging.info(f"Found {len(threads)} threads with alternate selector: {selector}")
                            break
                
                logging.info(f"Found {len(threads)} conversation threads")
                
                # Find the thread that matches this league
                thread_found = False
                for i, current_thread in enumerate(threads):
                    try:
                        # Take screenshot before processing
                        driver.save_screenshot(f"{league_name.lower().replace(' ', '_')}_thread_{i+1}_before.png")
                        
                        # Try to get the thread participants
                        try:
                            # First check if we can find a participants annotation inside this thread
                            participant_elements = current_thread.find_elements(By.CSS_SELECTOR, "gv-annotation.participants")
                            if participant_elements:
                                annotation_text = participant_elements[0].text
                                logging.info(f"Thread {i+1} participants (from annotation): {annotation_text}")
                            else:
                                # Fallback to using the thread container's text
                                annotation_text = current_thread.text
                                logging.info(f"Thread {i+1} participants (from container): {annotation_text}")
                            
                            # Check if this thread belongs to current league
                            is_match = False
                            if league_id == 3:  # PAL league
                                is_match = any(phone in annotation_text for phone in pal_league_phones)
                            elif league_id == 1:  # Main league
                                is_match = any(phone in annotation_text for phone in main_league_phones)
                            
                            if not is_match:
                                continue
                            
                        except Exception as e:
                            logging.error(f"Failed to get thread text: {e}")
                            continue
                        
                        logging.info(f"Found thread {i+1} for {league_name} (ID: {league_id})")
                        thread_found = True
                        
                        # Try multiple click methods to ensure reliability
                        click_success = False
                        
                        # Method 1: Using JavaScript click on the container element
                        try:
                            driver.execute_script("arguments[0].click();", current_thread)
                            logging.info(f"Clicked on {league_name} thread using JavaScript method 1")
                            click_success = True
                        except Exception as e:
                            logging.error(f"Failed to click with JavaScript method 1: {e}")
                        
                        # Method 2: Click on any participant annotation inside (if not already clicked)
                        if not click_success:
                            try:
                                if participant_elements:
                                    driver.execute_script("arguments[0].click();", participant_elements[0])
                                    logging.info(f"Clicked on {league_name} thread's participant annotation")
                                    click_success = True
                            except Exception as e:
                                logging.error(f"Failed to click participant annotation: {e}")
                        
                        # Method 3: Regular Selenium click as fallback
                        if not click_success:
                            try:
                                current_thread.click()
                                logging.info(f"Clicked on {league_name} thread using regular click")
                                click_success = True
                            except Exception as e:
                                logging.error(f"Failed with regular click: {e}")
                        
                        # Check if click was successful by looking for conversation container
                        try:
                            # Wait for conversation container to appear
                            WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "div[gv-id='conversation-scroll-container']"))
                            )
                            logging.info("Conversation container found after click")
                        except TimeoutException:
                            logging.error("Conversation container not found after click")
                            driver.save_screenshot(f"{league_name.lower().replace(' ', '_')}_click_failed.png")
                            continue
                        
                        # Take a screenshot after clicking
                        driver.save_screenshot(f"{league_name.lower().replace(' ', '_')}_thread_opened.png")
                        
                        # Wait a moment for content to load
                        time.sleep(2)
                        
                        # IMPLEMENT AGGRESSIVE OSCILLATING SCROLL PATTERN
                        logging.info("Starting aggressive oscillating scroll pattern")
                        try:
                            # Find the scroll container
                            scroll_container = driver.find_element(By.CSS_SELECTOR, "div[gv-id='conversation-scroll-container']")
                            
                            # Initial scroll to top
                            driver.execute_script("arguments[0].scrollTop = 0", scroll_container)
                            time.sleep(1)
                            
                            # Aggressive oscillating scroll pattern
                            scroll_count = 0
                            max_scrolls = 15
                            
                            while scroll_count < max_scrolls:
                                # Log current scroll iteration
                                logging.info(f"Scroll iteration {scroll_count+1}/{max_scrolls}")
                                
                                # Scroll up (negative value means going up)
                                driver.execute_script("arguments[0].scrollTop -= 1000", scroll_container)
                                time.sleep(0.5)
                                
                                # Capture elements during scroll-up
                                if scroll_count % 2 == 0:
                                    capture_hidden_elements(driver, league_name, f"scroll_{scroll_count+1}_up")
                                
                                # Scroll down (positive value means going down)
                                driver.execute_script("arguments[0].scrollTop += 2000", scroll_container)
                                time.sleep(0.5)
                                
                                # Capture elements during scroll-down
                                capture_hidden_elements(driver, league_name, f"scroll_{scroll_count+1}_down")
                                
                                scroll_count += 1
                            
                            # Final capture after scrolling completes
                            capture_hidden_elements(driver, league_name, "final")
                            
                        except Exception as e:
                            logging.error(f"Error during scrolling: {e}")
                            
                        # Take another screenshot after scrolling
                        driver.save_screenshot(f"{league_name.lower().replace(' ', '_')}_after_scroll.png")
                        
                    except Exception as e:
                        logging.error(f"Error processing thread {i+1}: {e}")
                
                if not thread_found:
                    logging.warning(f"No thread found for {league_name}")
                
            except Exception as e:
                logging.error(f"Error processing league {league_name}: {e}")
        
        logging.info("Thread DOM capture completed")
        return True
    
    except Exception as e:
        logging.error(f"Error in capture_thread_elements: {e}")
        driver.save_screenshot("capture_error.png")
        return False
    
    finally:
        # Close the driver
        driver.quit()

def capture_hidden_elements(driver, league_name, capture_id):
    """Capture .cdk-visually-hidden elements and save to a file"""
    try:
        hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
        logging.info(f"Found {len(hidden_elements)} hidden elements during {capture_id}")
        
        # Create a results directory if it doesn't exist
        results_dir = "thread_capture_results"
        os.makedirs(results_dir, exist_ok=True)
        
        # Create a file to store the element texts
        filename = f"{results_dir}/{league_name.lower().replace(' ', '_')}_{capture_id}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"Capture for {league_name} - {capture_id}\n")
            f.write(f"Found {len(hidden_elements)} hidden elements\n\n")
            
            for i, element in enumerate(hidden_elements):
                try:
                    text = element.text.strip()
                    f.write(f"Element {i+1}:\n{text}\n")
                    f.write("-" * 50 + "\n\n")
                    
                    # Log if this looks like a Wordle score
                    if "Wordle" in text and ("/6" in text or "X/6" in text):
                        logging.info(f"Found Wordle score during {capture_id}: {text}")
                        
                except Exception as e:
                    f.write(f"Error getting text for element {i+1}: {e}\n")
        
        # Also save the page source at this point
        page_source_filename = f"{results_dir}/{league_name.lower().replace(' ', '_')}_{capture_id}_page_source.html"
        with open(page_source_filename, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
            
        logging.info(f"Saved element capture to {filename} and page source to {page_source_filename}")
        
    except Exception as e:
        logging.error(f"Error capturing hidden elements: {e}")

if __name__ == "__main__":
    capture_thread_elements()
