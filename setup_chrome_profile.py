import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    filename='chrome_profile_setup.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()
email = os.getenv('EMAIL_USERNAME')
password = os.getenv('EMAIL_PASSWORD')

def setup_chrome_profile():
    profile_dir = os.path.join(os.getcwd(), 'automation_profile')
    os.makedirs(profile_dir, exist_ok=True)
    
    chrome_options = Options()
    chrome_options.add_argument(f"user-data-dir={profile_dir}")
    
    logging.info(f"Setting up Chrome profile in {profile_dir}")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Go to Google Voice
        logging.info("Navigating to Google Voice")
        driver.get('https://voice.google.com/')
        
        # Check if we need to log in
        if "Sign in" in driver.title:
            logging.info("Login page detected. Attempting to log in...")
            
            # Enter email
            email_input = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "identifierId"))
            )
            email_input.send_keys(email)
            
            # Click next
            next_button = driver.find_element(By.ID, "identifierNext")
            next_button.click()
            
            # Wait for password field
            time.sleep(3)
            password_input = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.NAME, "Passwd"))
            )
            password_input.send_keys(password)
            
            # Click next
            next_button = driver.find_element(By.ID, "passwordNext")
            next_button.click()
            
            # Wait for Google Voice to load
            logging.info("Waiting for Google Voice to load...")
            time.sleep(10)
        
        # Verify we're logged in
        logging.info("Checking if login was successful...")
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "gv-side-nav"))
        )
        
        logging.info("Successfully logged in and created Chrome profile")
        print("Chrome profile setup complete! You can now run the extraction script.")
        
        # Keep the browser open for a moment so user can see it worked
        time.sleep(5)
        
    except Exception as e:
        logging.error(f"Error setting up Chrome profile: {str(e)}")
        print(f"Error: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    setup_chrome_profile()
