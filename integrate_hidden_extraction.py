#!/usr/bin/env python3
"""
Integration Script for Hidden Element Extraction

This script integrates our new hidden element extraction approach into the main
extraction workflow in integrated_auto_update_multi_league.py.
"""

import re
import os
import shutil
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def backup_file(filepath):
    """Create a backup of a file"""
    if os.path.exists(filepath):
        backup_path = f"{filepath}.bak.{os.path.getmtime(filepath):.0f}"
        shutil.copy2(filepath, backup_path)
        logging.info(f"Created backup at {backup_path}")
        return True
    return False

def integrate_extraction():
    """
    Integrate hidden element extraction into the main script
    
    This function:
    1. Backs up the main extraction script
    2. Adds an import for our new extraction function
    3. Adds a call to our extraction function in the main thread processing loop
    """
    main_script = 'integrated_auto_update_multi_league.py'
    
    # Check if file exists
    if not os.path.exists(main_script):
        logging.error(f"Main script not found: {main_script}")
        return False
        
    # Create backup
    backup_file(main_script)
    
    try:
        # Read the main script
        with open(main_script, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Step 1: Add import for our new extraction function
        if "from direct_hidden_extraction import" not in content:
            # Find a good place to insert the import
            import_pos = content.find("import time")
            if import_pos >= 0:
                import_code = "\nimport time\n# Import hidden element extraction function\nfrom direct_hidden_extraction import extract_with_hidden_elements"
                content = content.replace("import time", import_code)
                logging.info("Added import for hidden element extraction")
            else:
                logging.warning("Could not find 'import time' in the main script")
                # Try to add at the top of the file
                content = "# Import hidden element extraction function\nfrom direct_hidden_extraction import extract_with_hidden_elements\n\n" + content
                logging.info("Added import at the top of the file")
        
        # Step 2: Find the extraction loop for each league
        # The pattern will vary based on the exact structure of the script
        # Let's search for the most likely integration point
        
        # Option 1: Look for the main score extraction function call
        extract_pattern = r"(extract_scores_from_conversation\(.*?\))"
        extract_matches = list(re.finditer(extract_pattern, content))
        
        if extract_matches:
            # For each match, add our extraction call before it
            modified_content = content
            offset = 0
            
            for match in extract_matches:
                extract_call = match.group(1)
                # Extract arguments from the call to reuse them
                args_match = re.search(r"\((.*?)\)", extract_call)
                if args_match:
                    args = args_match.group(1).split(",")
                    if len(args) >= 2:
                        # Assuming args[0] is driver and args[1] is related to league
                        new_extract_call = f"""
        # Try new hidden element extraction first
        logging.info("Using hidden element extraction for better reliability")
        hidden_scores = extract_with_hidden_elements({args[0]}, league_id, league_name)
        logging.info(f"Hidden element extraction found {{hidden_scores}} scores")
        
        # Fallback to original extraction for compatibility
        {extract_call}"""
                        
                        # Replace in the content with offset adjustment
                        start_pos = match.start(1) + offset
                        end_pos = match.end(1) + offset
                        modified_content = modified_content[:start_pos] + new_extract_call + modified_content[end_pos:]
                        # Update offset for subsequent replacements
                        offset += len(new_extract_call) - len(extract_call)
            
            content = modified_content
            logging.info("Added hidden element extraction calls")
        else:
            logging.warning("Could not find extraction function calls to modify")
            
            # Option 2: Look for thread processing loops
            thread_pattern = r"(for thread in threads:)"
            thread_matches = list(re.finditer(thread_pattern, content))
            
            if thread_matches:
                # For the last match (most likely the extraction loop)
                match = thread_matches[-1]
                thread_loop = match.group(1)
                
                # Add our extraction call right after the loop starts
                new_loop_code = f"""for thread in threads:
            # Try new hidden element extraction approach
            try:
                logging.info("Using hidden element extraction for better reliability")
                hidden_scores = extract_with_hidden_elements(driver, league_id, league_name)
                logging.info(f"Hidden element extraction found {{hidden_scores}} scores")
            except Exception as e:
                logging.error(f"Hidden element extraction failed: {{e}}")
                
            # Continue with regular thread processing"""
                
                content = content.replace(thread_loop, new_loop_code)
                logging.info("Added hidden element extraction to thread processing loop")
            else:
                logging.warning("Could not find thread processing loop")
        
        # Write updated content
        with open(main_script, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logging.info(f"Updated {main_script} with hidden element extraction integration")
        return True
        
    except Exception as e:
        logging.error(f"Error integrating hidden element extraction: {e}")
        return False

if __name__ == "__main__":
    print("Integrating hidden element extraction into main extraction script...")
    success = integrate_extraction()
    if success:
        print("Integration successful! You can now run the main extraction script.")
    else:
        print("Integration failed. Check the error messages above.")
