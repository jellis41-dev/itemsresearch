#!/usr/bin/env python3
import anthropic
import json
import os
import re
from datetime import datetime

def fetch_articles_from_claude():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    today = datetime.now().strftime("%B %Y")
    prompt = f"""You are a curator for a high-quality research and analysis digest called Items Research.
Today is {today}.

For each of the following categories, generate exactly 4 articles from the last 10 days from sources like Nature, Science, Foreign Affairs, The Economist, MIT Technology Review, NEJM, War on the Rocks, Brookings, RAND, Financial Times, Wired, arXiv, Council on Foreign Relations, Quanta Magazine.

Categories: Science, Technology, Birds, Modern Warfare, Artificial Intelligence, Financialization

Return ONLY a valid JSON array of 24 articles. Each article must have: id, category (science/technology/birds/warfare/ai/finance), type (research/analysis/commentary/report), headline, source, date, excerpt (2 short sentences max), url (#).

Example:
[{{"id":1,"category":"science","type":"research","headline":"Example headline","source":"Nature","date":"{today}","excerpt":"First sentence. Second sentence.","url":"#"}}]"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )
    response_text = message.content[0].text.strip()
    response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
    response_text = re.sub(r'\s*```$', '', response_text).strip()
    try:
        articles = json.loads(response_text)
    except json.JSONDecodeError:
        match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON found: {response_text[:300]}")
        articles = json.loads(match.group())
    for i, article in enumerate(articles, 1):
        article["id"] = i
    return articles

def update_index_html(articles):
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
    articles_js = "const DEFAULT_ARTICLES = [\n"
    for article in articles:
        headline = article["headline"].replace("'", "\\'")
        excerpt = article["excerpt"].replace("'", "\\'")
        articles_js += f"  {{ id: {article['id']}, category: '{article['category']}', type: '{article['type']}', headline: '{headline}', source: '{article['source']}', date: '{article['date']}', excerpt: '{excerpt}', url: '{article['url']}' }},\n"
    articles_js += "];"
    new_content = re.sub(r'const DEFAULT_ARTICLES = \[.*?\];', articles_js, content, flags=re.DOTALL)
    if new_content == content:
        raise ValueError("Could not find DEFAULT_ARTICLES in index.html")
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"✅ Updated index.html with {len(articles)} articles")

def main():
    print(f"🔄 Fetching articles... ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    articles = fetch_articles_from_claude()
    print(f"✅ Got {len(articles)} articles")
    update_index_html(articles)
    print("🚀 Done!")

if __name__ == "__main__":
    main()
