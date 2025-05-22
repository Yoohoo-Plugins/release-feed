#!/usr/bin/env python3
import os
import requests
import feedparser
from feedgen.feed import FeedGenerator
from datetime import datetime

# Load configuration
token = os.getenv('GITHUB_TOKEN')
org = os.getenv('ORG', 'strangerstudios')
headers = {'Authorization': f'token {token}'}

# Initialize feed
g = FeedGenerator()
g.id(f'https://github.com/{org}')
g.title(f'{org} Releases - Latest per Repo')
g.link(href=f'https://{org}.github.io', rel='alternate')
g.link(href='releases.xml', rel='self')
g.description(f'Latest release from each repo in the {org} organization')

# 1. List all public repos via GitHub API
repos = []
page = 1
while True:
    r = requests.get(
        f'https://api.github.com/orgs/{org}/repos',
        headers=headers,
        params={'per_page': 100, 'page': page}
    )
    data = r.json()
    if not data:
        break
    repos.extend(data)
    page += 1

# 2. Fetch only the latest release per repo via Atom feed
items = []
for repo in repos:
    name = repo['name']
    feed_url = f'https://github.com/{org}/{name}/releases.atom'
    parsed = feedparser.parse(feed_url)
    if not parsed.entries:
        continue
    entry = parsed.entries[0]
    # Determine parsed date (published or updated)
    dt_struct = entry.get('published_parsed') or entry.get('updated_parsed')
    if not dt_struct:
        # Skip if no date info
        continue
    published_dt = datetime(*dt_struct[:6])
    # Use entry.published or entry.updated for human-readable date
    published_str = getattr(entry, 'published', getattr(entry, 'updated', None))
    items.append({
        'title': entry.title,
        'link': entry.link,
        'id': entry.id,
        'published': published_dt,
        'published_str': published_str,
        'summary': entry.summary
    })

# 3. Sort items by published date ascending (oldest first)
items.sort(key=lambda x: x['published'])

# 4. Populate feed entries
for it in items:
    fe = g.add_entry()
    fe.id(it['id'])
    fe.title(it['title'])
    fe.link(href=it['link'])
    fe.published(it['published_str'])
    fe.summary(it['summary'] or '—')

# 5. Write RSS file
g.rss_file('releases.xml')