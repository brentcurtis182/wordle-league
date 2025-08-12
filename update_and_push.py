import os
import logging
import sys
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_and_push.log"),
        logging.StreamHandler()
    ]
)

# Import enhanced functions
from enhanced_functions import update_website, push_to_github

# Load environment variables
load_dotenv()

def main():
    logging.info("Starting website update and push")
    
    # Step 1: Update website
    website_success = update_website()
    
    if website_success:
        logging.info("Website updated successfully, now pushing to GitHub")
        
        # Step 2: Push to GitHub
        push_success = push_to_github()
        
        if push_success:
            logging.info("GitHub push completed successfully")
        else:
            logging.error("GitHub push failed")
    else:
        logging.error("Website update failed")

if __name__ == "__main__":
    main()
