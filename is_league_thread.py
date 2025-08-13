#!/usr/bin/env python3
# Helper function to identify which league a thread belongs to

import logging

def is_league_thread(thread_element, league_id):
    """
    Determine if a thread belongs to a specific league based on its content
    
    Args:
        thread_element: The thread element to check
        league_id: The league ID to check for (1=Warriorz, 2=Gang, 3=PAL, 4=Party, 5=Vball)
        
    Returns:
        bool: True if the thread belongs to the specified league, False otherwise
    """
    # Add more detailed debug logging
    debug = True  # Set to True for more verbose logging
    
    # Extract text from the thread element
    try:
        thread_text = thread_element.text
    except:
        thread_text = ""
        
    # Also get HTML to check for specific patterns
    try:
        thread_html = thread_element.get_attribute('outerHTML')
    except:
        thread_html = ""
        
    if not thread_text and not thread_html:
        logging.warning("No text or HTML content in thread element")
        return False
        
    # Define league identifiers for precise matching
    league_identifiers = {
        1: {
            "name": "Wordle Warriorz",
            "exact_pattern": "‪(310) 926-3555‬, ‪(760) 334-1190‬, +3",
            "phone_combo": ["(310) 926-3555", "(760) 334-1190"],
            "unique_names": ["Wordle Warriorz"]
        },
        2: {
            "name": "Wordle Gang",
            "exact_pattern": "‪(310) 200-4244‬, ‪(310) 266-1718‬, +5",
            "phone_combo": ["(310) 200-4244", "(310) 266-1718"],
            "unique_names": ["Wordle Gang"]
        },
        3: {
            "name": "PAL",
            "exact_pattern": "‪(469) 834-5364‬, ‪(760) 420-6113‬, +2",
            "phone_combo": ["(469) 834-5364", "(760) 420-6113"],
            "unique_names": ["PAL"]
        },
        4: {
            "name": "Wordle Party",
            "exact_pattern": "Dinkbeach, ‪(760) 682-5666‬, +2",
            "phone_combo": ["Dinkbeach", "(760) 682-5666"],
            "unique_names": ["Wordle Party"]
        },
        5: {
            "name": "Wordle Vball",
            "exact_pattern": "‪(650) 346-8822‬, ‪(858) 735-9353‬, +1",
            "phone_combo": ["(650) 346-8822", "(858) 735-9353"],
            "unique_names": ["Wordle Vball"]
        }
    }

    # First, check if thread exactly matches any OTHER league
    # This is the most strict check to prevent mis-identification
    for other_id, other_info in league_identifiers.items():
        if other_id != league_id:
            if other_info["exact_pattern"] in thread_text or other_info["exact_pattern"] in thread_html:
                if debug:
                    logging.info(f"Thread matches exact pattern of league {other_id}, not {league_id}")
                return False

    # Now check if this thread matches the requested league
    if league_id not in league_identifiers:
        logging.warning(f"Invalid league ID: {league_id}")
        return False

    league_info = league_identifiers[league_id]
    league_name = league_info["name"]
    
    # 1. Check exact pattern (most reliable)
    exact_pattern = league_info["exact_pattern"]
    if exact_pattern in thread_text or exact_pattern in thread_html:
        logging.info(f"Found exact {league_name} annotation pattern in thread")
        return True
    
    # 2. Check phone number combination
    phone_combo = league_info["phone_combo"]
    all_phones_found = all(phone in thread_text for phone in phone_combo)
    
    # Only accept if ALL phones from this league are found AND no phones from other leagues
    if all_phones_found:
        # Check for conflicting phones from other leagues
        has_conflicting_phones = False
        for other_id, other_info in league_identifiers.items():
            if other_id != league_id:
                for other_phone in other_info["phone_combo"]:
                    # If a phone from another league that isn't in our league is found, it's a conflict
                    if other_phone not in phone_combo and other_phone in thread_text:
                        has_conflicting_phones = True
                        if debug:
                            logging.info(f"Thread has phone {other_phone} from league {other_id}")
                        break
                        
        if not has_conflicting_phones:
            logging.info(f"Found {league_name} phone number combination in thread")
            return True
        else:
            if debug:
                logging.info(f"Thread has conflicting phones from other leagues")
    
    # 3. Check for unique league name (fallback)
    unique_names = league_info["unique_names"]
    for name in unique_names:
        if name in thread_text:
            # Ensure no other league name is in the thread
            has_conflicting_names = False
            for other_id, other_info in league_identifiers.items():
                if other_id != league_id:
                    for other_name in other_info["unique_names"]:
                        if other_name in thread_text:
                            has_conflicting_names = True
                            if debug:
                                logging.info(f"Thread has name {other_name} from league {other_id}")
                            break
            
            if not has_conflicting_names:
                logging.info(f"Found {league_name} unique name in thread: {name}")
                return True
            else:
                if debug:
                    logging.info(f"Thread has conflicting names from other leagues")
    
    if debug:
        logging.info(f"Thread did not match criteria for league {league_id} ({league_name})")
        if thread_text:
            logging.info(f"Thread preview: {thread_text[:100]}...")

    # Default to false - no match for this league ID
    return False
