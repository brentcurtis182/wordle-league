import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='extract_1503.log'
)

# Add console handler to see logs in real-time
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# League configurations
LEAGUES = [
    {
        'id': 1,
        'name': 'Wordle Warriorz',
        'phone_numbers': ['16193843994'],
        'player_mapping': {
            '16504414253': 'Brent',
            '14089691657': 'Evan',
            '14158070323': 'Joanna',
            '19254519643': 'Malia',
            '18184074444': 'Nanna'
        }
    },
    {
        'id': 3,
        'name': 'Wordle PAL',
        'phone_numbers': ['17608462302'],
        'player_mapping': {
            '17608462302': 'Vox'
        }
    }
]

def extract_todays_wordle_scores():
    driver = None
    try:
        # Set up Chrome with profile
        profile_path = os.path.join(os.getcwd(), "automation_profile")
        logging.info(f"Using Chrome profile at: {profile_path}")
        
        # Configure Chrome options
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
        
        # Process each league
        for league in LEAGUES:
            league_id = league['id']
            league_name = league['name']
            
            logging.info(f"Processing {league_name} (ID: {league_id})")
            
            for phone_number in league['phone_numbers']:
                logging.info(f"Processing thread with phone: {phone_number}")
                
                # Find thread by phone number
                try:
                    # Look for thread with different selectors
                    thread_found = False
                    
                    # Try finding thread by xpath containing phone number
                    try:
                        thread_xpath = f"//div[contains(., '{phone_number}')]"
                        thread = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, thread_xpath))
                        )
                        thread.click()
                        thread_found = True
                        logging.info(f"Found and clicked thread with phone: {phone_number}")
                    except Exception as e:
                        logging.warning(f"Failed to find thread by xpath: {e}")
                    
                    # If not found by xpath, try with CSS selector
                    if not thread_found:
                        try:
                            thread_selectors = [
                                "gv-thread-item",
                                "div[role='row']",
                                ".thread-item"
                            ]
                            
                            for selector in thread_selectors:
                                threads = driver.find_elements(By.CSS_SELECTOR, selector)
                                if threads:
                                    logging.info(f"Found {len(threads)} threads using selector: {selector}")
                                    # Click the first thread
                                    driver.execute_script("arguments[0].click();", threads[0])
                                    thread_found = True
                                    logging.info(f"Clicked on thread for {league_name}")
                                    break
                        except Exception as e:
                            logging.warning(f"Failed to find thread by CSS selector: {e}")
                    
                    if not thread_found:
                        logging.error(f"Could not find thread for {phone_number}")
                        continue
                    
                    # Wait for thread to load
                    time.sleep(5)
                    
                    # Find scroll container with different possible selectors
                    scroll_selectors = [
                        "div[gv-id='conversation-scroll-container']",
                        ".message-list-container",
                        "gv-message-list"
                    ]
                    
                    scroll_container = None
                    for selector in scroll_selectors:
                        try:
                            scroll_container = driver.find_element(By.CSS_SELECTOR, selector)
                            logging.info(f"Found scroll container with selector: {selector}")
                            break
                        except NoSuchElementException:
                            continue
                    
                    if not scroll_container:
                        logging.error("Could not find scroll container")
                        # Try to go back to thread list
                        try:
                            back_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Back'], button.back-button, gv-icon-button[icon-name='arrow_back']")
                            if back_buttons:
                                back_buttons[0].click()
                                time.sleep(3)
                        except:
                            driver.get(voice_url)
                            time.sleep(3)
                        continue
                    
                    # Scroll using the dynamic approach that worked before
                    logging.info("Starting scrolling sequence")
                    
                    # First scroll to top to ensure we start from the beginning
                    driver.execute_script("arguments[0].scrollTop = 0", scroll_container)
                    time.sleep(1)
                    
                    # Save HTML before scrolling for comparison
                    before_html = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
                    before_count = len(before_html)
                    logging.info(f"Found {before_count} hidden elements before scrolling")
                    
                    # Perform oscillating scroll pattern that worked previously
                    max_scrolls = 20  # Increase number of scrolls
                    for i in range(max_scrolls):
                        # Scroll up a bit then down to trigger loading more messages
                        driver.execute_script("arguments[0].scrollTop -= 1000", scroll_container)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].scrollTop += 2000", scroll_container)
                        time.sleep(0.5)
                        logging.info(f"Scroll {i+1}/{max_scrolls}")
                    
                    # Additional scrolls to top to ensure all content is loaded
                    for i in range(3):
                        driver.execute_script("arguments[0].scrollTop = 0", scroll_container)
                        time.sleep(1)
                    
                    # Save HTML after scrolling to file for debugging
                    with open(f"conversation_{league_id}_full.html", "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    logging.info(f"Saved full HTML to conversation_{league_id}_full.html")
                    
                    # Find hidden elements containing Wordle scores
                    hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
                    after_count = len(hidden_elements)
                    logging.info(f"Found {after_count} hidden elements after scrolling (added {after_count - before_count})")
                    
                    # Extract and display scores
                    found_1503 = False
                    scores_found = []
                    
                    print(f"\n========== {league_name} ==========")
                    
                    for element in hidden_elements:
                        try:
                            text = element.text.strip()
                            # Look for any Wordle scores
                            if "Wordle" in text and ("/6" in text or "X/6" in text):
                                # Extract wordle number and score
                                wordle_match = re.search(r'Wordle\s+([0-9,]+)\s+([X0-9])/6', text)
                                if wordle_match:
                                    wordle_num = wordle_match.group(1).replace(',', '')
                                    score = wordle_match.group(2)
                                    
                                    # Extract phone number if present
                                    phone_match = re.search(r'(\d{3}) (\d{3}) (\d{4})', text)
                                    phone_number = None
                                    if phone_match:
                                        phone_number = ''.join(phone_match.groups())
                                    
                                    # Get player name
                                    player_name = "Unknown"
                                    if phone_number and phone_number in league['player_mapping']:
                                        player_name = league['player_mapping'][phone_number]
                                    
                                    # Format score
                                    score_text = score
                                    if score == 'X':
                                        score = 7  # Convert X to 7 for failed attempts
                                    else:
                                        score = int(score)
                                    
                                    # Extract emoji pattern
                                    pattern_lines = []
                                    lines = text.split('\n')
                                    for line in lines:
                                        if '⬛' in line or '🟩' in line or '🟨' in line or '⬜' in line:
                                            pattern_lines.append(line)
                                    
                                    emoji_pattern = '\n'.join(pattern_lines) if pattern_lines else "No pattern"
                                    
                                    # Record the score
                                    scores_found.append({
                                        'wordle_num': wordle_num,
                                        'player': player_name,
                                        'score': score,
                                        'score_text': score_text,
                                        'pattern': emoji_pattern,
                                        'phone': phone_number,
                                        'league_id': league_id
                                    })
                                    
                                    # Check if it's today's Wordle
                                    if wordle_num == '1503':
                                        found_1503 = True
                        except Exception as e:
                            logging.error(f"Error processing element: {e}")
                    
                    # Display found scores
                    if scores_found:
                        # Sort by Wordle number (descending)
                        scores_found.sort(key=lambda x: int(x['wordle_num']), reverse=True)
                        
                        # Display scores
                        for score in scores_found:
                            print(f"\n--- Wordle #{score['wordle_num']} ---")
                            print(f"Player: {score['player']} ({score['phone'] or 'No phone'})")
                            print(f"Score: {score['score_text']}/6")
                            print(f"Pattern:\n{score['pattern']}")
                            
                            if score['wordle_num'] == '1503':
                                print("^^^ TODAY'S WORDLE #1503 SCORE ^^^")
                        
                        # Summary
                        print(f"\nFound {len(scores_found)} scores in {league_name}")
                        if found_1503:
                            print(f"TODAY'S WORDLE #1503 SCORES WERE FOUND!")
                        else:
                            print(f"No Wordle #1503 scores found in {league_name}")
                    else:
                        print(f"No Wordle scores found in {league_name}")
                    
                    # Go back to thread list
                    try:
                        back_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Back'], button.back-button, gv-icon-button[icon-name='arrow_back']")
                        if back_buttons:
                            back_buttons[0].click()
                            logging.info("Clicked back button")
                            time.sleep(3)
                        else:
                            logging.warning("Back button not found, navigating directly")
                            driver.get(voice_url)
                            time.sleep(3)
                    except Exception as e:
                        logging.error(f"Error going back to thread list: {e}")
                        driver.get(voice_url)
                        time.sleep(3)
                
                except Exception as e:
                    logging.error(f"Error processing league {league_name}: {e}")
                    # Try to get back to the main page
                    driver.get(voice_url)
                    time.sleep(3)
        
        logging.info("Extraction completed")
                
    except Exception as e:
        logging.error(f"Error extracting scores: {e}")
    finally:
        if driver:
            driver.quit()
            logging.info("Chrome driver closed")

if __name__ == "__main__":
    print("Extracting Wordle #1503 scores from Google Voice...")
    extract_todays_wordle_scores()
    print("\nDone! Check extract_1503.log for details")
