#!/usr/bin/env python3
# Test script for Google Voice navigation
# This script tests navigation to Google Voice with detailed logging

import os
import sys
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_navigation.log"),
        logging.StreamHandler()
    ]
)

def test_navigation():
    logging.info("Starting navigation test")
    
    # Set up Chrome options with the pre-authenticated profile
    profile_dir = os.path.join(os.getcwd(), "automation_profile")
    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir)
        logging.info(f"Created profile directory: {profile_dir}")
    
    logging.info(f"Using Chrome profile at: {profile_dir}")
    
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(f"user-data-dir={profile_dir}")
    
    # Disable automation flags to prevent detection
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Add user agent
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
    
    try:
        # Create the driver
        logging.info("Creating Chrome driver")
        driver = webdriver.Chrome(options=chrome_options)
        logging.info("Chrome driver created successfully")
        
        # Test 1: Navigate to Google
        logging.info("Test 1: Navigating to Google")
        driver.get("https://www.google.com")
        time.sleep(3)
        logging.info(f"Current URL after Google navigation: {driver.current_url}")
        driver.save_screenshot("test1_google.png")
        
        # Test 2: Navigate to Google Voice
        logging.info("Test 2: Navigating to Google Voice")
        driver.get("https://voice.google.com/messages")
        time.sleep(8)
        logging.info(f"Current URL after Voice navigation: {driver.current_url}")
        driver.save_screenshot("test2_voice.png")
        
        # Test 3: Try JavaScript navigation
        logging.info("Test 3: Using JavaScript to navigate to Google Voice")
        driver.execute_script("window.location.href = 'https://voice.google.com/messages';")
        time.sleep(8)
        logging.info(f"Current URL after JS navigation: {driver.current_url}")
        driver.save_screenshot("test3_js_voice.png")
        
        # Test 4: Check if we can interact with the page
        logging.info("Test 4: Checking if we can interact with the page")
        try:
            # Wait for any element that would indicate we're on Google Voice
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Messages') or contains(text(), 'Calls') or contains(text(), 'Voicemail')]"))
            )
            logging.info("Found Google Voice elements on the page")
            driver.save_screenshot("test4_elements.png")
        except Exception as e:
            logging.error(f"Could not find Google Voice elements: {e}")
            driver.save_screenshot("test4_no_elements.png")
        
        # Save page source for analysis
        with open("test_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logging.info("Saved page source for analysis")
        
    except Exception as e:
        logging.error(f"Error during navigation test: {e}")
    finally:
        try:
            driver.quit()
            logging.info("Chrome driver closed")
        except:
            pass
        
    logging.info("Navigation test completed")

if __name__ == "__main__":
    test_navigation()
    print("\nTest completed. Please check test_navigation.log for details.")
    print("Screenshots have been saved to the current directory.")
