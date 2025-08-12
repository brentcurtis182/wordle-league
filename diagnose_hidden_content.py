"""
Diagnostic script to analyze hidden elements content in Google Voice threads.
This will help identify why PAL league scores aren't being extracted.
"""

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
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Get environment variables for login
GOOGLE_EMAIL = os.environ.get('GOOGLE_EMAIL')
GOOGLE_PASSWORD = os.environ.get('GOOGLE_PASSWORD')

if not GOOGLE_EMAIL or not GOOGLE_PASSWORD:
    logging.error("Environment variables GOOGLE_EMAIL and GOOGLE_PASSWORD must be set")
    exit(1)

def setup_driver():
    """Set up Chrome WebDriver with appropriate options"""
    chrome_options = Options()
    
    # Comment out headless mode for debugging
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def login_to_google_voice(driver):
    """Login to Google Voice using provided credentials"""
    logging.info("Navigating to Google Voice login")
    driver.get("https://voice.google.com/")
    
    try:
        # Wait for and enter email
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "identifierId"))
        )
        driver.find_element(By.ID, "identifierId").send_keys(GOOGLE_EMAIL)
        driver.find_element(By.ID, "identifierNext").click()
        
        # Wait for and enter password
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "password"))
        )
        time.sleep(1)  # Short delay to ensure password field is ready
        driver.find_element(By.NAME, "password").send_keys(GOOGLE_PASSWORD)
        driver.find_element(By.ID, "passwordNext").click()
        
        # Wait for Google Voice to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "gv-nav"))
        )
        
        logging.info("Successfully logged in to Google Voice")
        return True
    
    except TimeoutException as e:
        logging.error(f"Login timed out: {e}")
        driver.save_screenshot("login_timeout.png")
        return False
    
    except Exception as e:
        logging.error(f"Login failed: {e}")
        driver.save_screenshot("login_error.png")
        return False

def clean_phone_number(phone_number):
    """Clean and standardize phone number format to digits only"""
    if not phone_number:
        return None
    
    # Remove Unicode directional characters that can appear in phone numbers
    phone_number = re.sub(r'[\u200e\u200f\u202a\u202b\u202c\u202d\u202e]', '', phone_number)
    
    # Extract just the digits
    digits = re.sub(r'\D', '', phone_number)
    
    # If it starts with 1 and has 11 digits, keep it as is
    # Otherwise if it has 10 digits, it's a standard US number
    if len(digits) == 11 and digits.startswith('1'):
        return digits
    elif len(digits) == 10:
        return digits
    else:
        logging.warning(f"Unusual phone number format: {phone_number} -> {digits} (length: {len(digits)})")
        return digits

def examine_pal_league_thread(driver):
    """Navigate to PAL league thread and examine hidden elements"""
    logging.info("Navigating to messages page")
    driver.get("https://voice.google.com/messages")
    time.sleep(5)
    
    # Phone numbers that identify the PAL league thread
    pal_league_phones = ["(469) 834-5364", "(760) 420-6113", "(760) 583-0059", "(858) 735-9353"]
    
    try:
        # Wait for threads to be visible
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "gv-annotation.participants"))
        )
        
        # Get all conversation threads
        annotation_elements = driver.find_elements(By.CSS_SELECTOR, "gv-annotation.participants")
        logging.info(f"Found {len(annotation_elements)} conversation threads with annotations")
        
        # Find the PAL league thread
        pal_thread_found = False
        for i, annotation in enumerate(annotation_elements):
            try:
                annotation_text = annotation.get_attribute("textContent")
                logging.info(f"Thread {i+1} participants: {annotation_text}")
                
                # Check if this is the PAL league thread
                if any(phone in annotation_text for phone in pal_league_phones):
                    logging.info(f"Found PAL league thread at position {i+1}")
                    pal_thread_found = True
                    
                    # Find the parent conversation element to click
                    parent_element = annotation
                    for _ in range(3):  # Try going up 3 levels
                        parent_element = parent_element.find_element(By.XPATH, "..")
                    
                    # Click on the thread
                    logging.info("Clicking on PAL league conversation thread")
                    driver.execute_script("arguments[0].click();", parent_element)
                    time.sleep(3)
                    
                    # Now analyze the hidden elements
                    analyze_hidden_elements(driver)
                    break
            except Exception as e:
                logging.error(f"Error processing thread {i+1}: {e}")
                continue
        
        if not pal_thread_found:
            logging.error("Could not find PAL league thread")
    
    except Exception as e:
        logging.error(f"Error examining PAL league thread: {e}")
        driver.save_screenshot("pal_thread_error.png")

def analyze_hidden_elements(driver):
    """Analyze the content of hidden elements in the current thread"""
    logging.info("Looking for visually hidden elements")
    
    try:
        # Wait for hidden elements to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cdk-visually-hidden"))
        )
        
        # Get all hidden elements
        hidden_elements = driver.find_elements(By.CLASS_NAME, "cdk-visually-hidden")
        logging.info(f"Found {len(hidden_elements)} visually hidden elements")
        
        # Pattern to match Wordle results like "Wordle 789 3/6"
        wordle_pattern = re.compile(r'Wordle\s+(\d+)\s+([1-6]|X)/6')
        
        # Save full content for analysis
        with open("pal_hidden_elements.txt", "w", encoding="utf-8") as f:
            f.write(f"=== PAL League Hidden Elements Analysis ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===\n\n")
            f.write(f"Total elements found: {len(hidden_elements)}\n\n")
            
            for i, element in enumerate(hidden_elements):
                try:
                    text = element.text
                    f.write(f"=== Element {i+1} ===\n")
                    f.write(f"{text}\n\n")
                    
                    # Check for phone number
                    phone_match = re.search(r'(?:\+?1[-\s]?)?\(?([0-9]{3})\)?[-\s]?([0-9]{3})[-\s]?([0-9]{4})', text)
                    if phone_match:
                        f.write(f"Phone detected: {phone_match.group(0)}\n")
                        clean_phone = clean_phone_number(phone_match.group(0))
                        f.write(f"Cleaned phone: {clean_phone}\n\n")
                    
                    # Check for Wordle pattern
                    match = wordle_pattern.search(text)
                    if match:
                        f.write(f"WORDLE SCORE FOUND: Wordle {match.group(1)} {match.group(2)}/6\n\n")
                    
                    # Check for emoji pattern
                    if '⬛' in text or '⬜' in text or '🟨' in text or '🟩' in text:
                        f.write("EMOJI PATTERN DETECTED\n\n")
                
                except Exception as e:
                    f.write(f"Error processing element {i+1}: {str(e)}\n\n")
        
        logging.info(f"Analysis complete. Results saved to pal_hidden_elements.txt")
    
    except Exception as e:
        logging.error(f"Error analyzing hidden elements: {e}")
        driver.save_screenshot("hidden_elements_error.png")

def main():
    """Main execution function"""
    driver = setup_driver()
    try:
        if login_to_google_voice(driver):
            logging.info("Login successful. Examining PAL league thread.")
            examine_pal_league_thread(driver)
        else:
            logging.error("Failed to login to Google Voice. Cannot proceed.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
