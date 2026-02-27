#!/usr/bin/env python3
"""
Items Research - Article Updater
Calls Claude API to generate fresh curated articles and updates index.html
Runs automatically at 7am and 7pm via GitHub Actions
"""

import anthropic
import json
import os
import re
from datetime import datetime

# Categories to curate
CATEGORIES = [
    {"id": "science",    "label": "Science"},
    {"id": "technology", "label": "Technology"},
    {"id": "birds",      "label": "Birds"},
    {"id": "warfare",    "label": "Modern Warfare"},
    {"id": "ai",         "label": "Artificial Intelligence"},
    {"id": "finance",    "label": "Financialization"},
]

ARTICLE_TYPES = ["research", "analysis", "commentary", "report"]

def fetch_articles_from_claude():
    """Ask Claude to generate fresh curated articles for each category."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    today = datetime.now().strftime("%B %Y")
    
    prompt = f"""You are a curator for a high-quality research and analysis digest called Items Research.
Today is {today}.

For each of the following categories, generate exactly 4 articles that represent the kind of high-quality, substantive content published in the last 10 days from sources like Nature, Science, Foreign Affairs, The Economist, MIT Technology Review, NEJM, War on the Rocks, Brookings Institution, RAND, Financial Times, Wired, arXiv, IISS, Council on Foreign Relations, Quanta Magazine, and similar outlets.

Categories: Science, Technology, Birds, Modern Warfare, Artificial Intelligence, Financialization

For each article provide:
- category (one of: science, technology, birds, warfare, ai, finance)
- type (one of: research, analysis, commentary, report)
- headline (specific, substantive, 10-15 words)
- source (real publication name)
- excerpt (2 sentences, substantive summary of findings or argument)
- url (use # as placeholder)

Return ONLY a valid JSON array of 24 articles (4 per category), no other text. Example format:
[
  {{
    "id": 1,
    "category": "science",
    "type": "research",
    "headline": "Example headline here",
    "source": "Nature",
    "date": "{today}",
    "excerpt": "First sentence of summary. Second sentence with key finding.",
    "url": "#"
  }}
]"""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    response_text = message.content[0].text.strip()
    
    # Extract JSON array from response
    match = re.search(r'\[.*\]', response_text, re.DOTALL)
    if not match:
        raise ValueError("No JSON array found in Claude response")
    
    articles = json.loads(match.group())
    
    # Ensure IDs are sequential
    for i, article in enumerate(articles, 1):
        article["id"] = i
    
    return articles

def update_index_html(articles):
    """Read index.html, replace the DEFAULT_ARTICLES array, write it back."""
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Build new DEFAULT_ARTICLES JS array
    articles_js = "const DEFAULT_ARTICLES = [\n"
    for article in articles:
        headline = article["headline"].replace("'", "\\'")
        excerpt  = article["excerpt"].replace("'", "\\'")
        articles_js += (
            f"  {{ id: {article['id']}, category: '{article['category']}', "
            f"type: '{article['type']}', headline: '{headline}', "
            f"source: '{article['source']}', date: '{article['date']}', "
            f"excerpt: '{excerpt}', url: '{article['url']}' }},\n"
        )
    articles_js += "];"
    
    # Replace existing DEFAULT_ARTICLES block
    new_content = re.sub(
        r'const DEFAULT_ARTICLES = \[.*?\];',
        articles_js,
        content,
        flags=re.DOTALL
    )
    
    if new_content == content:
        raise ValueError("Could not find DEFAULT_ARTICLES in index.html to replace")
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print(f"✅ Updated index.html with {len(articles)} fresh articles")

def main():
    print(f"🔄 Fetching fresh articles from Claude... ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    articles = fetch_articles_from_claude()
    print(f"✅ Received {len(articles)} articles")
    update_index_html(articles)
    print("🚀 Done! index.html is ready to deploy.")

if __name__ == "__main__":
    main()
