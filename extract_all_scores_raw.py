from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import re
import os

# League 1: Wordle Warriorz
PHONE_NUMBERS_1 = ["16193843994"]
# League 3: PAL
PHONE_NUMBERS_3 = ["17608462302"]

def extract_all_scores_raw():
    # Set up Chrome with existing profile
    chrome_options = Options()
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--window-size=1280,800")
    chrome_options.add_argument("--user-data-dir=" + os.path.abspath("automation_profile"))
    chrome_options.add_argument("--profile-directory=Default")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Navigate to Google Voice
        print("Navigating to Google Voice")
        driver.get("https://voice.google.com/messages")
        
        # Wait for the page to load
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".gvPageRoot"))
            )
            print("Google Voice loaded successfully")
            time.sleep(5)  # Give extra time for everything to load
        except TimeoutException:
            print("Timeout waiting for Google Voice to load")
            return
            
        # Process each league
        leagues = [
            {"name": "Wordle Warriorz", "id": 1, "phones": PHONE_NUMBERS_1},
            {"name": "Wordle PAL", "id": 3, "phones": PHONE_NUMBERS_3}
        ]
        
        for league in leagues:
            print(f"\nProcessing league: {league['name']} (ID: {league['id']})")
            
            for phone in league['phones']:
                print(f"Looking for conversation with phone: {phone}")
                
                # Find and click the conversation thread
                try:
                    # Look for thread using the phone number
                    thread_xpath = f"//gv-thread-item[contains(., '{phone}')]"
                    thread = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, thread_xpath))
                    )
                    thread.click()
                    print(f"Clicked on conversation thread for {phone}")
                    time.sleep(5)  # Wait for conversation to load
                    
                    # Scroll the conversation to load all messages
                    scroll_container = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".message-list-container"))
                    )
                    
                    # Scroll multiple times to ensure all messages load
                    print("Scrolling to load all messages...")
                    for _ in range(10):  # Scroll 10 times
                        driver.execute_script("arguments[0].scrollTop = 0", scroll_container)
                        time.sleep(1)
                    
                    # Extract all hidden DOM elements with Wordle scores
                    hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
                    
                    print(f"Found {len(hidden_elements)} hidden elements")
                    
                    # Extract all Wordle scores regardless of number
                    for elem in hidden_elements:
                        text = elem.text
                        if "Wordle" in text:
                            # Extract phone number from the text if it exists
                            phone_match = re.search(r'(\d{3}) (\d{3}) (\d{4})', text)
                            phone_number = None
                            if phone_match:
                                phone_number = ''.join(phone_match.groups())
                            
                            print("-" * 50)
                            print(f"Raw Text: {text}")
                            
                            # Try to extract Wordle number, score, and pattern
                            wordle_match = re.search(r'Wordle\s+([0-9,]+)\s+([X0-9])/6', text)
                            if wordle_match:
                                wordle_num = wordle_match.group(1).replace(',', '')
                                score = wordle_match.group(2)
                                if score == 'X':
                                    score = 7  # Failed attempt is scored as 7
                                print(f"Extracted - Wordle #{wordle_num}, Score: {score}, Phone: {phone_number}")
                    
                    # Go back to the messages list
                    back_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.back-button"))
                    )
                    back_button.click()
                    time.sleep(3)
                    
                except Exception as e:
                    print(f"Error processing thread: {e}")
                    
        print("\nExtraction completed successfully")
                
    finally:
        # Close the browser
        driver.quit()

if __name__ == "__main__":
    extract_all_scores_raw()
