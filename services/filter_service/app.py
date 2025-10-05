import psycopg2
import fasttext
import os
import requests
import time
from bs4 import BeautifulSoup
from shared.postgresql_config import DB_CONFIG
from shared.kafka_config import get_kafka_producer
import json
# -------------------------------
# Hàm lấy cursor DB
# -------------------------------
def get_db_cursor():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    return conn, conn.cursor()

# -------------------------------
# Kafka producer với retry
# -------------------------------
producer = None
while producer is None:
    try:
        producer = get_kafka_producer()
    except Exception as e:
        print(f"Kafka chưa sẵn sàng: {e}, retry sau 5s...")
        time.sleep(5)

topic_name = "raw_links"

# -------------------------------
# Load FastText model
# -------------------------------
MODEL_PATH = "/app/models/model_news_filter.bin"
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

print(f"Loading FastText model from {MODEL_PATH} ...")
model = fasttext.load_model(MODEL_PATH)

# -------------------------------
# Hàm lấy title từ URL
# -------------------------------
def extract_title(url):
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        if soup.title:
            return soup.title.string.strip()
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()
        return None
    except Exception as e:
        print(f"Lỗi extract title {url}: {e}")
        return None

# -------------------------------
# Vòng lặp chính
# -------------------------------
while True:
    conn, cur = get_db_cursor()

    # Lấy last_processed_id
    cur.execute("""
        SELECT last_processed_id 
        FROM filter_state 
        WHERE service_name='news_filter'
    """)
    row = cur.fetchone()
    last_processed_id = row[0] if row else 0
    print(f"Last processed ID: {last_processed_id}")

    # Lấy các bản ghi mới
    cur.execute("""
        SELECT id, url, category
        FROM news_links
        WHERE id > %s
        ORDER BY id ASC
    """, (last_processed_id,))

    rows = cur.fetchall()

    processed_ids = []

    for news_id, url, category in rows:
        print(f"Processing ID={news_id}, URL={url}, category={category}")

        title = None
        if category == "news":
            title = extract_title(url)
            if title:
                # Predict với model FastText
                labels, probs = model.predict(title)
                label = labels[0].replace("__label__", "")
                confidence = float(probs[0])

                # Chỉ lấy tin relevant > 0.3
                if label == "relevent" and confidence > 0.3:
                    msg = {
                        "id": news_id,
                        "url": url,
                        "category": category,
                    }
                    try:
                        producer.produce(topic_name, json.dumps(msg).encode("utf-8"))
                        print(f"Sent to Kafka: {msg}")
                    except Exception as e:
                        print(f"Lỗi gửi Kafka cho ID={news_id}: {e}")
        else:
            # Category khác news thì gửi thẳng
            msg = {
                "id": news_id,
                "url": url,
                "category": category
            }
            try:
                producer.produce(topic_name, json.dumps(msg).encode("utf-8"))
                print(f"Sent (non-news) to Kafka: {msg}")
            except Exception as e:
                print(f"Lỗi gửi Kafka cho ID={news_id}: {e}")
        # Luôn đánh dấu ID đã xử lý, bất kể có gửi Kafka hay không
        processed_ids.append(news_id)

    producer.flush()

    if processed_ids:
        max_id = max(processed_ids)
        cur.execute("""
            INSERT INTO filter_state(service_name, last_processed_id)
            VALUES('news_filter', %s)
            ON CONFLICT (service_name) DO UPDATE
            SET last_processed_id = EXCLUDED.last_processed_id
        """, (max_id,))
        print(f"Updated last_processed_id = {max_id}")

    cur.close()
    conn.close()
    time.sleep(5)
