#!/usr/bin/env python3
"""
Script to analyze the Google Voice DOM to understand the structure
and help improve the extraction of Wordle scores.
"""

import os
import sys
import time
import logging
import sqlite3
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("google_voice_dom_analysis.log"),
        logging.StreamHandler()
    ]
)

def setup_driver():
    """Set up Chrome WebDriver with appropriate options."""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        
        # Use headless mode for production, remove for debugging
        # chrome_options.add_argument("--headless")
        
        driver = webdriver.Chrome(options=chrome_options)
        logging.info("WebDriver initialized successfully")
        return driver
    except Exception as e:
        logging.error(f"Failed to initialize WebDriver: {e}")
        return None

def login_to_google_voice(driver):
    """Log in to Google Voice."""
    try:
        # Navigate to Google Voice
        driver.get("https://voice.google.com/")
        logging.info("Navigated to Google Voice")
        
        # Wait for sign-in button or account already logged in
        wait = WebDriverWait(driver, 10)
        try:
            # Check if we need to sign in
            sign_in_button = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Sign in')]")))
            sign_in_button.click()
            logging.info("Clicked sign-in button")
            
            # Enter email
            email_input = wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
            email = os.environ.get("GOOGLE_EMAIL")
            email_input.send_keys(email)
            logging.info(f"Entered email: {email}")
            
            # Click Next
            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']")))
            next_button.click()
            logging.info("Clicked Next after email")
            
            # Wait for password input and enter password
            password_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='password']")))
            password = os.environ.get("GOOGLE_PASSWORD")
            password_input.send_keys(password)
            logging.info("Entered password")
            
            # Click Next
            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']")))
            next_button.click()
            logging.info("Clicked Next after password")
            
        except TimeoutException:
            logging.info("Already logged in or sign-in button not found")
        
        # Wait for Google Voice to load
        wait.until(EC.presence_of_element_located((By.XPATH, "//gmat-nav-bar")))
        logging.info("Google Voice loaded successfully")
        return True
        
    except Exception as e:
        logging.error(f"Error during login: {e}")
        return False

def analyze_conversations(driver):
    """Navigate to conversations and analyze the DOM structure."""
    try:
        # Wait for conversations to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.XPATH, "//gv-conversation-list")))
        
        # Find all conversation items
        conversation_items = driver.find_elements(By.XPATH, "//gv-conversation-list-item")
        logging.info(f"Found {len(conversation_items)} conversation items")
        
        for i, conversation in enumerate(conversation_items[:2]):  # Limit to first 2 conversations for analysis
            try:
                # Click on conversation
                conversation.click()
                logging.info(f"Clicked on conversation {i+1}")
                
                # Wait for conversation details to load
                wait.until(EC.presence_of_element_located((By.XPATH, "//gv-message-list")))
                time.sleep(2)  # Give it a moment to fully load
                
                # Get the conversation HTML
                conversation_html = driver.page_source
                
                # Save the HTML to a file for analysis
                with open(f"conversation_{i+1}_dom.html", "w", encoding="utf-8") as f:
                    f.write(conversation_html)
                logging.info(f"Saved conversation {i+1} HTML to conversation_{i+1}_dom.html")
                
                # Use BeautifulSoup to analyze the HTML
                analyze_html_for_wordle_scores(conversation_html, i+1)
                
                # Go back to conversation list
                back_button = driver.find_element(By.XPATH, "//button[@aria-label='Back']")
                back_button.click()
                logging.info("Returned to conversation list")
                
                # Wait for conversations list to reload
                wait.until(EC.presence_of_element_located((By.XPATH, "//gv-conversation-list")))
                time.sleep(1)  # Short pause
                
                # Need to find conversation items again after navigating back
                conversation_items = driver.find_elements(By.XPATH, "//gv-conversation-list-item")
                
            except Exception as e:
                logging.error(f"Error processing conversation {i+1}: {e}")
                
                # Try to go back to conversation list if there was an error
                try:
                    back_button = driver.find_element(By.XPATH, "//button[@aria-label='Back']")
                    back_button.click()
                    wait.until(EC.presence_of_element_located((By.XPATH, "//gv-conversation-list")))
                except:
                    logging.error("Failed to return to conversation list after error")
                    
        return True
    
    except Exception as e:
        logging.error(f"Error analyzing conversations: {e}")
        return False

def analyze_html_for_wordle_scores(html, conversation_number):
    """Analyze the HTML to find and understand Wordle scores structure."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Look for different potential elements that might contain Wordle scores
    logging.info(f"\n===== ANALYSIS FOR CONVERSATION {conversation_number} =====")
    
    # 1. Check for cdk-visually-hidden elements
    visually_hidden = soup.select('.cdk-visually-hidden')
    logging.info(f"Found {len(visually_hidden)} .cdk-visually-hidden elements")
    
    # Sample some of the visually hidden elements
    for i, element in enumerate(visually_hidden[:10]):  # Look at first 10
        text = element.get_text(strip=True)
        if "Wordle" in text:
            logging.info(f"FOUND WORDLE SCORE in cdk-visually-hidden #{i}: {text}")
    
    # 2. Check for message content elements
    message_contents = soup.select('gv-message-content')
    logging.info(f"Found {len(message_contents)} gv-message-content elements")
    
    for i, element in enumerate(message_contents[:10]):  # Look at first 10
        text = element.get_text(strip=True)
        if "Wordle" in text:
            logging.info(f"FOUND WORDLE SCORE in message-content #{i}: {text}")
    
    # 3. Check text nodes that might contain Wordle patterns
    all_text = soup.find_all(string=True)
    wordle_texts = [text for text in all_text if "Wordle" in text]
    logging.info(f"Found {len(wordle_texts)} text nodes containing 'Wordle'")
    
    for i, text in enumerate(wordle_texts[:5]):  # Sample first 5
        logging.info(f"Wordle text #{i}: {text}")
        
        # Find parent element
        parent = text.parent
        logging.info(f"Parent element: {parent.name}, class: {parent.get('class', 'no-class')}")
        
        # Look at siblings to find emoji patterns
        siblings = list(parent.next_siblings)
        for j, sibling in enumerate(siblings[:3]):
            if sibling and sibling.string:
                logging.info(f"  Sibling #{j} text: {sibling.string}")
    
    # 4. Look for elements with emoji pattern specifically
    emoji_pattern = re.compile(r'[⬛🟨🟩]+')
    for i, element in enumerate(soup.find_all(string=emoji_pattern)):
        logging.info(f"FOUND EMOJI PATTERN #{i}: {element}")
        
        # Find parent and analyze structure
        parent = element.parent
        logging.info(f"Parent of emoji pattern: {parent.name}, class: {parent.get('class', 'no-class')}")
        
        # Try to find nearby wordle text
        siblings = list(parent.previous_siblings) + list(parent.next_siblings)
        for sibling in siblings[:5]:
            if sibling and hasattr(sibling, 'string') and sibling.string and "Wordle" in sibling.string:
                logging.info(f"  Near emoji pattern: {sibling.string}")
    
    # 5. Final structure recommendation
    logging.info("\nRECOMMENDATION FOR EXTRACTION:")
    logging.info("1. Look for .cdk-visually-hidden elements first as they may contain complete score data")
    logging.info("2. Then check gv-message-content elements for Wordle scores")
    logging.info("3. Look for text nodes containing 'Wordle' and check their siblings for emoji patterns")
    
def main():
    """Main function."""
    logging.info("Starting Google Voice DOM analysis")
    
    # Set up WebDriver
    driver = setup_driver()
    if not driver:
        logging.error("Failed to set up WebDriver, exiting")
        return
        
    try:
        # Login to Google Voice
        if not login_to_google_voice(driver):
            logging.error("Failed to log in to Google Voice, exiting")
            driver.quit()
            return
            
        # Analyze conversations
        analyze_conversations(driver)
            
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        # Clean up
        driver.quit()
        logging.info("Analysis completed, WebDriver closed")
        
if __name__ == "__main__":
    main()
