import json
from kafka import KafkaProducer
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
