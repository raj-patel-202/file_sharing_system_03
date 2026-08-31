import urllib.request
r = urllib.request.urlopen('http://localhost:8000/files')
html = r.read().decode('utf-8', 'ignore')
print(f"<main in html: {'<main' in html}")
print(f'id="main-content" in html: {"id=\"main-content\"" in html}')
print(html[:500])
