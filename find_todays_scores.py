import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import re

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

def extract_wordle_scores():
    driver = None
    try:
        # Kill any existing Chrome processes
        logging.info("Attempting to kill any running Chrome processes")
        os.system("taskkill /f /im chrome.exe")
        time.sleep(0.1)
        logging.info("Chrome processes terminated")
        time.sleep(2)
        
        # Set up Chrome with profile
        profile_path = os.path.join(os.getcwd(), "automation_profile")
        logging.info(f"Using Chrome profile at: {profile_path}")
        
        # Configure Chrome options
        logging.info("Creating Chrome driver")
        chrome_options = Options()
        chrome_options.add_argument(f"user-data-dir={profile_path}")
        chrome_options.add_argument("--start-maximized")
        
        # Initialize driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to Google Voice
        voice_url = "https://voice.google.com/messages"
        logging.info(f"Navigating to Google Voice: {voice_url}")
        driver.get(voice_url)
        
        # Wait for Google Voice to load
        wait = WebDriverWait(driver, 20)
        wait.until(EC.url_contains("voice.google.com"))
        
        # Take screenshot for verification
        driver.save_screenshot("google_voice_navigation.png")
        logging.info("Screenshot saved to: google_voice_navigation.png")
        logging.info(f"Current URL: {driver.current_url}")
        
        if "voice.google.com" in driver.current_url:
            logging.info("Successfully navigated to Google Voice")
        else:
            logging.error(f"Navigation failed. Current URL: {driver.current_url}")
            return
            
        # Wait for conversation threads to load
        logging.info("Waiting for conversation threads to load")
        time.sleep(3)
        
        # Find threads using the selector that works in the main script
        thread_selectors = [
            "gv-thread-item",
            "div[role='row']",
            "div.gvThreadsList div"
        ]
        
        threads = []
        for selector in thread_selectors:
            threads = driver.find_elements(By.CSS_SELECTOR, selector)
            if threads:
                logging.info(f"Found {len(threads)} threads using selector: {selector}")
                break
        
        if not threads:
            logging.error("Could not find any conversation threads")
            return
            
        # Click on the first thread (Wordle Warriorz)
        logging.info("Clicking on first thread (Wordle Warriorz)")
        driver.execute_script("arguments[0].click();", threads[0])
        logging.info("Clicked on Wordle Warriorz thread")
        
        # Wait for thread to load
        time.sleep(5)
        
        # Find and print all hidden elements
        print("\n==== CHECKING WORDLE WARRIORZ THREAD ====")
        find_wordle_scores(driver)
        
        # Go back to the thread list
        back_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Back']")
        driver.execute_script("arguments[0].click();", back_button)
        logging.info("Clicked back button to return to thread list")
        time.sleep(3)
        
        # Refresh threads list
        for selector in thread_selectors:
            threads = driver.find_elements(By.CSS_SELECTOR, selector)
            if threads and len(threads) > 1:
                logging.info(f"Found {len(threads)} threads for second selection")
                break
        
        # Click on the second thread (PAL league)
        if len(threads) > 1:
            logging.info("Clicking on second thread (PAL)")
            driver.execute_script("arguments[0].click();", threads[1])
            logging.info("Clicked on PAL thread")
            
            # Wait for thread to load
            time.sleep(5)
            
            # Find and print all hidden elements
            print("\n==== CHECKING PAL THREAD ====")
            find_wordle_scores(driver)
        
    except Exception as e:
        logging.error(f"Error extracting scores: {e}")
    finally:
        if driver:
            driver.quit()
            logging.info("Chrome driver closed")

def find_wordle_scores(driver):
    try:
        # Scroll to load more messages
        scroll_container = driver.find_element(By.CSS_SELECTOR, "div[gv-id='conversation-scroll-container']")
        
        # Scroll repeatedly to ensure all messages are loaded
        logging.info("Scrolling to load all messages")
        scroll_count = 0
        max_scrolls = 15  # Increase number of scrolls
        
        # Scroll to top first
        driver.execute_script("arguments[0].scrollTop = 0", scroll_container)
        time.sleep(1)
        
        # Then scroll down repeatedly
        while scroll_count < max_scrolls:
            # Scroll up a bit then down to trigger loading more messages
            driver.execute_script("arguments[0].scrollTop -= 1000", scroll_container)
            time.sleep(0.5)
            driver.execute_script("arguments[0].scrollTop += 2000", scroll_container)
            time.sleep(0.5)
            scroll_count += 1
            logging.info(f"Scroll {scroll_count}/{max_scrolls}")
        
        # Find hidden elements containing Wordle scores
        hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
        logging.info(f"Found {len(hidden_elements)} hidden elements")
        
        # Extract and display scores
        found_1503 = False
        found_any = False
        
        print(f"\nFound {len(hidden_elements)} hidden DOM elements")
        
        for element in hidden_elements:
            text = element.text.strip()
            # Look for any Wordle scores
            if "Wordle" in text and ("/6" in text or "X/6" in text):
                found_any = True
                print(f"\n--- WORDLE SCORE FOUND ---")
                print(f"{text}")
                
                # Check if it's today's Wordle
                if "Wordle 1503" in text:
                    found_1503 = True
                    print("^^^ TODAY'S SCORE (WORDLE #1503) ^^^")
        
        if not found_1503:
            print("\nNo Wordle 1503 scores found in this conversation!")
            
        if not found_any:
            print("\nNo Wordle scores found at all in this conversation!")
            
    except Exception as e:
        logging.error(f"Error finding scores: {e}")

if __name__ == "__main__":
    print("Extracting Wordle scores from Google Voice...")
    extract_wordle_scores()
    print("\nDone!")
