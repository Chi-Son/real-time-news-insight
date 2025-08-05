import json
import feedparser

def load_sources(path="rss_sources.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def crawl_rss():
    sources = load_sources()
    for category, urls in sources.items():
        print(f"\n📰 Category: {category}")
        for url in urls:
            print(f"🔗 Crawling: {url}")
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:  
                print(f"- {entry.title}")
                print(f"  {entry.link}")
                print()

if __name__ == "__main__":
    crawl_rss()
