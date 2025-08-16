import requests
from bs4 import BeautifulSoup
from shared.kafka_config import get_kafka_consumer, get_kafka_producer
from time import sleep, time

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
#producer = get_kafka_producer()


print("Subscription:", consumer.subscription())
print("Consumer assignment after waiting:", consumer.assignment())
    
for message in consumer:
    url_data = message.value  # {"url": "...", "title": "..."}
    url = url_data.get("url")
    print(f"🔍 Extracting from: {url}")

    try:
        resp = requests.get(url, timeout=5) #5s tránh treo
        soup = BeautifulSoup(resp.text, 'html.parser')
        text_content = soup.get_text(separator=' ', strip=True)

        output_data = {
            "url": url,
            "title": url_data.get("title"),
            "html": resp.text,
            "text": text_content
        }

        #producer.send(OUTPUT_TOPIC, value=output_data)
        print(f"📤 Sent extracted HTML for {url}")

    except Exception as e:
        print(f"❌ Failed to extract {url}: {e}") 

"""from kafka import KafkaConsumer, TopicPartition
from shared.kafka_config import get_kafka_consumer, get_kafka_producer
import time
consumer = KafkaConsumer(
    'raw_links',
    bootstrap_servers='kafka:9092',
    group_id=None, #'url_extractor_group',   
    auto_offset_reset='latest',
    enable_auto_commit=True
)

# Subscribe rồi ép poll để join group
consumer.subscribe(['raw_links'])

print("Subscription:", consumer.subscription())

# Bắt buộc poll 1 lần để Kafka assign partition
for _ in range(5):
    consumer.poll(timeout_ms=1000)
    assignment = consumer.assignment()
    print("Assignment:", assignment)
    if assignment:
        break
    time.sleep(1)

if not assignment:
    print("❌ Không được assign partition nào. Check lại topic/partition count.")
else:
    print("✅ Đã join group và được assign:", assignment)

for message in consumer:
    print(f"PROCESS: {message.topic} {message.partition} {message.offset} {message.value}")"""

