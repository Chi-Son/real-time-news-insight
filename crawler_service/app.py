import json
import feedparser
import redis
import hashlib
import time
import os
import re

# Kết nối đến Redis
redis_host = os.getenv("REDIS_HOST", "localhost")  # dùng biến môi trường
r = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)

# Set name dùng để chứa URL đã crawl
REDIS_KEY = "crawled_urls"

# Hàm tạo khóa hash để tránh URL dài và lộn xộn
def url_to_hash(url):
    # Lấy ID bài báo ở cuối URL
    match = re.search(r'-(\d+)\.html', url)
    if match:
        article_id = match.group(1)
    else:
        # Nếu không match được thì fallback lại dùng URL đầy đủ
        article_id = url
    return hashlib.sha256(article_id.encode()).hexdigest()

# Load danh sách nguồn từ file JSON
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
            for entry in feed.entries[:3]:  # Lấy 3 tin mới nhất
                link_hash = url_to_hash(entry.link)

                # Kiểm tra nếu đã tồn tại trong Redis thì bỏ qua
                if r.sismember(REDIS_KEY, link_hash):
                    print(f"⛔️ Trùng: {entry.title}", flush=True)
                    continue

                # Nếu chưa có thì xử lý bài viết
                print(f"✅ Mới: {entry.title}", flush=True)
                print(f"   {entry.link}", flush=True)

                # Lưu vào Redis và đặt thời gian sống (TTL)
                r.sadd(REDIS_KEY, link_hash)
                r.expire(REDIS_KEY, 43200)  # TTL: 86400 giây = 1 ngày

if __name__ == "__main__":
    while True:
        print("⏰ Bắt đầu crawl RSS", flush=True)
        crawl_rss()
        print("🛌 Ngủ 2 phút 30...\n", flush=True)
        time.sleep(300)  # 5 phút
