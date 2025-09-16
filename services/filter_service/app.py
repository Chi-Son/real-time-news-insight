import psycopg2
from confluent_kafka import Producer
import fasttext
from shared.postgresql_config import DB_CONFIG
# -------------------------------
# Kết nối DB
# -------------------------------
conn = psycopg2.connect(**DB_CONFIG)
conn.autocommit = True
cur = conn.cursor()

# -------------------------------
# Kafka producer config
# -------------------------------
#producer = Producer({'bootstrap.servers': 'localhost:9092'})
#topic_name = "raw_news"

# -------------------------------
# Load FastText model
# -------------------------------
model = fasttext.load_model("model_category.bin")

# -------------------------------
# Lấy last_processed_id
# -------------------------------
cur.execute("""
    SELECT last_processed_id 
    FROM filter_state 
    WHERE service_name='news_filter'
""")
row = cur.fetchone()
last_processed_id = row[0] if row else 0

print(f"Last processed ID: {last_processed_id}")

# -------------------------------
# Query các bản ghi mới từ news_links
# -------------------------------
cur.execute("""
    SELECT id, url, title 
    FROM news_links 
    WHERE id > %s
    ORDER BY id ASC
""", (last_processed_id,))
rows = cur.fetchall()

if not rows:
    print("Không có tin mới.")
    exit(0)

# -------------------------------
# Lọc + gửi vào Kafka
# -------------------------------
processed_ids = []
for r in rows:
    news_id, url, title = r

    # Predict với fastText
    label, prob = model.predict(title)
    label = label[0].replace("__label__", "")  # fastText trả về "__label__news"

    if label == "news" and prob > 0.7:  # Ngưỡng tin cậy
        msg = {
            "id": news_id,
            "url": url,
            "title": title,
            "category": label,
            "confidence": float(prob)
        }
        # Gửi Kafka
        producer.produce(topic_name, str(msg).encode("utf-8"))
        print(f"Sent to Kafka: {msg}")

    processed_ids.append(news_id)

producer.flush()

# -------------------------------
# Update last_processed_id
# -------------------------------
if processed_ids:
    max_id = max(processed_ids)
    cur.execute("""
        UPDATE filter_state
        SET last_processed_id = %s
        WHERE service_name='news_filter'
    """, (max_id,))
    print(f"Updated last_processed_id = {max_id}")

cur.close()
conn.close()
