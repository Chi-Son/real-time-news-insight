import json
import logging
import time
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

# =========================
# KAFKA CONFIG
# =========================
INPUT_TOPIC = "extractor_topic"
OUTPUT_TOPIC = "topic_scoring_input"  
GROUP_ID = "extractor_sentiment"

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

# =========================
# MAIN LOOP
# =========================
while True:
    msg = consumer.poll(1.0)
    current_time = time.time()

    # flush batch nếu đủ size hoặc timeout
    if batch_messages and (len(batch_messages) >= BATCH_SIZE or current_time - last_flush_time >= BATCH_TIMEOUT):
        for m in batch_messages:
            # gửi sang topic kết quả nếu cần
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
