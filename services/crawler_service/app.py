import json
import feedparser
import time
import os
import logging
import psycopg2
from psycopg2.extras import execute_values
from shared.postgresql_config import DB_CONFIG
from shared.utils import url_to_hash, is_duplicate
from shared.redis_connect import redis_connection

REDIS_KEY = "crawled_urls"
r = redis_connection()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_sources():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rss_sources.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Insert batch vào PostgreSQL
def insert_links(rows):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    sql = """
    INSERT INTO news_links (url, category)
    VALUES %s
    ON CONFLICT (url) DO NOTHING;
    """
    execute_values(cur, sql, rows)
    conn.commit()

    cur.close()
    conn.close()

def crawl_rss():
    sources = load_sources()
    new_rows = []

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

                logger.info(f"✅ Mới ok: {entry.title} | {entry.link}")
                new_rows.append((entry.link, category))

    if new_rows:
        insert_links(new_rows)
        logger.info(f"📥 Đã chèn {len(new_rows)} link mới vào PostgreSQL")

if __name__ == "__main__":
    while True:
        print("s Bắt đầu crawl RSS", flush=True)
        crawl_rss()
        time.sleep(300)  
