import json ,logging
import os
import time
from confluent_kafka import Producer,Consumer, KafkaException

logging.basicConfig(level=logging.INFO)
logger =logging.getLogger(__name__)
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

def retry_connection(func,retries=5, delay=5):
    for i in range(retries):
        try:
            return func()
        except KafkaException as e:
            logger.warning(f"Kafka broker not available, retrying in {delay}s... ({i+1}/{retries}) | {e}")
            time.sleep(delay) 
    raise RuntimeError("Failed to connect to Kafka broker after retries.")


def get_kafka_producer():
    def connect():
        conf={
            "bootstrap.servers":KAFKA_BOOTSTRAP,
            "compression.type":"lz4",
            "retries":5,
            "acks":"all",
            "batch.num.messages": 10000, 
            "linger.ms": 50, 
            "message.max.bytes": 67108864,
        }
        return Producer(conf)
    producer = retry_connection(connect)
    logger.info("Kafka producer connected.")
    return  producer


def get_kafka_consumer(topic, group_id, **kwargs):
    BASE_CONSUMER_CONFIG = {
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
        "auto.commit.interval.ms": 5000,
        "session.timeout.ms": 45000,
        "heartbeat.interval.ms": 10000,
        "fetch.max.bytes": 5_242_880,
    }
    def connect():
        conf = {**BASE_CONSUMER_CONFIG, "group.id": group_id, **kwargs}
        consumer = Consumer(conf)
        consumer.subscribe([topic])
        return consumer

    consumer = retry_connection(connect)
    logger.info(
        f"Kafka consumer connected to topic '{topic}' with group_id '{group_id}'."
    )
    return consumer

