import json
import re

with open('file_sharing_after.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract the JSON embedded in the HTML
match = re.search(r'window\.__LIGHTHOUSE_JSON__ = (\{.*?\});</script>', html, re.DOTALL)
if match:
    data = json.loads(match.group(1))
    categories = data.get('categories', {})
    for cat_id, cat in categories.items():
        score = cat.get('score')
        print(f"{cat.get('title')}: {int(score * 100) if score is not None else 'N/A'}")
else:
    print("Could not find Lighthouse JSON in HTML")
