import os
from bs4 import BeautifulSoup

def highlight_top_player(html_path):
    """Highlight the player with the lowest average in the All-Time Stats table"""
    print(f"Processing {html_path}...")
    
    try:
        # Read the HTML file
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find the All-Time Stats container
        all_time_container = soup.find('div', {'class': 'all-time-container'})
        if not all_time_container:
            print(f"Could not find all-time container in {html_path}")
            return False
        
        # Find the table in the All-Time Stats section
        table = all_time_container.find('table')
        if not table:
            print(f"Could not find table in all-time section")
            return False
        
        # Get all rows in the table body
        tbody = table.find('tbody')
        if not tbody:
            print(f"Could not find table body")
            return False
            
        rows = tbody.find_all('tr')
        if not rows:
            print(f"No rows found in table")
            return False
        
        # Find the lowest average score
        best_avg = float('inf')
        best_row = None
        
        for row in rows:
            # Get the average score (3rd column)
            cols = row.find_all('td')
            if len(cols) >= 3:
                try:
                    # Get the text of the average column
                    avg_text = cols[2].get_text().strip()
                    
                    # Check if it's a valid number (not '-' or empty)
                    if avg_text and avg_text != '-':
                        avg_score = float(avg_text)
                        
                        # Update if this is the lowest average
                        if avg_score < best_avg:
                            best_avg = avg_score
                            best_row = row
                except (ValueError, IndexError) as e:
                    # Skip rows with non-numeric averages
                    print(f"Skipping row with invalid average: {e}")
                    continue
        
        # Highlight the row with the lowest average
        if best_row:
            # Add the highlighting class (same as weekly table)
            best_row['class'] = best_row.get('class', []) + ['highlight']
            
            # Also add inline style for consistency
            best_row['style'] = 'background-color: rgba(106, 170, 100, 0.2);'
            
            print(f"Highlighted player with average score {best_avg}")
        else:
            print(f"No valid rows found to highlight")
            return False
        
        # Save the file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        print(f"Successfully highlighted top player in {html_path}")
        return True
        
    except Exception as e:
        print(f"Error processing {html_path}: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    # Define the main directories
    website_dir = "website_export"
    
    # League paths
    league_paths = [
        os.path.join(website_dir, "index.html"),            # Wordle Warriorz
        os.path.join(website_dir, "gang", "index.html"),    # Wordle Gang
        os.path.join(website_dir, "pal", "index.html"),     # Wordle PAL
        os.path.join(website_dir, "party", "index.html"),   # Wordle Party
        os.path.join(website_dir, "vball", "index.html")    # Wordle Vball
    ]
    
    success_count = 0
    
    for path in league_paths:
        if os.path.exists(path):
            if highlight_top_player(path):
                success_count += 1
        else:
            print(f"File not found: {path}")
    
    print(f"Highlighted top player in {success_count} out of {len(league_paths)} files")

if __name__ == "__main__":
    main()
