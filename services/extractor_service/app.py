import requests
from bs4 import BeautifulSoup
import logging
import psycopg2
import json
import os
import time
from urllib.parse import urlparse

from shared.kafka_config import get_kafka_consumer
from shared.encode_json import consume_json
from shared.postgresql_config import DB_CONFIG

# -------------------------------
# Logging setup
# -------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("extractor")

INPUT_TOPIC = "raw_links"
GROUP_ID = "extractor_group"

# Kafka consumer
consumer = get_kafka_consumer(topic=INPUT_TOPIC, group_id=GROUP_ID)
logger.info("URL Extractor service started.")

# -------------------------------
# Load nguồn báo từ file JSON
# -------------------------------
SOURCES_FILE = os.path.join(os.path.dirname(__file__), "rss_sources.json")
with open(SOURCES_FILE, "r", encoding="utf-8") as f:
    SOURCES_MAP = json.load(f)

# Map domain -> source name
DOMAIN_TO_SOURCE = {}
for source_name, urls in SOURCES_MAP.items():
    for url in urls:
        domain = urlparse(url).netloc.replace("www.", "")
        DOMAIN_TO_SOURCE[domain] = source_name

# -------------------------------
# DB helper
# -------------------------------
def get_db_cursor():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    return conn, conn.cursor()

# -------------------------------
# Extract content
# -------------------------------
def extract_article(url):
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"URL {url} trả về status {resp.status_code}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Lấy title
        title = None
        if soup.title:
            title = soup.title.string.strip()
        else:
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                title = og_title["content"].strip()

        # Lấy content
        paragraphs = soup.find_all("p")
        content = " ".join(p.get_text().strip() for p in paragraphs if p.get_text())
        if not content:
            content = soup.get_text()

        # Lấy published date (nếu có)
        published_at = None
        meta_date = soup.find("meta", property="article:published_time")
        if meta_date and meta_date.get("content"):
            published_at = meta_date["content"]

        return {
            "title": title,
            "content": content,
            "published_at": published_at
        }
    except Exception as e:
        logger.error(f"Lỗi extract {url}: {e}")
        return None

# -------------------------------
# Detect nguồn báo từ URL
# -------------------------------
def detect_source(url):
    domain = urlparse(url).netloc.replace("www.", "")
    return DOMAIN_TO_SOURCE.get(domain, "Unknown")

# -------------------------------
# Main loop
# -------------------------------
for message in consumer:
    try:
        msg = consume_json(message)
        news_id = msg.get("id")
        url = msg.get("url")

        if not news_id or not url:
            logger.warning(f"Bỏ qua message không hợp lệ: {msg}")
            continue

        logger.info(f"Đang xử lý ID={news_id}, URL={url}")

        article = extract_article(url)
        if not article:
            continue

        source = detect_source(url)

        # Lưu vào Postgres
        conn, cur = get_db_cursor()
        try:
            cur.execute("""
                INSERT INTO news_content(id, title, content, source, published_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (news_id, article["title"], article["content"], source, article["published_at"]))
            logger.info(f"Đã lưu bài ID={news_id}, source={source}")
        finally:
            cur.close()
            conn.close()

    except Exception as e:
        logger.error(f"Lỗi xử lý message: {e}")
        time.sleep(1)
