import requests
from bs4 import BeautifulSoup
from shared.kafka_config import get_kafka_consumer, get_kafka_producer

INPUT_TOPIC = "raw_links"
OUTPUT_TOPIC = "extracted_html"
GROUP_ID = "url_extractor_group"

# Lấy consumer và producer từ shared
consumer = get_kafka_consumer(
    topic=INPUT_TOPIC,
    group_id=GROUP_ID,
    max_poll_records=20,         # xử lý HTML nên để thấp
    max_poll_interval_ms=300000  # 5 phút, phòng khi request lâu
)
producer = get_kafka_producer()

print("✅ Extractor Service started...")
for message in consumer:
    url_data = message.value  # {"url": "...", "title": "..."}
    url = url_data.get("url")
    print(f"🔍 Extracting from: {url}")

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

        producer.send(OUTPUT_TOPIC, value=output_data)
        print(f"📤 Sent extracted HTML for {url}")

    except Exception as e:
        print(f"❌ Failed to extract {url}: {e}")
