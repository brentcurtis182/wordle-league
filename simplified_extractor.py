import os
import time
import logging
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("simplified_extractor.log"),
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

def extract_scores():
    """Extract Wordle scores from Google Voice"""
    logging.info("Starting simplified extraction process")
    
    # Kill any running Chrome processes
    kill_chrome_processes()
    
    # Set up Chrome profile directory
    profile_dir = os.path.join(os.getcwd(), "automation_profile")
    logging.info(f"Using Chrome profile at: {profile_dir}")
    
    if not os.path.exists(profile_dir):
        logging.error(f"Profile directory does not exist: {profile_dir}")
        return False
    
    try:
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument(f"user-data-dir={profile_dir}")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Create Chrome driver
        logging.info("Creating Chrome driver")
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to Google Voice
        url = "https://voice.google.com/messages"
        logging.info(f"Navigating to Google Voice: {url}")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(10)
        
        # Take screenshot
        screenshot_path = os.path.join(os.getcwd(), "google_voice_navigation.png")
        driver.save_screenshot(screenshot_path)
        logging.info(f"Screenshot saved to: {screenshot_path}")
        
        # Get current URL
        current_url = driver.current_url
        logging.info(f"Current URL: {current_url}")
        
        # Check if we're on Google Voice
        if "voice.google.com" in current_url:
            logging.info("Successfully navigated to Google Voice")
            
            # Look for conversation list items
            try:
                logging.info("Looking for conversation list items")
                # Wait for conversation list to load
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "gv-conversation-list-item"))
                )
                
                # Find all conversation items
                conversation_items = driver.find_elements(By.CSS_SELECTOR, "gv-conversation-list-item")
                logging.info(f"Found {len(conversation_items)} conversation items")
                
                # Take another screenshot with conversation items
                driver.save_screenshot("conversations_found.png")
                logging.info("Screenshot saved with conversations")
                
                # Click on the first conversation
                if conversation_items:
                    logging.info("Clicking on first conversation")
                    conversation_items[0].click()
                    time.sleep(5)
                    
                    # Take screenshot of opened conversation
                    driver.save_screenshot("conversation_opened.png")
                    logging.info("Screenshot saved of opened conversation")
                    
                    # Get conversation text
                    conversation_text = driver.find_element(By.CSS_SELECTOR, "gv-message-list").text
                    logging.info(f"Conversation text: {conversation_text[:200]}...")  # Log first 200 chars
                    
                    # Look for Wordle patterns
                    if "Wordle" in conversation_text:
                        logging.info("Found Wordle content in conversation!")
                    else:
                        logging.info("No Wordle content found in this conversation")
                
            except Exception as e:
                logging.error(f"Error processing conversations: {e}")
        else:
            logging.error(f"Failed to navigate to Google Voice. Current URL: {current_url}")
        
        # Close the driver
        driver.quit()
        logging.info("Chrome driver closed")
        
        return True
    except Exception as e:
        logging.error(f"Error during extraction: {e}")
        return False

if __name__ == "__main__":
    extract_scores()
