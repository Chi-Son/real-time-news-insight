import json
from kafka import KafkaProducer
import os
# cấu hình kafka producer
def get_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        acks='all',
        retries=5,
        batch_size=32768,
        linger_ms=50,
        buffer_memory=67108864,
        compression_type='lz4',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )