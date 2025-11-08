import sys
import os
import logging
import json
import time
import torch

# Thêm pipeline vào path
sys.path.append('/app/models')

from pipeline import KeywordExtractorPipeline
from transformers import AutoTokenizer, AutoModel, AutoModelForTokenClassification

# Kafka config
from shared.kafka_config import get_kafka_consumer, get_kafka_producer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SOURCE_TOPIC = os.getenv("SOURCE_TOPIC", "source_topic_name")
TARGET_TOPIC = os.getenv("TARGET_TOPIC", "raw_keywords")
GROUP_ID = os.getenv("GROUP_ID", "keyword-extractor-group")

# Load model
logger.info("Loading PhoBERT + NER model...")
tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base", use_fast=False)
phobert = AutoModel.from_pretrained("vinai/phobert-base")
ner_model = AutoModelForTokenClassification.from_pretrained("NlpHUST/ner-vietnamese-electra-base")
kw_pipeline = KeywordExtractorPipeline(phobert, ner_model)
logger.info("Model loaded successfully.")

# Kafka producer + consumer
producer = get_kafka_producer()
consumer = get_kafka_consumer(SOURCE_TOPIC, GROUP_ID)

logger.info(f"Starting Kafka keyword extractor service. Listening on topic: {SOURCE_TOPIC}")

def process_message(msg):
    try:
        data = json.loads(msg.value().decode('utf-8'))
        id =data.get('id','')
        title = data.get('title', '')
        content = data.get('content', '')
        category = data.get('category', '')

        if not title or not content:
            return None

        sample_input = {"title": title, "text": content}
        keywords = kw_pipeline(
            inputs=sample_input,
            min_freq=1,
            ngram_n=(1,3),
            top_n=10,
            diversify_result=False
        )

        output_msg = {
            "id":id,
            "title": title,
            "content": content,
            "category": category,
            "keywords": [{"kw": kw, "score": float(score)} for kw, score in keywords]
        }

        return output_msg
    except Exception as e:
        logger.exception(f"Error processing message: {e}")
        return None

# Main loop
try:
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            logger.error(f"Consumer error: {msg.error()}")
            continue

        output_msg = process_message(msg)
        if output_msg:
            producer.produce(TARGET_TOPIC, json.dumps(output_msg).encode('utf-8'))
            producer.flush()
            logger.info(f"Sent keywords for article: {output_msg['title'][:50]}...")
except KeyboardInterrupt:
    logger.info("Shutting down...")
finally:
    consumer.close()
