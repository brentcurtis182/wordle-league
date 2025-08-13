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
        logging.info("Looking for conversation threads")
        time.sleep(2)
        
        # Find threads
        thread_containers = driver.find_elements(By.CSS_SELECTOR, "gv-thread-item")
        logging.info(f"Found {len(thread_containers)} conversation threads")
        
        # Find main Wordle Warriorz thread (usually the first one)
        main_thread = thread_containers[0]
        logging.info("Clicking on main Wordle Warriorz thread")
        
        # Click on thread
        driver.execute_script("arguments[0].click();", main_thread)
        logging.info("Clicked on thread")
        
        # Wait for thread to load
        time.sleep(5)
        
        # Scroll to load all messages
        scroll_container = driver.find_element(By.CSS_SELECTOR, "div[gv-id='conversation-scroll-container']")
        
        # Scroll repeatedly to ensure all messages are loaded
        logging.info("Scrolling to load all messages")
        scroll_count = 0
        max_scrolls = 10  # Adjust as needed
        
        while scroll_count < max_scrolls:
            driver.execute_script("arguments[0].scrollTop = 0", scroll_container)
            time.sleep(0.5)  # Pause between scrolls
            scroll_count += 1
            logging.info(f"Scroll {scroll_count}/{max_scrolls}")
        
        # Find hidden elements containing Wordle scores
        hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
        logging.info(f"Found {len(hidden_elements)} hidden elements")
        
        # Extract and display scores
        found_today = False
        
        for element in hidden_elements:
            text = element.text.strip()
            # Look for Wordle 1503 scores
            if "Wordle 1503" in text:
                found_today = True
                print(f"\nFOUND TODAY'S SCORE: {text}")
                # Extract phone number
                phone_match = re.search(r'\((\d{3})\) (\d{3})-(\d{4})', text)
                if phone_match:
                    phone = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"
                    print(f"Phone: {phone}")
                
                # Extract score
                score_match = re.search(r'(\d|X)/6', text)
                if score_match:
                    score = score_match.group(0)
                    print(f"Score: {score}")
                
                # Extract emoji pattern
                emoji_pattern = ""
                if "⬛" in text or "🟨" in text or "🟩" in text:
                    lines = text.split('\n')
                    for line in lines:
                        if "⬛" in line or "🟨" in line or "🟩" in line:
                            emoji_pattern += line + "\n"
                    print(f"Emoji Pattern:\n{emoji_pattern}")
        
        if not found_today:
            print("\nNo Wordle 1503 scores found in this conversation!")
            
            # Print some recent scores for context
            print("\nMost recent scores found:")
            count = 0
            for element in hidden_elements:
                text = element.text.strip()
                if "Wordle" in text and ("/6" in text or "X/6" in text):
                    print(f"\n{text[:200]}...")  # Print first 200 chars
                    count += 1
                    if count >= 3:  # Show only 3 most recent scores
                        break
        
    except Exception as e:
        logging.error(f"Error extracting scores: {e}")
    finally:
        if driver:
            driver.quit()
            logging.info("Chrome driver closed")

if __name__ == "__main__":
    print("Extracting Wordle scores from Google Voice...")
    extract_wordle_scores()
    print("\nDone!")
