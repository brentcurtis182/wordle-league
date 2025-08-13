#!/usr/bin/env python3
import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s',
                   handlers=[
                       logging.FileHandler("html_dump.log"),
                       logging.StreamHandler()
                   ])

def dump_conversation_html():
    """Dump the HTML of Google Voice conversation threads to inspect for Wordle scores"""
    
    # League thread information
    LEAGUES = [
        {"name": "Wordle Warriorz", "id": 1, "phone_pattern": r".*760.*|.*737.*|.*670.*|.*213.*|.*858.*"},
        {"name": "Wordle PAL", "id": 3, "phone_pattern": r".*469.*|.*760.*"}
    ]
    
    # Setup Chrome driver
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Use user profile for persistent login
    user_data_dir = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data')
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Set implicit wait time
        driver.implicitly_wait(10)
        
        # Navigate to Google Voice
        driver.get("https://voice.google.com/messages")
        logging.info("Navigated to Google Voice")
        
        # Wait for threads to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "gv-thread-list md-virtual-repeat-container"))
        )
        
        # Process each league
        for league in LEAGUES:
            logging.info(f"Processing league: {league['name']} (ID: {league['id']})")
            
            # Find all thread elements
            thread_elements = driver.find_elements(By.CSS_SELECTOR, "gv-thread-item")
            logging.info(f"Found {len(thread_elements)} thread elements")
            
            for i, thread_element in enumerate(thread_elements):
                logging.info(f"Checking thread {i+1}")
                
                # Get participant elements
                try:
                    participant_elements = thread_element.find_elements(By.CSS_SELECTOR, "gv-annotation.participants")
                    if participant_elements:
                        annotation_text = participant_elements[0].text
                        logging.info(f"Thread {i+1} participants: {annotation_text}")
                        
                        # Check if this thread matches league criteria
                        import re
                        if re.search(league['phone_pattern'], annotation_text):
                            logging.info(f"Found thread {i+1} for {league['name']} (ID: {league['id']})")
                            
                            # Click on thread to open conversation
                            try:
                                driver.execute_script("arguments[0].click();", thread_element)
                                logging.info(f"Clicked on {league['name']} thread")
                                time.sleep(2)  # Allow thread to load
                                
                                # Wait for conversation to load
                                WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "gv-message-list"))
                                )
                                
                                # Dump the HTML of the conversation
                                conversation_html = driver.find_element(By.CSS_SELECTOR, "gv-message-list").get_attribute('outerHTML')
                                logging.info(f"Conversation HTML length: {len(conversation_html)}")
                                
                                # Save HTML to file for inspection
                                with open(f"{league['name'].replace(' ', '_')}_conversation.html", "w", encoding="utf-8") as f:
                                    f.write(conversation_html)
                                logging.info(f"Saved {league['name']} conversation HTML to file")
                                
                                # Check for visually hidden elements that might contain Wordle scores
                                hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
                                logging.info(f"Found {len(hidden_elements)} hidden elements")
                                
                                # Log the text content of hidden elements
                                with open(f"{league['name'].replace(' ', '_')}_hidden_elements.txt", "w", encoding="utf-8") as f:
                                    for j, elem in enumerate(hidden_elements):
                                        try:
                                            elem_text = elem.get_attribute('textContent')
                                            if "Wordle" in elem_text:
                                                logging.info(f"Hidden element {j} contains Wordle score: {elem_text}")
                                                f.write(f"Element {j}:\n{elem_text}\n\n")
                                        except Exception as e:
                                            logging.error(f"Error getting text from hidden element: {e}")
                                
                                # Go back to thread list
                                driver.get("https://voice.google.com/messages")
                                time.sleep(2)
                                
                                # Wait for threads to load again
                                WebDriverWait(driver, 20).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "gv-thread-list md-virtual-repeat-container"))
                                )
                                # Refresh thread elements
                                thread_elements = driver.find_elements(By.CSS_SELECTOR, "gv-thread-item")
                                
                            except Exception as e:
                                logging.error(f"Error processing thread for {league['name']}: {e}")
                                driver.get("https://voice.google.com/messages")
                                time.sleep(2)
                except Exception as e:
                    logging.error(f"Error checking thread {i+1}: {e}")
                    
    except Exception as e:
        logging.error(f"Error in dump_conversation_html: {e}")
    finally:
        if driver:
            driver.quit()
            
    logging.info("HTML dump completed")

if __name__ == "__main__":
    dump_conversation_html()
