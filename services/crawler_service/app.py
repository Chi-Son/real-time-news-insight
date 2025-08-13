import json ,feedparser, time ,os
from shared.utils import url_to_hash, is_duplicate
from shared.kafka_config import get_kafka_producer,on_success, on_error
from shared.redis_connect import redis_connection
#key của crawl trên redis
REDIS_KEY = "crawled_urls"
r= redis_connection()

# đặt topic để gửi vào
producer=get_kafka_producer()
KAFKA_TOPIC="raw_links"

# Load json
def load_sources():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rss_sources.json")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        return json.loads(content)

# Crawl 
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
                producer.send(KAFKA_TOPIC,value=data).add_callback(on_success).add_errback(on_error)
                producer.flush()
                print("Đã gửi")

if __name__ == "__main__":
    while True:
        print("⏰ Bắt đầu crawl RSS", flush=True)
        crawl_rss()
        time.sleep(300)  
