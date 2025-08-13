#!/usr/bin/env python3
"""
Finalize Multi-League Integration

This script integrates all the improvements into the server_auto_update_multi_league.py
script to ensure the main workflow uses our improved extraction process.
"""

import os
import sys
import logging
import re
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

def main():
    """Integrate all improvements into the server_auto_update_multi_league.py script"""
    logging.info("Starting final integration")
    
    server_file = "server_auto_update_multi_league.py"
    if not os.path.exists(server_file):
        logging.error(f"File {server_file} not found")
        return False
        
    # Backup original file
    backup_file = f"{server_file}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(server_file, backup_file)
    logging.info(f"Created backup of {server_file} at {backup_file}")
    
    try:
        # Read file content
        with open(server_file, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Check if the file already uses the integrated_auto_update_multi_league.py for extraction
        if "import integrated_auto_update_multi_league" not in content and "from integrated_auto_update_multi_league import" not in content:
            # Update to use integrated_auto_update_multi_league.py for extraction
            content = re.sub(
                r'import extract_scores_multi_league',
                r'import integrated_auto_update_multi_league',
                content
            )
            content = re.sub(
                r'from extract_scores_multi_league import',
                r'from integrated_auto_update_multi_league import',
                content
            )
            content = re.sub(
                r'extract_scores_multi_league\.extract_wordle_scores\(',
                r'integrated_auto_update_multi_league.extract_wordle_scores_multi_league(',
                content
            )
            
        # Write updated content
        with open(server_file, 'w', encoding='utf-8') as file:
            file.write(content)
            
        # Create an updated run_extraction_only function to call in server_auto_update_multi_league.py
        create_run_extraction_script()
            
        logging.info(f"Successfully updated {server_file} to use integrated extraction")
        
        # Run the updated script to test
        test_result = run_extraction_test()
        return test_result
        
    except Exception as e:
        logging.error(f"Error during integration: {str(e)}")
        # Restore from backup if there was an error
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, server_file)
            logging.info(f"Restored {server_file} from backup")
        return False

def create_run_extraction_script():
    """Create an updated run_extraction_only script"""
    run_extraction_file = "run_extraction_only.py"
    
    content = """#!/usr/bin/env python3
\"\"\"
Run Extraction Only

This script runs only the extraction part of the Wordle League update process,
using the improved multi-league extraction methods.
\"\"\"

import sys
import logging
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"extraction_run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

def main():
    \"\"\"Run extraction only\"\"\"
    logging.info("=" * 50)
    logging.info("STARTING EXTRACTION ONLY")
    logging.info("=" * 50)
    
    try:
        # Import the extract function
        from integrated_auto_update_multi_league import extract_wordle_scores_multi_league
        
        # Run extraction
        success = extract_wordle_scores_multi_league()
        
        logging.info(f"Extraction completed with success: {success}")
        return success
    except Exception as e:
        logging.error(f"Error during extraction: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"Extraction only completed with success: {success}")
    sys.exit(0 if success else 1)
"""
    
    with open(run_extraction_file, 'w', encoding='utf-8') as file:
        file.write(content)
        
    logging.info(f"Created {run_extraction_file} for easy extraction testing")
    return True

def run_extraction_test():
    """Run the extraction test"""
    logging.info("Running extraction test")
    
    test_script = "run_extraction_only.py"
    if not os.path.exists(test_script):
        logging.error(f"Test script {test_script} not found")
        return False
        
    try:
        import subprocess
        process = subprocess.run(
            [sys.executable, test_script],
            capture_output=True,
            text=True,
            check=False
        )
        
        logging.info(f"Test exit code: {process.returncode}")
        logging.info(f"Test output: {process.stdout}")
        if process.stderr:
            logging.warning(f"Test errors: {process.stderr}")
            
        return process.returncode == 0
    except Exception as e:
        logging.error(f"Error running test: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"Final integration completed with success: {success}")
    sys.exit(0 if success else 1)
