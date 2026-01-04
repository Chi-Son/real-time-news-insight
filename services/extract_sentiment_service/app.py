import json
import logging
import time
import psycopg2
from psycopg2.extras import execute_values
from shared.postgresql_config import DB_CONFIG
from shared.kafka_config import get_kafka_consumer, get_kafka_producer
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
import os
import re
# =========================
# LOGGING
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentiment_extractor")

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)
# =========================
# KAFKA CONFIG
# =========================
INPUT_TOPIC = "extractor_topic"
OUTPUT_TOPIC = "extractor_sentiment"  
GROUP_ID = "extractor_sentiment_group"

consumer = get_kafka_consumer(topic=INPUT_TOPIC, group_id=GROUP_ID)
producer = get_kafka_producer()

# =========================
# LOAD SENTIMENT MODEL
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "ModelSentiment")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)

device = 0 if torch.cuda.is_available() else -1

sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model=model,
    tokenizer=tokenizer,
    device=device
)

logger.info("Sentiment pipeline loaded")

# =========================
# BATCH CONFIG
# =========================
BATCH_SIZE = 10
BATCH_TIMEOUT = 20  # giây
batch_messages = []
last_flush_time = time.time()
def save_to_db(batch_messages):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        sentiment_data = []
        topic_rels = set() 
        entity_rels = set() 

        for item in batch_messages:
            news_id = item['id']
            label = item['sentiment']['label']
            sentiment_data.append((news_id, label))

            for t_id in item['topic_ids']:
                topic_rels.add((news_id, t_id))
            
            for ent in item['entities']:
                # Kiểm tra xem entity_id có tồn tại và không None không
                if ent.get('entity_id') is not None:
                    try:
                        ent_id = int(ent['entity_id'])
                        entity_rels.add((news_id, ent_id))
                    except (ValueError, TypeError):
                        logger.warning(f"ID thực thể không hợp lệ: {ent.get('entity_id')} tại bài viết {news_id}")

        # Chuyển set về list
        topic_rels = list(topic_rels)
        entity_rels = list(entity_rels)

        # --- ĐOẠN IN RA ĐỂ DEBUG ---
        logger.info("="*30)
        logger.info(f"DEBUG: Dữ liệu chuẩn bị insert vào article_entity ({len(entity_rels)} records):")
        for rel in entity_rels:
            logger.info(f" -> Article ID: {rel[0]} | Entity ID: {rel[1]}")
        logger.info("="*30)
        # ---------------------------

        logger.info(f"Đang insert: {len(sentiment_data)} sentiment, {len(topic_rels)} topics, {len(entity_rels)} entities")

        # 1. Sentiment
        execute_values(cur, """
            INSERT INTO article_sentiment (id, sentiment) 
            VALUES %s ON CONFLICT (id) DO UPDATE SET sentiment = EXCLUDED.sentiment
        """, sentiment_data)

        # 2. Topic
        if topic_rels:
            execute_values(cur, "INSERT INTO public.article_topic (id, topic_id) VALUES %s ON CONFLICT DO NOTHING", topic_rels)

        # 3. Entity
        if entity_rels:
            execute_values(
                cur,
                "INSERT INTO public.article_entity (id, entity_id) VALUES %s ON CONFLICT DO NOTHING",
                entity_rels
            )

        conn.commit()
        logger.info("Batch đã được commit thành công vào DB")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"DB Error: {e}")
        logger.error(f"Dữ liệu Entity gây lỗi: {entity_rels}")
    finally:
        cur.close()
        conn.close()
# =========================
# MAIN LOOP
# =========================
while True:
    msg = consumer.poll(1.0)
    current_time = time.time()

    if batch_messages and (len(batch_messages) >= BATCH_SIZE or current_time - last_flush_time >= BATCH_TIMEOUT):
        save_to_db(batch_messages)

        for m in batch_messages:
            producer.produce(
                OUTPUT_TOPIC,
                key=str(m["id"]),
                value=json.dumps(m).encode("utf-8")
            )
        producer.flush()
        batch_messages.clear()
        last_flush_time = current_time

    if msg is None:
        continue
    if msg.error():
        logger.error(msg.error())
        continue

    try:
        data = json.loads(msg.value().decode("utf-8"))
        news_id = data.get("id")
        title = data.get("title")
        content = data.get("content")
        published_at = data.get("published_at")
        topic_ids = data.get("topic_ids", [])
        entities = data.get("entities", [])

        if not title or not content:
            continue

        text_for_sentiment = f"{title}. {content}"[:1024]
        sentences = re.split(r"(?<=[.!?])\s+", content)
        first_3_sentences = " ".join(sentences[:3])
        # dự đoán sentiment
        sentiment_result = sentiment_pipeline(text_for_sentiment)[0]  

        logger.info(f"--- Processing News ID: {news_id} ---")
        logger.info(f"Title: {title}")
        logger.info(f"Topic IDs: {topic_ids}")
        logger.info(f"Entities: {entities}")
        logger.info(f"Sentiment: {sentiment_result}")
        logger.info(f"Published: {published_at}")
        logger.info("-" * 40)

        msg_out = {
            "id": news_id,
            "published_at": published_at,
            "topic_ids": topic_ids,
            "entities": entities,
            "sentiment": sentiment_result  
        }

        batch_messages.append(msg_out)

    except Exception as e:
        logger.exception(e)
