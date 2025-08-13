def scroll_up_in_thread(driver, yesterday_wordle_num=None):
    """Scroll to the top of the conversation thread to load all messages.
    
    Args:
        driver: Selenium WebDriver instance
        yesterday_wordle_num: If provided, stops scrolling once messages from yesterday are found
        
    Returns:
        bool: True if scrolling successfully loaded more messages, False otherwise
    """
    import logging
    import time
    import re
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    
    logging.info("Starting enhanced message scrolling...")
    
    # Take screenshot before scrolling
    driver.save_screenshot(f"before_scroll.png")
    logging.info("Saved screenshot before scrolling")
    
    # Initialize counters for scroll attempts
    max_attempts = 15  # Maximum number of scroll attempts
    message_count = 0  # Current visible message count
    consecutive_same_count = 0  # Counter for consecutive attempts with no new messages
    found_yesterday = False  # Flag for finding yesterday's messages
    
    # Create pattern to match yesterday's Wordle number
    yesterday_pattern = None
    if yesterday_wordle_num:
        # Match formats like "Wordle 1,502" or "Wordle #1502"
        yesterday_pattern = re.compile(rf'Wordle\s+(?:#)?([\d,]+)')
    
    # APPROACH 1: Aggressively scroll to the top using the messages-container
    logging.info("Method 1: Aggressive scrolling using messages-container...")
    
    # Find the main scrollable messages container
    try:
        # Try multiple possible container selectors
        messages_container = None
        container_selectors = [
            ".messages-container",
            "div[gvinfinitescroll]",
            "div.messages-container",
            ".list"  # The ul.list that contains messages
        ]
        
        for selector in container_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    messages_container = elements[0]
                    logging.info(f"Found messages container with selector: {selector}")
                    break
            except:
                continue
        
        if not messages_container:
            logging.warning("Could not find specific messages container, falling back to body element")
            messages_container = driver.find_element(By.TAG_NAME, "body")
        
        # Initial count of hidden elements (our source of truth for messages)
        hidden_elements = driver.find_elements(By.CLASS_NAME, "cdk-visually-hidden")
        initial_hidden_count = len(hidden_elements)
        logging.info(f"Initial count: {initial_hidden_count} hidden elements")
        
        # Main scrolling loop
        for attempt in range(max_attempts):
            # Log current progress
            logging.info(f"Scroll attempt {attempt+1}/{max_attempts}...")
            
            # Method 1: Use JavaScript to scroll to top
            try:
                # Scroll the messages container to the top
                driver.execute_script("arguments[0].scrollTop = 0;", messages_container)
                time.sleep(1)  # Short wait
                
                # More aggressive scroll to the very top
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)  # Short wait
            except Exception as e:
                logging.error(f"Error during JS scroll: {e}")
            
            # Method 2: Send Page Up keys
            try:
                # Send Page Up keys to the container
                body = driver.find_element(By.TAG_NAME, "body")
                for _ in range(3):  # Multiple Page Up presses
                    body.send_keys(Keys.PAGE_UP)
                    time.sleep(0.5)
            except Exception as e:
                logging.error(f"Error during keyboard scroll: {e}")
            
            # Allow time for messages to load
            time.sleep(3)  # Longer wait between scrolls for DOM updates
            
            # Check how many hidden elements we have now
            hidden_elements = driver.find_elements(By.CLASS_NAME, "cdk-visually-hidden")
            new_hidden_count = len(hidden_elements)
            
            # Log progress
            logging.info(f"After attempt {attempt+1}: Found {new_hidden_count} hidden elements " +
                        f"(was {initial_hidden_count if attempt == 0 else message_count})")
            
            # Check for yesterday's wordle number in messages
            if yesterday_pattern:
                found_yesterday = False
                for element in hidden_elements:
                    try:
                        text = element.text
                        match = yesterday_pattern.search(text)
                        if match:
                            # Convert potential comma-formatted number "1,502" to integer 1502
                            found_num = int(match.group(1).replace(",", ""))
                            if found_num == yesterday_wordle_num:
                                logging.info(f"SUCCESS: Found yesterday's Wordle #{yesterday_wordle_num} in the conversation!")
                                found_yesterday = True
                                break
                    except:
                        continue
                
                if found_yesterday:
                    logging.info("Found messages from yesterday's Wordle, stopping scroll")
                    break
            
            # Check if we've loaded new messages
            if new_hidden_count == message_count:
                # No new messages loaded after this scroll attempt
                consecutive_same_count += 1
                if consecutive_same_count >= 3:  # Stop if same count for 3 consecutive attempts
                    logging.info("No new messages loaded after multiple attempts, stopping scroll")
                    break
            else:
                # Reset counter since we found new messages
                consecutive_same_count = 0
            
            message_count = new_hidden_count
    
    except Exception as e:
        logging.error(f"Error in main scrolling loop: {e}")
    
    # APPROACH 2: Try an alternative method - use JavaScript to expose all messages
    logging.info("Method 2: Using JavaScript to ensure all messages are visible...")
    try:
        # This script attempts to manipulate the DOM to expand all messages
        expand_js = """
        // Force all message containers to be visible
        var allMessages = document.querySelectorAll('.message-row');
        allMessages.forEach(function(msg) {
            msg.style.display = 'block';
            msg.style.visibility = 'visible';
            msg.classList.remove('ng-hide');
        });
        
        // Force all hidden elements to be exposed
        var allHidden = document.querySelectorAll('.cdk-visually-hidden');
        allHidden.forEach(function(el) {
            el.setAttribute('data-extracted', 'true');
        });
        
        // Try to expose any lazy-loaded messages
        var scrollContainer = document.querySelector('.messages-container');
        if (scrollContainer) {
            scrollContainer.scrollTop = 0;
        }
        """
        
        # Execute the JavaScript to manipulate the DOM
        driver.execute_script(expand_js)
        time.sleep(2)  # Allow time for DOM changes
    except Exception as e:
        logging.error(f"Error during DOM manipulation: {e}")
    
    # Take a screenshot after scrolling is complete
    driver.save_screenshot("after_scroll.png")
    logging.info("Saved screenshot after scrolling")
    
    # Final count of hidden elements
    final_hidden_elements = driver.find_elements(By.CLASS_NAME, "cdk-visually-hidden")
    logging.info(f"Final count: {len(final_hidden_elements)} hidden elements")
    
    # Check if we successfully loaded more messages
    success = len(final_hidden_elements) > initial_hidden_count
    logging.info(f"Scrolling {'successful' if success else 'did not load new messages'}")
    
    return success
