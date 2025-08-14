import json
from kafka import KafkaProducer,KafkaConsumer
import os
import time
from kafka.errors import NoBrokersAvailable

def get_kafka_producer(retries=5, delay=5):
    for i in range(retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
                acks='all',
                retries=5,
                batch_size=32768,
                linger_ms=50,
                buffer_memory=67108864,
                compression_type='lz4',
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print("Kafka producer connected.")
            return producer
        except NoBrokersAvailable:
            print(f"Kafka broker not available, retrying in {delay}s... ({i+1}/{retries})")
            time.sleep(delay)
    raise RuntimeError("Failed to connect to Kafka broker after retries.")


BASE_CONSUMER_CONFIG = {
    "bootstrap_servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
    "auto_offset_reset": "earliest",  # đổi thành 'latest' khi chạy production
    "enable_auto_commit": True,
    "auto_commit_interval_ms": 5000,
    "key_deserializer": lambda k: k.decode('utf-8') if k else None,
    "value_deserializer": lambda v: json.loads(v.decode('utf-8')),
    "fetch_max_bytes": 5_242_880,  
    "session_timeout_ms": 45000,
    "heartbeat_interval_ms": 10000
}

def get_kafka_consumer(topic, group_id, max_poll_records=20, max_poll_interval_ms=300000, retries=5, delay=5):
    for i in range(retries):
        try:
            config = {**BASE_CONSUMER_CONFIG}
            config["group_id"] = group_id
            config["max_poll_records"] = max_poll_records
            config["max_poll_interval_ms"] = max_poll_interval_ms

            consumer = KafkaConsumer(topic, **config)
            print(f"Kafka consumer connected to topic '{topic}' with group_id '{group_id}'.")
            return consumer
        except NoBrokersAvailable:
            print(f"Kafka broker not available, retrying in {delay}s... ({i+1}/{retries})")
            time.sleep(delay)
    raise RuntimeError("Failed to connect to Kafka broker after retries.")

def on_success(record_metadata):
    print(f"✅ Sent to {record_metadata.topic} "
          f"[partition {record_metadata.partition}] "
          f"offset {record_metadata.offset}")
def on_error(excp):
    print(f"❌ Failed to send message: {excp}")