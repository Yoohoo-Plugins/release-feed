#!/usr/bin/env python3
import os, requests
from feedgen.feed import FeedGenerator

ORG = os.getenv('ORG')
TOKEN = os.getenv('GITHUB_TOKEN')
HEADERS = {'Authorization': f'token {TOKEN}'}

# Initialize feed
fg = FeedGenerator()
fg.id(f'https://github.com/{ORG}')
fg.title(f'{ORG} Releases')
fg.link(href=f'https://{ORG}.github.io', rel='alternate')
fg.link(href='releases.xml', rel='self')
fg.description(f'All releases across the {ORG} organization')

# 1. List all repos
repos = []
page = 1
while True:
    resp = requests.get(f'https://api.github.com/orgs/{ORG}/repos',
                        params={'per_page': 100, 'page': page},
                        headers=HEADERS)
    data = resp.json()
    if not data:
        break
    repos.extend(data)
    page += 1

# 2. For each repo, fetch its releases
items = []
for repo in repos:
    name = repo['name']
    releases = requests.get(
        f'https://api.github.com/repos/{ORG}/{name}/releases',
        headers=HEADERS
    ).json()
    for rel in releases:
        # skip drafts
        if rel.get('draft'):
            continue
        items.append({
            'title': f"{name}: {rel['name'] or rel['tag_name']}",
            'link': rel['html_url'],
            'id': rel['url'],
            'published': rel['published_at'],
            'summary': rel.get('body', '').strip()
        })

# 3. Sort by published date descending, limit last 50
items = sorted(items, key=lambda x: x['published'], reverse=True)[:50]

# 4. Add items to feed
for it in items:
    fe = fg.add_entry()
    fe.id(it['id'])
    fe.title(it['title'])
    fe.link(href=it['link'])
    fe.published(it['published'])
    fe.summary(it['summary'] or '—')

# 5. Write out
fg.rss_file('releases.xml')
