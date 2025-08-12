import os
import time
import logging
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("diagnose_profile.log"),
        logging.StreamHandler()
    ]
)

def kill_chrome_processes():
    """Kill any running Chrome processes"""
    logging.info("Attempting to kill any running Chrome processes")
    try:
        # For Windows
        subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
        logging.info("Chrome processes terminated")
    except Exception as e:
        logging.error(f"Error killing Chrome processes: {e}")
    
    # Wait a moment for processes to fully terminate
    time.sleep(2)

def check_profile_directory():
    """Check if profile directory exists and is valid"""
    profile_dir = os.path.join(os.getcwd(), "automation_profile")
    logging.info(f"Checking profile directory: {profile_dir}")
    
    if not os.path.exists(profile_dir):
        logging.error("Profile directory does not exist")
        return False
    
    if not os.listdir(profile_dir):
        logging.error("Profile directory is empty")
        return False
    
    logging.info(f"Profile directory exists and contains files")
    return True

def test_direct_chrome_launch():
    """Test launching Chrome directly"""
    profile_dir = os.path.join(os.getcwd(), "automation_profile")
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    url = "https://voice.google.com/messages"
    
    logging.info(f"Testing direct Chrome launch to {url}")
    
    try:
        # Launch Chrome directly
        cmd = f'"{chrome_path}" --user-data-dir="{profile_dir}" {url}'
        logging.info(f"Running command: {cmd}")
        
        # Use subprocess.Popen to launch Chrome
        process = subprocess.Popen(cmd, shell=True)
        logging.info(f"Chrome process started with PID: {process.pid}")
        
        # Wait for Chrome to open
        time.sleep(10)
        
        # Check if process is still running
        if process.poll() is None:
            logging.info("Chrome process is still running")
        else:
            logging.error(f"Chrome process exited with code: {process.returncode}")
        
        # Try to kill the process
        try:
            process.terminate()
            logging.info("Chrome process terminated")
        except:
            logging.warning("Could not terminate Chrome process")
        
        return True
    except Exception as e:
        logging.error(f"Error launching Chrome directly: {e}")
        return False

def test_selenium_launch():
    """Test launching Chrome with Selenium"""
    profile_dir = os.path.join(os.getcwd(), "automation_profile")
    
    logging.info("Testing Selenium Chrome launch")
    
    try:
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument(f"user-data-dir={profile_dir}")
        
        # Create Chrome driver
        logging.info("Creating Chrome driver")
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to Google Voice
        url = "https://voice.google.com/messages"
        logging.info(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(5)
        
        # Take screenshot
        screenshot_path = os.path.join(os.getcwd(), "selenium_test.png")
        driver.save_screenshot(screenshot_path)
        logging.info(f"Screenshot saved to: {screenshot_path}")
        
        # Get current URL
        current_url = driver.current_url
        logging.info(f"Current URL: {current_url}")
        
        # Close driver
        driver.quit()
        logging.info("Chrome driver closed")
        
        return True
    except Exception as e:
        logging.error(f"Error with Selenium Chrome launch: {e}")
        return False

def main():
    logging.info("Starting profile diagnostics")
    
    # Step 1: Kill any running Chrome processes
    kill_chrome_processes()
    
    # Step 2: Check profile directory
    if not check_profile_directory():
        logging.error("Profile directory check failed")
        return
    
    # Step 3: Test direct Chrome launch
    logging.info("Testing direct Chrome launch...")
    direct_launch_success = test_direct_chrome_launch()
    
    # Kill Chrome processes again before Selenium test
    kill_chrome_processes()
    
    # Step 4: Test Selenium launch
    logging.info("Testing Selenium Chrome launch...")
    selenium_launch_success = test_selenium_launch()
    
    # Summary
    logging.info("=== Diagnostic Summary ===")
    logging.info(f"Direct Chrome launch: {'SUCCESS' if direct_launch_success else 'FAILED'}")
    logging.info(f"Selenium Chrome launch: {'SUCCESS' if selenium_launch_success else 'FAILED'}")
    
    if direct_launch_success and not selenium_launch_success:
        logging.info("RECOMMENDATION: Use direct Chrome launch approach instead of Selenium")
    elif not direct_launch_success and not selenium_launch_success:
        logging.info("RECOMMENDATION: Check Chrome installation and profile directory permissions")

if __name__ == "__main__":
    main()
