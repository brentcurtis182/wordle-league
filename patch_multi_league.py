#!/usr/bin/env python3
"""
Wordle League Multi-League Extraction Patch

This patch integrates all our fixes for the multi-league extraction system:
1. Improved thread identification with exact gv-annotation patterns
2. Robust thread clicking using multiple methods
3. Better error handling and logging

To use this patch, run it directly:
python patch_multi_league.py

This will apply the fixes to the extraction process while maintaining compatibility 
with the existing scheduler system.
"""

import os
import sys
import time
import logging
import subprocess
from datetime import datetime

# Configure logging for this patch script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("patch_multi_league.log"),
        logging.StreamHandler()
    ]
)

def check_files_exist():
    """Check if all required files exist"""
    required_files = [
        "integrated_auto_update_multi_league.py",
        "is_league_thread.py", 
        "robust_thread_click.py",
        "improved_extraction_wrapper.py",
        "server_auto_update_multi_league.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        logging.error(f"Missing required files: {', '.join(missing_files)}")
        return False
    
    logging.info("All required files are present")
    return True

def backup_original_file():
    """Create a backup of the original multi-league extraction file"""
    original_file = "integrated_auto_update_multi_league.py"
    backup_file = f"integrated_auto_update_multi_league_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    
    try:
        import shutil
        shutil.copy2(original_file, backup_file)
        logging.info(f"Created backup of original file: {backup_file}")
        return True
    except Exception as e:
        logging.error(f"Failed to create backup: {e}")
        return False

def create_patched_run_script():
    """Create a script to run the patched extraction process"""
    script_content = """#!/usr/bin/env python3
# Patched Multi-League Extraction Runner

import sys
import os
import logging
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("patched_extraction.log"),
        logging.StreamHandler()
    ]
)

def main():
    logging.info("Starting patched multi-league extraction")
    
    try:
        # Import the original module
        from integrated_auto_update_multi_league import setup_driver, extract_hidden_scores, get_todays_wordle_number, get_yesterdays_wordle_number
        
        # Import our patched function
        from improved_extraction_wrapper import extract_with_improved_clicking
        
        # Import thread identification
        from is_league_thread import is_league_thread
        
        # Set up the driver
        driver = setup_driver()
        if not driver:
            logging.error("Failed to set up WebDriver")
            return False
            
        try:
            # Use patched extraction process
            from fixed_extract_multi_league import extract_wordle_scores_multi_league
            
            # Run extraction with our improved function
            success = extract_wordle_scores_multi_league(
                driver=driver,
                extract_hidden_scores_func=extract_hidden_scores,
                get_todays_wordle_number_func=get_todays_wordle_number,
                get_yesterdays_wordle_number_func=get_yesterdays_wordle_number,
                is_league_thread_func=is_league_thread
            )
            
            if success:
                logging.info("Patched extraction completed successfully!")
            else:
                logging.warning("Patched extraction completed but found no scores")
                
            return success
            
        except Exception as e:
            logging.error(f"Error during patched extraction: {str(e)}")
            logging.error(traceback.format_exc())
            return False
            
        finally:
            # Always close the driver
            try:
                if driver:
                    driver.quit()
                    logging.info("WebDriver closed")
            except Exception as e:
                logging.error(f"Error closing WebDriver: {str(e)}")
                
    except Exception as e:
        logging.error(f"Fatal error in patched extraction: {str(e)}")
        logging.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    exit_code = 0 if success else 1
    sys.exit(exit_code)
"""
    
    try:
        with open("run_patched_extraction.py", "w") as f:
            f.write(script_content)
        logging.info("Created patched runner script: run_patched_extraction.py")
        return True
    except Exception as e:
        logging.error(f"Failed to create patched runner script: {e}")
        return False

def test_patched_extraction():
    """Run the patched extraction script and verify it works"""
    try:
        logging.info("Testing patched extraction...")
        
        # Run the patched extraction script
        result = subprocess.run(
            [sys.executable, "run_patched_extraction.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logging.info("Patched extraction test successful!")
            logging.info("Output:")
            for line in result.stdout.splitlines():
                logging.info(f"> {line}")
            return True
        else:
            logging.error("Patched extraction test failed!")
            logging.error(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        logging.error(f"Failed to test patched extraction: {e}")
        return False

def create_direct_run_script():
    """Create a direct script that can be called by the scheduler"""
    script_content = """#!/usr/bin/env python3
# Direct Multi-League Extraction Script
# This script can be called directly by server_auto_update_multi_league.py

import logging
import sys
import os
from datetime import datetime

# Configure logging
log_file = f"multi_league_extraction_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

def main():
    """Run the improved multi-league extraction process"""
    logging.info("Starting improved multi-league extraction")
    
    try:
        # Use the patched runner
        import run_patched_extraction
        success = run_patched_extraction.main()
        
        # If that fails, fall back to original
        if not success:
            logging.warning("Patched extraction failed, falling back to original method")
            from integrated_auto_update_multi_league import extract_wordle_scores_multi_league
            success = extract_wordle_scores_multi_league()
        
        return success
        
    except Exception as e:
        logging.error(f"Error in direct run script: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    exit_code = 0 if success else 1
    print(f"Extraction completed with success: {success}")
    sys.exit(exit_code)
"""
    
    try:
        with open("run_multi_league.py", "w") as f:
            f.write(script_content)
        logging.info("Created direct run script: run_multi_league.py")
        return True
    except Exception as e:
        logging.error(f"Failed to create direct run script: {e}")
        return False

def update_scheduled_task():
    """Update the scheduled task to use our patched script"""
    bat_content = """@echo off
echo Running Wordle League Multi-League Update with improved extraction...
cd /d %~dp0
python run_multi_league.py
echo Multi-League extraction complete.
python server_auto_update_multi_league.py --sync-only --export-only --publish-only
echo Full update process complete.
"""
    
    try:
        with open("run_improved_update.bat", "w") as f:
            f.write(bat_content)
        logging.info("Created improved update batch file: run_improved_update.bat")
        return True
    except Exception as e:
        logging.error(f"Failed to create batch file: {e}")
        return False

def main():
    """Main function to apply all patches"""
    print("\n=== Wordle League Multi-League Extraction Patch ===\n")
    logging.info("Starting patch process")
    
    # Step 1: Check if all required files exist
    if not check_files_exist():
        print("\nERROR: Missing required files. Please ensure all helper files are present.")
        return False
    
    # Step 2: Create a backup of the original file
    if not backup_original_file():
        print("\nERROR: Failed to create backup. Aborting patch process.")
        return False
    
    # Step 3: Create patched run script
    if not create_patched_run_script():
        print("\nERROR: Failed to create patched runner script.")
        return False
    
    # Step 4: Create direct run script
    if not create_direct_run_script():
        print("\nERROR: Failed to create direct run script.")
        return False
    
    # Step 5: Update scheduled task
    if not update_scheduled_task():
        print("\nERROR: Failed to create improved batch file.")
        return False
    
    # Step 6: Test the patched extraction
    print("\nTesting the patched extraction...")
    test_result = test_patched_extraction()
    
    if test_result:
        print("\n=== Patch successfully applied! ===")
        print("\nThe following files have been created:")
        print("1. run_patched_extraction.py - The patched extraction runner")
        print("2. run_multi_league.py - A direct script that can be called by the scheduler")
        print("3. run_improved_update.bat - A batch file to run the improved update process")
        print("\nTo use the improved extraction:")
        print("- Run 'run_improved_update.bat' to perform a complete update")
        print("- Or schedule this batch file to run automatically")
    else:
        print("\n=== Patch applied but test failed ===")
        print("\nThe patch has been applied, but the test failed.")
        print("You can still use the original script by running:")
        print("python integrated_auto_update_multi_league.py")
    
    logging.info("Patch process completed")
    return test_result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
