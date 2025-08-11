import json ,feedparser, time
from shared.utils import url_to_hash, is_duplicate
from shared.kafka_config import get_kafka_producer
from shared.redis_connect import redis_connection
#key của crawl trên redis
REDIS_KEY = "crawled_urls"
r= redis_connection()

# đặt topic để gửi vào
producer=get_kafka_producer()
KAFKA_TOPIC="news.raw_links"

# Load json
def load_sources(path="rss_sources.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Crawl và lọc trùng
def crawl_rss():
    sources = load_sources()
    for category, urls in sources.items():
        print(f"\n📰 Category: {category}", flush=True)
        for url in urls:
            print(f"🔗 Crawling: {url}", flush=True)
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:  
                link_hash = url_to_hash(entry.link)
                if is_duplicate (r,REDIS_KEY,link_hash):
                    print(f"⛔️ Trùng: {entry.title}", flush=True)
                    continue
                # gửi vào kafka
                print(f"✅ Mới: {entry.title}", flush=True)
                print(f"   {entry.link}", flush=True)
                data = {
                    "url": entry.link,
                    "title": entry.title,
                    "category": category,
                    "published": entry.published if "published" in entry else None
                }  
                producer.send(KAFKA_TOPIC,value=data)
                print("Đã gửi")

if __name__ == "__main__":
    while True:
        print("⏰ Bắt đầu crawl RSS", flush=True)
        crawl_rss()
        print("🛌 Ngủ 2 phút 30...\n", flush=True)
        time.sleep(300)  
