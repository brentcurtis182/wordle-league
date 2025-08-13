#!/usr/bin/env python3
"""
Minimal modification of integrated_auto_update_multi_league.py to log DOM elements
"""
import os
import sys
import logging
from datetime import datetime
import re

# Set up logging specifically for DOM elements
dom_logger = logging.getLogger('dom_elements')
dom_handler = logging.FileHandler('dom_elements.log', mode='w')
dom_handler.setLevel(logging.INFO)
dom_handler.setFormatter(logging.Formatter('%(message)s'))
dom_logger.addHandler(dom_handler)
dom_logger.setLevel(logging.INFO)

# Create HTML output file
html_file = open('dom_elements.html', 'w', encoding='utf-8')
html_file.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Wordle DOM Elements - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .element {{ border: 1px solid #ccc; padding: 10px; margin: 10px 0; }}
        .wordle-num {{ font-weight: bold; color: blue; }}
        .player {{ font-weight: bold; }}
        .score {{ color: green; font-weight: bold; }}
        .emoji {{ font-family: monospace; white-space: pre; }}
        pre {{ background-color: #f5f5f5; padding: 10px; overflow-x: auto; }}
        .today {{ background-color: #ccffcc; }}
        .match {{ background-color: #ffffcc; }}
    </style>
</head>
<body>
    <h1>Wordle Score DOM Elements</h1>
    <p>Extraction time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
""")

# Import the main script
sys.path.append(os.getcwd())
import integrated_auto_update_multi_league

# Store the original extract_scores_from_conversations function
original_extract = integrated_auto_update_multi_league.extract_scores_from_conversations

# Create a modified version that logs DOM elements
def extract_scores_with_logging(driver, conversation_items, today_wordle, yesterday_wordle, league_id=1):
    print(f"\n{'='*60}")
    print(f"EXTRACTING SCORES FOR LEAGUE {league_id}")
    print(f"Today's Wordle: #{today_wordle}, Yesterday's Wordle: #{yesterday_wordle}")
    print(f"{'='*60}")
    
    html_file.write(f"""
    <h2>League ID: {league_id}</h2>
    <p>Today's Wordle: <span class="wordle-num">#{today_wordle}</span>, Yesterday's: <span class="wordle-num">#{yesterday_wordle}</span></p>
""")
    
    # Regular expressions for finding Wordle scores
    wordle_pattern = re.compile(r'Wordle\s+([0-9,]+)\s+([1-6]|X)/6')
    
    # Process each conversation
    for i, conversation in enumerate(conversation_items):
        try:
            # Click on conversation to load messages
            driver.execute_script("arguments[0].click();", conversation)
            print(f"Clicked on conversation {i+1} for league {league_id}")
            
            # Wait for the conversation to load
            html_file.write(f"""
    <div class="element">
        <h3>Conversation {i+1}</h3>
""")
            
            # Let the original code scroll
            integrated_auto_update_multi_league.scroll_up_in_thread(driver, yesterday_wordle)
            print(f"Scrolled through conversation {i+1}")
            
            # Find hidden elements containing message text
            hidden_elements = driver.find_elements(integrated_auto_update_multi_league.By.CSS_SELECTOR, ".cdk-visually-hidden")
            print(f"Found {len(hidden_elements)} hidden elements in conversation {i+1}")
            
            # Process each hidden element
            for j, element in enumerate(hidden_elements):
                try:
                    # Get text content
                    text = element.get_attribute("textContent") or element.text
                    
                    # Skip empty or very short texts
                    if not text or len(text) < 10:
                        continue
                    
                    # Skip reaction messages
                    reaction_patterns = ['Loved', 'Liked', 'Laughed at', 'Emphasized', 'Reacted to']
                    if any(pattern in text for pattern in reaction_patterns):
                        continue
                    
                    # Check if this contains a Wordle score
                    css_class = ""
                    match = None
                    
                    if "Wordle" in text:
                        match = wordle_pattern.search(text)
                        if match:
                            wordle_num_str = match.group(1).replace(',', '')
                            try:
                                wordle_num = int(wordle_num_str)
                                score_text = match.group(2)
                                
                                if wordle_num == today_wordle:
                                    css_class = "today"
                                    print(f"\n{'='*60}")
                                    print(f"TODAY'S WORDLE #{today_wordle} FOUND!")
                                    print(f"{'='*60}")
                                    print(f"Text: {text}")
                                    print(f"{'='*60}")
                                    dom_logger.info(f"\n{'='*60}\nTODAY'S WORDLE #{today_wordle} FOUND!\n{'='*60}")
                                    dom_logger.info(f"Text: {text}")
                                    dom_logger.info(f"{'='*60}")
                                elif wordle_num == yesterday_wordle:
                                    css_class = "match"
                            except ValueError:
                                pass
                    
                    # Write element to HTML file
                    html_file.write(f"""
        <div class="element {css_class}">
            <h4>Element {j+1}</h4>
            <pre>{text}</pre>
        </div>
""")
                
                except Exception as e:
                    print(f"Error processing element {j+1}: {e}")
            
            # Close the conversation div
            html_file.write("</div>")
            
            # Navigate back to the conversations list
            try:
                back_button = integrated_auto_update_multi_league.WebDriverWait(driver, 10).until(
                    integrated_auto_update_multi_league.EC.element_to_be_clickable((
                        integrated_auto_update_multi_league.By.CSS_SELECTOR, 
                        "gv-icon-button[icon-name='arrow_back']"
                    ))
                )
                back_button.click()
                integrated_auto_update_multi_league.time.sleep(2)
            except Exception as e:
                print(f"Error navigating back: {e}")
                driver.get("https://voice.google.com/messages")
                integrated_auto_update_multi_league.time.sleep(3)
            
        except Exception as e:
            print(f"Error processing conversation {i+1}: {e}")
            driver.get("https://voice.google.com/messages")
            integrated_auto_update_multi_league.time.sleep(3)
    
    # Call the original function to do the actual extraction and database updates
    return original_extract(driver, conversation_items, today_wordle, yesterday_wordle, league_id)

# Replace the original function with our logging version
integrated_auto_update_multi_league.extract_scores_from_conversations = extract_scores_with_logging

if __name__ == "__main__":
    print("Starting extraction with DOM element logging...")
    
    try:
        # Run the main script's extraction function
        integrated_auto_update_multi_league.extract_wordle_scores_multi_league()
        
        # Close the HTML file
        html_file.write("""
    <p>Extraction completed successfully</p>
</body>
</html>
""")
        html_file.close()
        
        print("\nExtraction completed!")
        print(f"DOM elements saved to dom_elements.log and dom_elements.html")
        
    except Exception as e:
        print(f"Error during extraction: {e}")
        
        # Make sure to close the HTML file
        html_file.write(f"""
    <p>Extraction failed with error: {e}</p>
</body>
</html>
""")
        html_file.close()
