import os
import time
import logging
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("diagnose_vox_score.log")
    ]
)

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

def get_yesterdays_wordle_number():
    """Get yesterday's Wordle number"""
    return get_todays_wordle_number() - 1

def diagnose_vox_score():
    """Extract and diagnose Vox's Wordle score from Google Voice"""
    logging.info("Starting Vox score diagnosis")
    
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
        
        # Navigate to Google Voice messages directly
        url = "https://voice.google.com/messages"
        logging.info(f"Navigating to Google Voice: {url}")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(10)
        
        # Take screenshot
        screenshot_path = os.path.join(os.getcwd(), "diagnose_vox_navigation.png")
        driver.save_screenshot(screenshot_path)
        logging.info(f"Screenshot saved to: {screenshot_path}")
        
        # Wait for conversation threads to load
        logging.info("Waiting for conversation threads to load")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "gv-thread-list-item .container[role='button']"))
        )
        
        # Find clickable conversation threads
        threads = driver.find_elements(By.CSS_SELECTOR, "gv-thread-list-item .container[role='button']")
        logging.info(f"Found {len(threads)} conversation threads")
        
        # Get today's and yesterday's Wordle numbers
        today_wordle = get_todays_wordle_number()
        yesterday_wordle = get_yesterdays_wordle_number()
        logging.info(f"Today's Wordle: #{today_wordle}, Yesterday's Wordle: #{yesterday_wordle}")
        
        # PAL league phone numbers
        pal_league_phones = ["(858) 735-9353", "(469) 834-5364", "(760) 420-6113", "(760) 583-0059"]
        
        # Search for PAL league thread
        pal_thread_found = False
        for thread in threads:
            try:
                # Try to get text that might contain PAL league numbers
                thread_text = thread.text
                
                # Look for any PAL league phone number in this thread
                for phone in pal_league_phones:
                    if phone in thread_text:
                        logging.info(f"Found PAL league thread with phone: {phone}")
                        logging.info(f"Thread text preview: {thread_text[:100]}...")
                        pal_thread_found = True
                        
                        # Click this thread
                        logging.info("Clicking PAL thread to open conversation")
                        thread.click()
                        time.sleep(5)
                        
                        # Take screenshot after clicking thread
                        screenshot_path = os.path.join(os.getcwd(), "pal_thread_clicked.png")
                        driver.save_screenshot(screenshot_path)
                        
                        # Now extract all hidden elements to find Vox's score
                        hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
                        logging.info(f"Found {len(hidden_elements)} hidden elements in PAL thread")
                        
                        # Log the raw content of all elements that mention Vox or the phone number (858) 735-9353
                        vox_elements_found = 0
                        for i, element in enumerate(hidden_elements):
                            try:
                                text = element.text.strip()
                                
                                # Only process if it contains Vox's number or looks like a Wordle score
                                if "(858) 735-9353" in text or "Vox" in text or (text.lstrip().startswith("Wordle") and ("/6" in text or "X/6" in text)):
                                    vox_elements_found += 1
                                    
                                    # Log the COMPLETE raw element text
                                    logging.info(f"ELEMENT {i+1} RAW TEXT:")
                                    logging.info("=" * 80)
                                    logging.info(text)
                                    logging.info("=" * 80)
                                    
                                    # Try to extract Wordle number and score
                                    wordle_regex = re.compile(r'Wordle ([\\d,]+)(?: #([\\d,]+)?)? ([1-6X])/6')
                                    match = wordle_regex.search(text)
                                    
                                    if match:
                                        wordle_num_str = match.group(1)
                                        wordle_num_str = wordle_num_str.replace(',', '')
                                        try:
                                            wordle_num = int(wordle_num_str)
                                            score_str = match.group(3)
                                            
                                            # Identify if this is today's or yesterday's Wordle
                                            if wordle_num == today_wordle:
                                                logging.info(f"*** FOUND TODAY'S WORDLE #{today_wordle} - Score: {score_str}/6 ***")
                                            elif wordle_num == yesterday_wordle:
                                                logging.info(f"*** FOUND YESTERDAY'S WORDLE #{yesterday_wordle} - Score: {score_str}/6 ***")
                                            else:
                                                logging.info(f"*** FOUND OTHER WORDLE #{wordle_num} - Score: {score_str}/6 ***")
                                        except ValueError:
                                            logging.warning(f"Could not convert Wordle number to int: {wordle_num_str}")
                            except Exception as e:
                                logging.error(f"Error processing element {i+1}: {e}")
                        
                        if vox_elements_found == 0:
                            logging.warning("No elements found containing Vox or Wordle scores!")
                        
                        break  # Stop after processing the PAL thread
                
                if pal_thread_found:
                    break
            
            except Exception as e:
                logging.error(f"Error processing thread: {e}")
                continue
        
        if not pal_thread_found:
            logging.error("Could not find PAL league thread!")
        
        logging.info("Diagnosis complete")
        
    except Exception as e:
        logging.error(f"Error during diagnosis: {e}")
        return False
    finally:
        # Close the browser
        try:
            driver.quit()
        except:
            pass
    
    return True

if __name__ == "__main__":
    diagnose_vox_score()
