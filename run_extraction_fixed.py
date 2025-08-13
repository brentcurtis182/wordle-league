#!/usr/bin/env python3
# Integration function to use our fixed extraction method

import logging
import time
from is_league_thread import is_league_thread
from fixed_extract_multi_league import extract_wordle_scores_multi_league as fixed_extract

def run_extraction_with_fixed_method(driver_setup_func, extract_hidden_scores_func, 
                                    get_todays_wordle_func, get_yesterdays_wordle_func):
    """
    Run the fixed extraction method with proper error handling
    
    Args:
        driver_setup_func: Function to set up the WebDriver
        extract_hidden_scores_func: Function to extract scores from thread
        get_todays_wordle_func: Function to get today's Wordle number
        get_yesterdays_wordle_func: Function to get yesterday's Wordle number
        
    Returns:
        bool: True if extraction was successful, False otherwise
    """
    logging.info("=== STARTING EXTRACTION USING FIXED METHOD ===")
    
    try:
        # Set up the driver
        driver = driver_setup_func()
        if not driver:
            logging.error("Failed to set up WebDriver")
            return False
        
        try:
            # Run the fixed extraction method
            success = fixed_extract(
                driver=driver,
                extract_hidden_scores_func=extract_hidden_scores_func,
                get_todays_wordle_number_func=get_todays_wordle_func,
                get_yesterdays_wordle_number_func=get_yesterdays_wordle_func,
                is_league_thread_func=is_league_thread
            )
            
            if success:
                logging.info("Extraction completed successfully!")
            else:
                logging.warning("Extraction completed with no scores found")
            
            return success
            
        except Exception as e:
            logging.error(f"Error during extraction: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False
            
        finally:
            # Always ensure driver is closed
            try:
                if driver:
                    driver.quit()
                    logging.info("WebDriver closed")
            except Exception as e:
                logging.error(f"Error closing WebDriver: {e}")
    
    except Exception as e:
        logging.error(f"Error in run_extraction_with_fixed_method: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return False
