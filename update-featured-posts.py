#!/usr/bin/env python3
"""
update-featured-posts.py
Fetches latest posts from estherops.tech RSS and updates featured-posts.json.
Run manually or via cron (1st and 15th of each month).
"""

import json
import subprocess
import sys
import urllib.request
from datetime import datetime
from xml.etree import ElementTree as ET
import re, html

RSS_URL = 'https://estherops.tech/index.xml'
JSON_PATH = '/home/esther/finksecurity-site/featured-posts.json'
REPO_PATH = '/home/esther/finksecurity-site'
MAX_POSTS = 3

def strip_html(text):
    return re.sub(r'<[^>]+>', '', text).strip()

def get_category(url):
    if '/reports/' in url: return 'REPORTS'
    if '/methods/' in url: return 'METHODS'
    if '/intelligence/' in url: return 'INTELLIGENCE'
    if '/labs/' in url: return 'LABS'
    return 'RESEARCH'

def parse_date(date_str):
    for fmt in ('%a, %d %b %Y %H:%M:%S %z', '%a, %d %b %Y %H:%M:%S %Z'):
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return date_str[:10]

print("Fetching RSS feed...")
try:
    with urllib.request.urlopen(RSS_URL, timeout=15) as r:
        xml = r.read()
except Exception as e:
    print(f"ERROR: Could not fetch RSS: {e}")
    sys.exit(1)

root = ET.fromstring(xml)
ns = {'atom': 'http://www.w3.org/2005/Atom'}
items = root.findall('.//item')[:MAX_POSTS]

posts = []
for item in items:
    title = item.findtext('title', '').strip()
    url = item.findtext('link', '').strip()
    pub_date = item.findtext('pubDate', '')
    desc = strip_html(item.findtext('description', ''))[:140].strip() + '...'
    posts.append({
        "title": title,
        "url": url,
        "date": parse_date(pub_date),
        "category": get_category(url),
        "summary": desc,
        "thumbnail": ""
    })
    print(f"  + {title[:60]}")

with open(JSON_PATH, 'w') as f:
    json.dump(posts, f, indent=2)
print(f"\nWrote {len(posts)} posts to featured-posts.json")

# Commit and push
print("Committing...")
cmds = [
    ['git', '-C', REPO_PATH, 'add', 'featured-posts.json'],
    ['git', '-C', REPO_PATH, 'commit', '-m', 'Update featured blog posts from estherops.tech RSS'],
    ['git', '-C', REPO_PATH, 'pull', '--rebase'],
    ['git', '-C', REPO_PATH, 'push'],
]
for cmd in cmds:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and 'nothing to commit' not in result.stdout and 'nothing to commit' not in result.stderr:
        print(f"ERROR: {' '.join(cmd)}\n{result.stderr}")
        sys.exit(1)
    print(f"OK: {' '.join(cmd[2:])}")

print("\nDone.")
