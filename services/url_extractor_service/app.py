import requests
from bs4 import BeautifulSoup
import logging
from shared.kafka_config import get_kafka_consumer, get_kafka_producer
from shared.encode_json import send_json, consume_json  
import json
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("kafka").setLevel(logging.DEBUG)

INPUT_TOPIC = "raw_links"
OUTPUT_TOPIC = "extracted_html"
GROUP_ID = "url_extractor_group"

consumer = get_kafka_consumer(topic=INPUT_TOPIC, group_id=GROUP_ID)
#producer = get_kafka_producer()

logger.info("URL Extractor service started.")

while True:
    url_data = consume_json(consumer, timeout=1.0)
    if url_data is None:
        time.sleep(0.1)
        continue

    url = url_data.get("url")
    logger.info(f"🔍 Extracting from: {url}")

    try:
        resp = requests.get(url, timeout=5)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text_content = soup.get_text(separator=' ', strip=True)
        output_data = {
            "url": url,
            "title": url_data.get("title"),
            "html": resp.text,
            "text": text_content
        }
        #send_json(producer, OUTPUT_TOPIC, output_data)
        #producer.poll(0) 
        logger.info(f"📤 Sent extracted HTML for {url}")

    except Exception as e:
        logger.error(f"❌ Failed to extract {url}: {e}")
