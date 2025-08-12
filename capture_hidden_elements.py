"""
Script to capture and save all hidden elements from both league threads
to analyze what content we're actually finding in the DOM.

This will help us determine if there are really Wordle scores in the PAL thread
that our extraction is missing.
"""

import os
import time
import logging
import re
import json
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

# Get credentials from .env file using existing variable names
try:
    EMAIL_USERNAME = None
    EMAIL_PASSWORD = None
    
    # Load from .env file
    with open('.env', 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                try:
                    key, value = line.strip().split('=', 1)
                    if key == 'EMAIL_USERNAME':
                        EMAIL_USERNAME = value
                    elif key == 'EMAIL_PASSWORD':
                        EMAIL_PASSWORD = value
                except ValueError:
                    # Skip lines that don't have proper format
                    continue
    
    if not EMAIL_USERNAME or not EMAIL_PASSWORD:
        logging.error("Could not find EMAIL_USERNAME or EMAIL_PASSWORD in .env file")
        exit(1)
    
    logging.info(f"Using credentials from .env file: {EMAIL_USERNAME}")
    
    # Assign to variables used in script
    GOOGLE_EMAIL = EMAIL_USERNAME
    GOOGLE_PASSWORD = EMAIL_PASSWORD
    
except Exception as e:
    logging.error(f"Error loading .env file: {e}")
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

def examine_thread(driver, league_name, league_id, league_phones):
    """Navigate to thread and examine hidden elements"""
    logging.info(f"Examining {league_name} (ID: {league_id}) thread")
    
    driver.get("https://voice.google.com/messages")
    time.sleep(5)
    
    try:
        # Wait for threads to be visible
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "gv-annotation.participants"))
        )
        
        # Get all conversation threads
        annotation_elements = driver.find_elements(By.CSS_SELECTOR, "gv-annotation.participants")
        logging.info(f"Found {len(annotation_elements)} conversation threads with annotations")
        
        # Find the thread that matches this league
        thread_found = False
        for i, annotation in enumerate(annotation_elements):
            try:
                annotation_text = annotation.get_attribute("textContent")
                logging.info(f"Thread {i+1} participants: {annotation_text}")
                
                # Check if this thread belongs to current league
                is_match = any(phone in annotation_text for phone in league_phones)
                
                if not is_match:
                    continue
                
                logging.info(f"Found thread {i+1} for {league_name}")
                thread_found = True
                
                # Find the parent conversation element to click
                parent_element = annotation
                for _ in range(3):  # Try going up 3 levels
                    parent_element = parent_element.find_element(By.XPATH, "..")
                
                # Click on the thread
                logging.info(f"Clicking on {league_name} conversation thread")
                driver.execute_script("arguments[0].click();", parent_element)
                time.sleep(3)
                
                # Analyze hidden elements
                return analyze_hidden_elements(driver, league_name, league_id)
                
            except Exception as e:
                logging.error(f"Error processing thread {i+1}: {e}")
                continue
        
        if not thread_found:
            logging.error(f"Could not find {league_name} thread")
            return None
    
    except Exception as e:
        logging.error(f"Error examining {league_name} thread: {e}")
        driver.save_screenshot(f"{league_name.lower().replace(' ', '_')}_thread_error.png")
        return None

def analyze_hidden_elements(driver, league_name, league_id):
    """Analyze the content of hidden elements in the current thread and return the data"""
    logging.info(f"Looking for visually hidden elements in {league_name} thread")
    
    try:
        # Take screenshot of conversation
        driver.save_screenshot(f"{league_name.lower().replace(' ', '_')}_conversation.png")
        
        # Wait for hidden elements to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cdk-visually-hidden"))
        )
        
        # Get all hidden elements
        hidden_elements = driver.find_elements(By.CLASS_NAME, "cdk-visually-hidden")
        logging.info(f"Found {len(hidden_elements)} visually hidden elements in {league_name} thread")
        
        # Pattern to match Wordle results like "Wordle 789 3/6"
        wordle_pattern = re.compile(r'Wordle\s+(\d+)\s+([1-6]|X)/6')
        
        # Collect data for all elements
        elements_data = []
        
        for i, element in enumerate(hidden_elements):
            try:
                text = element.text
                element_data = {
                    "index": i,
                    "league": league_name,
                    "league_id": league_id,
                    "raw_text": text,
                    "contains_phone": False,
                    "contains_wordle": False,
                    "contains_emoji": False,
                    "phone_number": None,
                    "wordle_num": None,
                    "score": None,
                    "emoji_pattern": None
                }
                
                # Check for phone number
                phone_match = re.search(r'(?:\+?1[-\s]?)?\(?([0-9]{3})\)?[-\s]?([0-9]{3})[-\s]?([0-9]{4})', text)
                if phone_match:
                    element_data["contains_phone"] = True
                    element_data["phone_number"] = phone_match.group(0)
                    element_data["phone_digits"] = clean_phone_number(phone_match.group(0))
                
                # Check for Wordle pattern
                match = wordle_pattern.search(text)
                if match:
                    element_data["contains_wordle"] = True
                    element_data["wordle_num"] = match.group(1)
                    element_data["score"] = match.group(2)
                
                # Check for emoji pattern
                emoji_chars = ['\u2b1b', '\u2b1c', '\ud83d\udfe8', '\ud83d\udfe9']
                has_emoji = any(emoji in text for emoji in emoji_chars)
                if has_emoji:
                    element_data["contains_emoji"] = True
                    # Extract the emoji pattern
                    pattern_lines = []
                    for line in text.split('\n'):
                        if any(emoji in line for emoji in emoji_chars):
                            pattern_lines.append(line.strip())
                    if pattern_lines:
                        element_data["emoji_pattern"] = "\n".join(pattern_lines)
                
                elements_data.append(element_data)
            except Exception as e:
                logging.error(f"Error processing element {i+1}: {str(e)}")
        
        # Save to JSON file
        with open(f"{league_name.lower().replace(' ', '_')}_elements.json", "w", encoding="utf-8") as f:
            json.dump(elements_data, f, indent=2)
        
        # Save raw text for easier analysis
        with open(f"{league_name.lower().replace(' ', '_')}_elements.txt", "w", encoding="utf-8") as f:
            f.write(f"=== {league_name} Hidden Elements Analysis ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===\n\n")
            f.write(f"Total elements found: {len(hidden_elements)}\n\n")
            
            for i, element in enumerate(hidden_elements):
                try:
                    text = element.text
                    f.write(f"=== Element {i+1} ===\n")
                    f.write(f"{text}\n\n")
                except:
                    f.write(f"Error processing element {i+1}\n\n")
        
        # Summary of findings
        wordle_scores = [e for e in elements_data if e["contains_wordle"]]
        logging.info(f"Found {len(wordle_scores)} elements with Wordle scores in {league_name}")
        
        # Return the data
        return {
            "league_name": league_name,
            "league_id": league_id,
            "elements_count": len(hidden_elements),
            "wordle_scores_count": len(wordle_scores),
            "elements_data": elements_data
        }
    
    except Exception as e:
        logging.error(f"Error analyzing hidden elements in {league_name}: {e}")
        driver.save_screenshot(f"{league_name.lower().replace(' ', '_')}_elements_error.png")
        return None

def main():
    """Main execution function"""
    driver = setup_driver()
    
    # League definitions
    leagues = [
        {
            "name": "Wordle Warriorz",
            "id": 1,
            "phones": ["(310) 926-3555", "(760) 334-1190", "(949) 230-4472", "(858) 735-9353", "(760) 846-2302"]
        },
        {
            "name": "Wordle PAL",
            "id": 3,
            "phones": ["(469) 834-5364", "(760) 420-6113", "(760) 583-0059", "(858) 735-9353"]
        }
    ]
    
    results = {}
    
    try:
        if login_to_google_voice(driver):
            logging.info("Login successful. Examining threads.")
            
            # Process each league
            for league in leagues:
                league_result = examine_thread(
                    driver, 
                    league["name"], 
                    league["id"], 
                    league["phones"]
                )
                
                if league_result:
                    results[league["name"]] = league_result
                    
                    # Log summary stats
                    total = league_result["elements_count"]
                    scores = league_result["wordle_scores_count"]
                    logging.info(f"Summary for {league['name']}: {scores}/{total} elements contain Wordle scores")
                    
                    # Log some examples if available
                    wordle_examples = [e for e in league_result["elements_data"] if e["contains_wordle"]]
                    if wordle_examples:
                        logging.info("Examples of Wordle scores found:")
                        for i, example in enumerate(wordle_examples[:3]):  # Show up to 3 examples
                            logging.info(f"  {i+1}. Wordle {example['wordle_num']} {example['score']}/6")
                    else:
                        logging.info("No Wordle scores found in this league thread")
        else:
            logging.error("Failed to login to Google Voice. Cannot proceed.")
    finally:
        driver.quit()
    
    # Final comparison of leagues
    if len(results) == 2:
        main_league = results.get("Wordle Warriorz", {})
        pal_league = results.get("Wordle PAL", {})
        
        main_scores = main_league.get("wordle_scores_count", 0)
        pal_scores = pal_league.get("wordle_scores_count", 0)
        
        logging.info("\n=== Final Comparison ===")
        logging.info(f"Wordle Warriorz: {main_scores} scores found")
        logging.info(f"Wordle PAL: {pal_scores} scores found")
        
        if pal_scores == 0 and main_scores > 0:
            logging.info("DIAGNOSIS: There are no Wordle scores in the PAL league thread")
        elif pal_scores > 0:
            logging.info("DIAGNOSIS: There ARE Wordle scores in the PAL thread that aren't being extracted")

if __name__ == "__main__":
    main()
