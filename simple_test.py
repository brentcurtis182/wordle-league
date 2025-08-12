import re
import html

# This is the HTML from Nanna's message that you shared
html_content = """
<div _ngcontent-ng-c420718552="" class="subject-content-container bubble"><!----><gv-annotation _ngcontent-ng-c420718552="" aria-hidden="true" class="content ng-star-inserted" _nghost-ng-c2555192858="">Wordle 1,500 6/6

<img alt="⬜" aria-label="white large square" class="element medium" src="https://www.gstatic.com/voice-fe/emoji/noto_v2/emoji_u2b1c.png">🟩<img alt="⬜" aria-label="white large square" class="element medium" src="https://www.gstatic.com/voice-fe/emoji/noto_v2/emoji_u2b1c.png"><img alt="⬜" aria-label="white large square" class="element medium" src="https://www.gstatic.com/voice-fe/emoji/noto_v2/emoji_u2b1c.png">🟩
<img alt="⬜" aria-label="white large square" class="element medium" src="https://www.gstatic.com/voice-fe/emoji/noto_v2/emoji_u2b1c.png">🟩<img alt="⬜" aria-label="white large square" class="element medium" src="https://www.gstatic.com/voice-fe/emoji/noto_v2/emoji_u2b1c.png"><img alt="⬜" aria-label="white large square" class="element medium" src="https://www.gstatic.com/voice-fe/emoji/noto_v2/emoji_u2b1c.png">🟩
<img alt="⬜" aria-label="white large square" class="element medium" src="https://www.gstatic.com/voice-fe/emoji/noto_v2/emoji_u2b1c.png">🟩<img alt="⬜" aria-label="white large square" class="element medium" src="https://www.gstatic.com/voice-fe/emoji/noto_v2/emoji_u2b1c.png"><img alt="⬜" aria-label="white large square" class="element medium" src="https://www.gstatic.com/voice-fe/emoji/noto_v2/emoji_u2b1c.png">🟩
<img alt="⬜" aria-label="white large square" class="element medium" src="https://www.gstatic.com/voice-fe/emoji/noto_v2/emoji_u2b1c.png">🟩🟨<img alt="⬜" aria-label="white large square" class="element medium" src="https://www.gstatic.com/voice-fe/emoji/noto_v2/emoji_u2b1c.png">🟩
🟩🟩<img alt="⬜" aria-label="white large square" class="element medium" src="https://www.gstatic.com/voice-fe/emoji/noto_v2/emoji_u2b1c.png"><img alt="⬜" aria-label="white large square" class="element medium" src="https://www.gstatic.com/voice-fe/emoji/noto_v2/emoji_u2b1c.png">🟩
🟩🟩🟩🟩🟩</gv-annotation><!----></div>
"""

# Write test results to a file instead of console
with open('diagnosis_results.txt', 'w', encoding='utf-8') as f:
    # Extract plain text
    text = html_content
    text = text.replace('<br>', '\n')
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = html.unescape(text)
    plain_text = text.strip()
    
    f.write(f"Extracted plain text:\n{plain_text}\n\n")
    
    # These are the patterns from the code
    wordle_patterns = [
        re.compile(r'Wordle\s+#?(\d+(?:,\d+)?)\s+(\d+)/6'),  # Standard format
        re.compile(r'Wordle[:\s]+#?(\d+(?:,\d+)?)\s*[:\s]+(\d+)/6'),  # With colons
        re.compile(r'Wordle[^\d]*(\d+(?:,\d+)?)[^\d]*(\d+)/6')  # Very flexible
    ]
    
    f.write("Trying to match Wordle score patterns:\n")
    for i, pattern in enumerate(wordle_patterns):
        matches = pattern.findall(plain_text)
        f.write(f"Pattern {i+1}: {pattern.pattern}\n")
        f.write(f"  Matches: {matches}\n")
    
    # Also try with the raw HTML
    f.write("\nTrying to match directly against raw HTML:\n")
    for i, pattern in enumerate(wordle_patterns):
        matches = pattern.findall(html_content)
        f.write(f"Pattern {i+1}: {pattern.pattern}\n")
        f.write(f"  Matches: {matches}\n")
    
    # Try a more general pattern that might catch scores
    f.write("\nTrying with a more general pattern:\n")
    general_pattern = re.compile(r'Wordle[^0-9]*(\d[\d,]*)[^0-9]*(\d)[^0-9]6')
    matches = general_pattern.findall(plain_text)
    f.write(f"General pattern: {general_pattern.pattern}\n")
    f.write(f"  Matches: {matches}\n")
    
    # Count alt text matches
    alt_text_pattern = re.compile(r'alt="([⬛⬜])"')
    alt_text_matches = alt_text_pattern.findall(html_content)
    f.write(f"\nAlt text matches: {len(alt_text_matches)}\n")
    
    # Try enhanced alt text pattern
    enhanced_alt_pattern = re.compile(r'alt="([⬛⬜🟨🟩])"')
    enhanced_matches = enhanced_alt_pattern.findall(html_content)
    f.write(f"Enhanced alt text matches: {len(enhanced_matches)}\n")
    
print("Analysis complete! Results written to diagnosis_results.txt")
