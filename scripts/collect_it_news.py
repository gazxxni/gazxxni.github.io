import os
import json
import datetime
import feedparser
from pathlib import Path

RSS_FEEDS = {
    "기술 뉴스": [
        "https://news.hada.io/rss/news",
        "https://techcrunch.com/feed/",
    ],
    "개발 트렌드": [
        "https://news.ycombinator.com/rss",
    ],
    "한국 IT": [
        "https://yozm.wishket.com/rss.xml",
    ]
}

DATA_DIR = "it_news_data"
MAX_ITEMS_PER_FEED = 5

def fetch_rss_feed(url, category):
    try:
        print(f"[INFO] Fetching {category}: {url}")
        feed = feedparser.parse(url)
        
        items = []
        for entry in feed.entries[:MAX_ITEMS_PER_FEED]:
            item = {
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", entry.get("updated", "")),
                "summary": entry.get("summary", entry.get("description", ""))[:300],
                "category": category,
                "source": feed.feed.get("title", url)
            }
            items.append(item)
        
        print(f"[OK] Fetched {len(items)} items from {category}")
        return items
    
    except Exception as e:
        print(f"[ERROR] Failed to fetch {url}: {e}")
        return []

def load_existing_data():
    today = datetime.date.today()
    filename = f"{DATA_DIR}/{today.strftime('%Y-%m-%d')}.json"
    
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"date": str(today), "articles": []}

def save_data(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    
    today = datetime.date.today()
    filename = f"{DATA_DIR}/{today.strftime('%Y-%m-%d')}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] Saved to {filename}")

def collect_news():
    print("[INFO] Starting news collection...")
    
    data = load_existing_data()
    existing_links = {article["link"] for article in data["articles"]}
    
    new_count = 0
    
    for category, feeds in RSS_FEEDS.items():
        for feed_url in feeds:
            items = fetch_rss_feed(feed_url, category)
            
            for item in items:
                if item["link"] not in existing_links:
                    data["articles"].append(item)
                    existing_links.add(item["link"])
                    new_count += 1
    
    save_data(data)
    
    print(f"\n{'='*50}")
    print(f"[DONE] Collected {new_count} new articles")
    print(f"[INFO] Total articles today: {len(data['articles'])}")
    print(f"{'='*50}")

if __name__ == "__main__":
    collect_news()
