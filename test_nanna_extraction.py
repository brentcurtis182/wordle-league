import re
import logging
import html

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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

# Step 1: Extract plain text from HTML (similar to what the extractor might do)
def extract_text_from_html(html_content):
    # Replace <br> with newlines and strip HTML tags
    text = html_content
    text = text.replace('<br>', '\n')
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = html.unescape(text)
    return text.strip()

plain_text = extract_text_from_html(html_content)
print(f"Extracted plain text:\n{plain_text}")

# Step 2: Apply the regex patterns used in integrated_auto_update.py
# These are the patterns from the code
wordle_patterns = [
    re.compile(r'Wordle\s+#?(\d+(?:,\d+)?)\s+(\d+)/6'),  # Standard format
    re.compile(r'Wordle[:\s]+#?(\d+(?:,\d+)?)\s*[:\s]+(\d+)/6'),  # With colons
    re.compile(r'Wordle[^\d]*(\d+(?:,\d+)?)[^\d]*(\d+)/6')  # Very flexible
]

# Try to match each pattern
print("\nTrying to match Wordle score patterns:")
for i, pattern in enumerate(wordle_patterns):
    matches = pattern.findall(plain_text)
    print(f"Pattern {i+1}: {pattern.pattern}")
    print(f"  Matches: {matches}")

# Also try with the raw HTML in case text extraction is losing something
print("\nTrying to match directly against raw HTML:")
for i, pattern in enumerate(wordle_patterns):
    matches = pattern.findall(html_content)
    print(f"Pattern {i+1}: {pattern.pattern}")
    print(f"  Matches: {matches}")

# Now let's try to extract emoji patterns
print("\nTrying to extract emoji pattern:")
emoji_pattern_regex = re.compile(r'((?:[⬛⬜🟨🟩]{5}[\s\n]*){1,6})', re.MULTILINE)
emoji_matches = re.findall(emoji_pattern_regex, plain_text)
print(f"Emoji matches: {emoji_matches}")

# Let's also check for alt text in img tags
print("\nChecking for alt text in img tags:")
alt_text_pattern = re.compile(r'alt="([⬛⬜])"')
alt_text_matches = alt_text_pattern.findall(html_content)
print(f"Alt text matches: {alt_text_matches}")

# Try an enhanced alt text pattern that includes all colors
print("\nTrying enhanced alt text pattern:")
enhanced_alt_pattern = re.compile(r'alt="([⬛⬜🟨🟩])"')
enhanced_matches = enhanced_alt_pattern.findall(html_content)
print(f"Enhanced alt text matches: {enhanced_matches}")

# Count rows in the emoji pattern by counting lines with 5 emoji squares
print("\nCounting rows in the emoji pattern:")
rows = [row for row in re.findall(r'[⬛⬜🟨🟩]{5}', plain_text)]
print(f"Found {len(rows)} rows: {rows}")
