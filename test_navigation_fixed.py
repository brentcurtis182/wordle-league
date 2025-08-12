#!/usr/bin/env python3
# Test script for Google Voice navigation with process cleanup
# This script first kills any Chrome processes, then tests navigation

import os
import sys
import time
import logging
import subprocess
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
        logging.FileHandler("test_navigation_fixed.log"),
        logging.StreamHandler()
    ]
)

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

def test_navigation():
    logging.info("Starting navigation test")
    
    # First kill any Chrome processes
    kill_chrome_processes()
    
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
        
        # Save screenshot with full path
        screenshot_path = os.path.join(os.getcwd(), "test1_google.png")
        driver.save_screenshot(screenshot_path)
        logging.info(f"Saved screenshot to: {screenshot_path}")
        
        # Test 2: Navigate to Google Voice
        logging.info("Test 2: Navigating to Google Voice")
        driver.get("https://voice.google.com/messages")
        time.sleep(8)
        logging.info(f"Current URL after Voice navigation: {driver.current_url}")
        
        # Save screenshot with full path
        screenshot_path = os.path.join(os.getcwd(), "test2_voice.png")
        driver.save_screenshot(screenshot_path)
        logging.info(f"Saved screenshot to: {screenshot_path}")
        
        # Save page source for analysis
        page_source_path = os.path.join(os.getcwd(), "test_page_source.html")
        with open(page_source_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logging.info(f"Saved page source for analysis to: {page_source_path}")
        
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
    print("\nTest completed. Please check test_navigation_fixed.log for details.")
    print("Screenshots have been saved to the current directory.")
