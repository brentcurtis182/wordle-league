import os
import re
import sys
from bs4 import BeautifulSoup

# Force UTF-8 output encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def analyze_dom_snapshot(filename):
    """Analyze a DOM snapshot to find Wordle scores and phone numbers"""
    print(f"Analyzing DOM snapshot: {filename}")
    
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return
    
    with open(filename, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find all elements that might contain Wordle scores
    annotations = soup.select("gv-annotation.preview")
    print(f"Found {len(annotations)} gv-annotation.preview elements")
    
    aria_elements = soup.select('[aria-label*="Wordle"]')
    print(f"Found {len(aria_elements)} elements with Wordle in aria-label")
    
    hidden_elements = soup.select(".cdk-visually-hidden")
    print(f"Found {len(hidden_elements)} visually-hidden elements")
    
    # Define regex for Wordle scores
    wordle_regex = re.compile(r'Wordle ([\d,]+)(?:\s+#([\d,]+))?\s+([1-6X])/6')
    phone_regex = re.compile(r'\((\d{3})\)[\s-]*(\d{3})[\s-]*(\d{4})')
    
    # Check for Wordle patterns in annotation elements
    print("\n--- Checking annotation elements ---")
    for i, elem in enumerate(annotations):
        text = elem.get_text(strip=True)
        print(f"\nAnnotation {i+1}: {text[:100].encode('ascii', 'replace').decode('ascii')}...")
        
        match = wordle_regex.search(text)
        if match:
            wordle_num = match.group(1).replace(',', '')
            score = match.group(3)
            print(f"✅ FOUND WORDLE: #{wordle_num} Score: {score}/6")
            
            # Look for phone numbers
            phone_matches = phone_regex.findall(text)
            if phone_matches:
                raw_phone = f"{phone_matches[0][0]}{phone_matches[0][1]}{phone_matches[0][2]}"
                print(f"   Phone: {raw_phone} (raw), 1{raw_phone} (with leading 1)")
    
    # Check aria-label elements
    print("\n--- Checking aria-label elements ---")
    for i, elem in enumerate(aria_elements):
        text = elem.get('aria-label', '')
        print(f"\nAria {i+1}: {text[:100].encode('ascii', 'replace').decode('ascii')}...")
        
        match = wordle_regex.search(text)
        if match:
            wordle_num = match.group(1).replace(',', '')
            score = match.group(3)
            print(f"✅ FOUND WORDLE: #{wordle_num} Score: {score}/6")
            
            # Look for phone numbers
            phone_matches = phone_regex.findall(text)
            if phone_matches:
                raw_phone = f"{phone_matches[0][0]}{phone_matches[0][1]}{phone_matches[0][2]}"
                print(f"   Phone: {raw_phone} (raw), 1{raw_phone} (with leading 1)")
    
    # Check for Wordle scores in hidden elements (often contain full text)
    print("\n--- Checking visually-hidden elements ---")
    wordle_count = 0
    for i, elem in enumerate(hidden_elements):
        text = elem.get_text(strip=True)
        if "Wordle" in text and "/6" in text:
            wordle_count += 1
            print(f"\nHidden {i+1}: {text[:100].encode('ascii', 'replace').decode('ascii')}...")
            
            match = wordle_regex.search(text)
            if match:
                wordle_num = match.group(1).replace(',', '')
                score = match.group(3)
                print(f"✅ FOUND WORDLE: #{wordle_num} Score: {score}/6")
                
                # Look for phone numbers
                phone_matches = phone_regex.findall(text)
                if phone_matches:
                    raw_phone = f"{phone_matches[0][0]}{phone_matches[0][1]}{phone_matches[0][2]}"
                    print(f"   Phone: {raw_phone} (raw), 1{raw_phone} (with leading 1)")
    
    print(f"\nTotal Wordle scores found in hidden elements: {wordle_count}")
    
    # Check all text for any Wordle patterns we might have missed
    all_text = soup.get_text()
    all_matches = wordle_regex.findall(all_text)
    print(f"\nTotal Wordle matches in entire document: {len(all_matches)}")
    
    for match in all_matches[:10]:  # Show first 10
        wordle_num = match[0].replace(',', '')
        score = match[2]
        print(f"- Wordle #{wordle_num} Score: {score}/6")

if __name__ == "__main__":
    # Check the latest DOM snapshot in the dom_captures folder
    dom_dir = "dom_captures"
    pal_files = [f for f in os.listdir(dom_dir) if f.startswith("dom_PAL_") and f.endswith(".html")]
    
    if pal_files:
        # Get the most recent PAL file
        latest_pal = sorted(pal_files)[-1]
        analyze_dom_snapshot(os.path.join(dom_dir, latest_pal))
    else:
        print("No PAL DOM snapshots found in dom_captures folder")
