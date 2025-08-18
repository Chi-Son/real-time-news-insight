import json ,feedparser, time ,os, logging
from shared.utils import url_to_hash, is_duplicate
from shared.kafka_config import get_kafka_producer
from shared.encode_json import send_json, delivery_report
from shared.redis_connect import redis_connection
#key của crawl trên redis
REDIS_KEY = "crawled_urls"
r= redis_connection()

# đặt topic để gửi vào
producer=get_kafka_producer()
KAFKA_TOPIC="raw_links"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
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
        logger.info(f"Category: {category}")
        for url in urls:
            logger.info(f"Crawling: {url}")
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:  
                link_hash = url_to_hash(entry.link)
                if is_duplicate(r, REDIS_KEY, link_hash):
                    logger.info(f"⛔️ Trùng: {entry.title}")
                    continue

                logger.info(f"✅ Mới: {entry.title} | {entry.link}")
                data = {
                    "url": entry.link,
                    "title": entry.title,
                    "category": category,
                    "published": getattr(entry, "published", None)
                }
                send_json(producer, KAFKA_TOPIC, data)
                producer.poll(0)
                print("Đã gửi")

if __name__ == "__main__":
    while True:
        print("⏰ Bắt đầu crawl RSS", flush=True)
        crawl_rss()
        time.sleep(300)
