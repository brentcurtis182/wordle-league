#!/usr/bin/env python3
"""
Script to capture Google Voice DOM HTML for debugging score extraction issues.
Uses the same login process as the integrated_auto_update_multi_league.py script.
"""

import os
import sys
import time
import logging
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("google_voice_dom_capture.log"),
        logging.StreamHandler()
    ]
)

def kill_chrome_processes():
    """Kill any running Chrome processes"""
    logging.info("Attempting to kill any running Chrome processes")
    try:
        # For Windows
        import subprocess
        subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
        logging.info("Chrome processes terminated")
    except Exception as e:
        logging.error(f"Error killing Chrome processes: {e}")
    
    # Wait a moment for processes to fully terminate
    time.sleep(2)

def capture_google_voice_dom():
    """Capture Google Voice DOM HTML"""
    logging.info("Starting Google Voice DOM capture")
    
    # Kill any running Chrome processes
    kill_chrome_processes()
    
    # Set up Chrome profile directory - EXACTLY as in the integrated script
    profile_dir = os.path.join(os.getcwd(), "automation_profile")
    logging.info(f"Using Chrome profile at: {profile_dir}")
    
    if not os.path.exists(profile_dir):
        logging.error(f"Profile directory does not exist: {profile_dir}")
        return False
    
    driver = None
    try:
        # Set up Chrome options - EXACTLY as in the integrated script
        chrome_options = Options()
        chrome_options.add_argument(f"user-data-dir={profile_dir}")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Create Chrome driver
        logging.info("Creating Chrome driver")
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to Google Voice messages directly
        url = "https://voice.google.com/messages"
        logging.info(f"Navigating to Google Voice: {url}")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(10)
        
        # Take screenshot of the main messages page
        screenshot_path = os.path.join(os.getcwd(), "google_voice_messages.png")
        driver.save_screenshot(screenshot_path)
        logging.info(f"Screenshot of messages page saved to: {screenshot_path}")
        
        # Check if we're on Google Voice
        current_url = driver.current_url
        logging.info(f"Current URL: {current_url}")
        
        if "voice.google.com" not in current_url:
            logging.error(f"Failed to navigate to Google Voice. Current URL: {current_url}")
            return False
        
        # Save the main messages page HTML
        with open("google_voice_messages.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logging.info("Saved Google Voice messages page HTML")
        
        # Wait for conversation threads to be visible
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "gv-annotation.participants"))
            )
        except TimeoutException:
            logging.error("Conversation threads not found")
            return False
        
        # Get conversation threads
        annotation_elements = driver.find_elements(By.CSS_SELECTOR, "gv-annotation.participants")
        logging.info(f"Found {len(annotation_elements)} conversation threads with participant annotations")
        
        # Process first two conversation threads
        for i, annotation in enumerate(annotation_elements[:2]):
            try:
                # Get thread info before clicking
                thread_text = annotation.text
                logging.info(f"Thread {i+1}: {thread_text}")
                
                # Click on the conversation
                annotation.click()
                logging.info(f"Clicked on conversation thread {i+1}")
                
                # Wait for conversation to load
                time.sleep(5)
                
                # Take screenshot
                thread_screenshot = os.path.join(os.getcwd(), f"thread_{i+1}.png")
                driver.save_screenshot(thread_screenshot)
                logging.info(f"Screenshot saved for thread {i+1}")
                
                # Save HTML
                with open(f"thread_{i+1}.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                logging.info(f"Saved HTML for thread {i+1}")
                
                # Analyze the conversation DOM for debug purposes
                analyze_conversation_dom(driver.page_source, i+1)
                
                # Go back to the messages list
                driver.get("https://voice.google.com/messages")
                time.sleep(3)
                
                # Wait for thread list to reload
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "gv-annotation.participants"))
                )
                
                # Get fresh list of conversation threads
                annotation_elements = driver.find_elements(By.CSS_SELECTOR, "gv-annotation.participants")
                
            except Exception as e:
                logging.error(f"Error processing thread {i+1}: {e}")
                # Go back to messages in case of error
                driver.get("https://voice.google.com/messages")
                time.sleep(3)
        
        logging.info("Google Voice DOM capture completed successfully")
        return True
        
    except Exception as e:
        logging.error(f"Error capturing Google Voice DOM: {e}")
        return False
    
    finally:
        if driver:
            driver.quit()
            logging.info("WebDriver closed")

def analyze_conversation_dom(html, thread_num):
    """Analyze conversation DOM to find Wordle scores"""
    soup = BeautifulSoup(html, 'html.parser')
    
    logging.info(f"\n===== ANALYZING THREAD {thread_num} =====")
    
    # 1. Check for cdk-visually-hidden elements
    visually_hidden = soup.select('.cdk-visually-hidden')
    logging.info(f"Found {len(visually_hidden)} .cdk-visually-hidden elements")
    
    # Save all hidden elements to file for analysis
    with open(f"thread_{thread_num}_hidden_elements.txt", "w", encoding="utf-8") as f:
        f.write(f"===== THREAD {thread_num} HIDDEN ELEMENTS =====\n")
        for i, elem in enumerate(visually_hidden):
            f.write(f"\n--- Element {i+1} ---\n{elem.get_text()}\n")
            
            # Check for Wordle scores
            text = elem.get_text()
            if "Wordle" in text:
                f.write(f"*** CONTAINS WORDLE SCORE ***\n")
                logging.info(f"Found Wordle score in hidden element {i+1}")
                
                # Look for phone numbers in this element
                phone_match = re.search(r'(?:\+?1[-\s]?)?\(?([0-9]{3})\)?[-\s]?([0-9]{3})[-\s]?([0-9]{4})', text)
                if phone_match:
                    f.write(f"Phone number found: {phone_match.group(0)}\n")
                    logging.info(f"Found phone number in hidden element {i+1}: {phone_match.group(0)}")
                
                # Look for "Message from" pattern
                direct_phone_match = re.search(r'Message from ([0-9 ]+)', text)
                if direct_phone_match:
                    f.write(f"Direct phone found: {direct_phone_match.group(1)}\n")
                    logging.info(f"Found direct phone in hidden element {i+1}: {direct_phone_match.group(1)}")
                    
    # 2. Check for message-specific elements
    message_rows = soup.select('.message-row')
    logging.info(f"Found {len(message_rows)} message-row elements")
    
    with open(f"thread_{thread_num}_message_rows.txt", "w", encoding="utf-8") as f:
        f.write(f"===== THREAD {thread_num} MESSAGE ROWS =====\n")
        for i, row in enumerate(message_rows):
            f.write(f"\n--- Message {i+1} ---\n{row.get_text()}\n")
            
            # Check for Wordle scores
            text = row.get_text()
            if "Wordle" in text:
                f.write(f"*** CONTAINS WORDLE SCORE ***\n")
                logging.info(f"Found Wordle score in message row {i+1}")
    
    # 3. Extract all text nodes containing "Wordle" - most reliable
    all_text = soup.find_all(string=lambda s: "Wordle" in s if s else False)
    logging.info(f"Found {len(all_text)} text nodes containing 'Wordle'")
    
    with open(f"thread_{thread_num}_wordle_texts.txt", "w", encoding="utf-8") as f:
        f.write(f"===== THREAD {thread_num} WORDLE TEXT NODES =====\n")
        for i, text in enumerate(all_text):
            f.write(f"\n--- Wordle Text {i+1} ---\n{text}\n")
            
            # Find parent element
            parent = text.parent
            f.write(f"Parent element: {parent.name}, class: {parent.get('class', 'no-class')}\n")
            
            # Try to match wordle pattern with more flexible regex
            wordle_match = re.search(r'Wordle\s+(?:#)?([0-9,]+)\s+([1-6]|X)/6', text)
            if wordle_match:
                wordle_num = wordle_match.group(1)
                score_text = wordle_match.group(2)
                f.write(f"FOUND MATCH: Wordle {wordle_num} {score_text}/6\n")
                logging.info(f"MATCHED WORDLE: Wordle {wordle_num} {score_text}/6")

if __name__ == "__main__":
    capture_google_voice_dom()
