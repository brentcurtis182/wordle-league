#!/usr/bin/env python3
"""
Google Voice Thread Inspection Tool

This script opens Google Voice and inspects the DOM to find the exact selectors
for conversation threads, saving screenshots and the page source at each step.
"""

import os
import sys
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("inspect_gv_threads.log"),
        logging.StreamHandler()
    ]
)

def setup_driver():
    """Set up Chrome driver with the existing profile"""
    logging.info("Setting up Chrome driver")
    try:
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Use existing Chrome profile to avoid login issues
        profile_path = os.path.join(os.getcwd(), "automation_profile")
        if os.path.exists(profile_path):
            chrome_options.add_argument(f"user-data-dir={profile_path}")
            logging.info(f"Using existing Chrome profile at {profile_path}")
        else:
            logging.warning(f"Chrome profile not found at {profile_path}")
        
        # Initialize Chrome driver
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        logging.error(f"Error setting up Chrome driver: {e}")
        return None

def navigate_to_google_voice(driver):
    """Navigate to Google Voice and wait for page to load"""
    try:
        logging.info("Navigating to Google Voice")
        driver.get("https://voice.google.com/u/0/messages")
        
        # Wait longer for Google Voice to load completely (up to 30 seconds)
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "gv-conversation-list"))
            )
            logging.info("Google Voice page loaded successfully")
            return True
        except TimeoutException:
            logging.warning("Timed out waiting for gv-conversation-list")
            # Try an alternative wait
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[role='listitem']"))
                )
                logging.info("Google Voice page loaded (found listitem elements)")
                return True
            except TimeoutException:
                logging.error("Timed out waiting for Google Voice to load")
                return False
    except Exception as e:
        logging.error(f"Error navigating to Google Voice: {e}")
        return False

def save_page_info(driver, prefix):
    """Save page source and screenshot for debugging"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Save screenshot
    screenshot_path = f"{prefix}_screenshot_{timestamp}.png"
    driver.save_screenshot(screenshot_path)
    logging.info(f"Saved screenshot: {screenshot_path}")
    
    # Save page source
    source_path = f"{prefix}_source_{timestamp}.html"
    with open(source_path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    logging.info(f"Saved page source: {source_path}")
    
    # Save page DOM info using JavaScript
    try:
        dom_info = driver.execute_script("""
            function getElementInfo(element) {
                const rect = element.getBoundingClientRect();
                return {
                    tag: element.tagName,
                    id: element.id,
                    className: element.className,
                    text: element.innerText.substring(0, 50),
                    attributes: Array.from(element.attributes).map(attr => ({
                        name: attr.name,
                        value: attr.value
                    })),
                    position: {
                        x: rect.left,
                        y: rect.top,
                        width: rect.width,
                        height: rect.height
                    }
                };
            }
            
            const listElements = Array.from(document.querySelectorAll('[role="listitem"]'));
            const conversationElements = Array.from(document.querySelectorAll('gv-conversation-item'));
            
            return {
                listItems: listElements.slice(0, 5).map(getElementInfo),
                conversationItems: conversationElements.slice(0, 5).map(getElementInfo)
            };
        """)
        
        dom_path = f"{prefix}_dom_info_{timestamp}.json"
        with open(dom_path, "w", encoding="utf-8") as f:
            json.dump(dom_info, f, indent=2)
        logging.info(f"Saved DOM info: {dom_path}")
    except Exception as e:
        logging.error(f"Error saving DOM info: {e}")

def try_all_selectors(driver):
    """Try all possible CSS selectors for threads and log results"""
    selectors = [
        "gv-conversation-list gv-conversation-item",
        ".gvConversationListItem",
        "[role='listitem']",
        "[gv-id]",
        ".conversation-wrapper .conversation",
        ".gmat-list-item",
        "md-virtual-repeat-container md-list-item"
    ]
    
    results = {}
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            results[selector] = len(elements)
            logging.info(f"Selector '{selector}' found {len(elements)} elements")
            
            # For the first few elements, log their text content
            if elements:
                logging.info(f"First element with selector '{selector}' details:")
                for i, element in enumerate(elements[:3]):
                    try:
                        text = element.text
                        classes = element.get_attribute("class")
                        attrs = element.get_attribute("outerHTML")
                        logging.info(f"  Element {i}: Text: '{text[:50]}...' Classes: {classes}")
                        logging.info(f"  HTML snippet: '{attrs[:100]}...'")
                    except Exception as e:
                        logging.error(f"Error getting element details: {e}")
        except Exception as e:
            logging.error(f"Error finding elements with selector '{selector}': {e}")
            results[selector] = f"ERROR: {str(e)}"
    
    # Save results to file
    with open("selector_results.json", "w") as f:
        json.dump(results, f, indent=2)
    logging.info("Saved selector results to selector_results.json")
    
    return results

def inspect_thread_attributes(driver):
    """Inspect thread attributes to find identifiable patterns"""
    logging.info("Inspecting thread attributes")
    
    # Get thread elements with the most reliable selector
    threads = []
    selectors = ["[role='listitem']", "gv-conversation-item", ".gvConversationListItem"]
    
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                threads = elements
                logging.info(f"Using selector '{selector}' for thread inspection, found {len(elements)} threads")
                break
        except Exception:
            continue
    
    if not threads:
        logging.error("No thread elements found for inspection")
        return
    
    # Inspect attributes of each thread
    thread_info = []
    for i, thread in enumerate(threads[:5]):  # Inspect up to 5 threads
        try:
            html = thread.get_attribute("outerHTML")
            text = thread.text
            
            # Extract phone numbers using JavaScript
            phone_info = driver.execute_script("""
                const element = arguments[0];
                const text = element.innerText;
                const phonePattern = /\\(\\d{3}\\) \\d{3}-\\d{4}/g;
                const phones = text.match(phonePattern) || [];
                
                // Check for hidden annotation spans
                const annotations = element.querySelectorAll('.gv-annotation');
                const annotationTexts = [];
                annotations.forEach(a => {
                    annotationTexts.push(a.innerText);
                });
                
                return {
                    phones: phones,
                    annotations: annotationTexts,
                    hasMultipleParticipants: text.includes('+') && /\\+\\d+/.test(text)
                };
            """, thread)
            
            thread_info.append({
                "index": i,
                "text": text[:200],
                "html_sample": html[:300],
                "phone_info": phone_info
            })
            
            logging.info(f"Thread {i} info:")
            logging.info(f"  Text: {text[:50]}...")
            logging.info(f"  Phone numbers: {phone_info.get('phones', [])}")
            logging.info(f"  Annotations: {phone_info.get('annotations', [])}")
            logging.info(f"  Has multiple participants: {phone_info.get('hasMultipleParticipants', False)}")
            
        except Exception as e:
            logging.error(f"Error inspecting thread {i}: {e}")
    
    # Save thread info to file
    with open("thread_info.json", "w") as f:
        json.dump(thread_info, f, indent=2)
    logging.info("Saved thread info to thread_info.json")

def run_inspection():
    """Run the full inspection process"""
    driver = None
    try:
        # Set up WebDriver
        driver = setup_driver()
        if not driver:
            logging.error("Failed to set up WebDriver")
            return False
        
        # Navigate to Google Voice
        if not navigate_to_google_voice(driver):
            logging.error("Failed to navigate to Google Voice")
            return False
        
        # Save initial page info
        save_page_info(driver, "initial")
        
        # Try all CSS selectors
        selector_results = try_all_selectors(driver)
        
        # Inspect thread attributes
        inspect_thread_attributes(driver)
        
        # Save final page info
        save_page_info(driver, "final")
        
        # Return successful selectors
        successful_selectors = [selector for selector, count in selector_results.items() 
                              if isinstance(count, int) and count > 0]
        
        logging.info(f"Successful selectors: {successful_selectors}")
        return True
        
    except Exception as e:
        logging.error(f"Error during inspection: {e}")
        return False
        
    finally:
        # Clean up WebDriver
        if driver:
            driver.quit()
            logging.info("WebDriver closed")

if __name__ == "__main__":
    logging.info("Starting Google Voice thread inspection")
    success = run_inspection()
    logging.info(f"Inspection completed with success: {success}")
    sys.exit(0 if success else 1)
