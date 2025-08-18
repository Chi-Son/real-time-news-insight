from confluent_kafka import Producer,Consumer
import json,logging

logging.basicConfig(level=logging.INFO)
logger =logging.getLogger(__name__)
def send_json(producer: Producer, topic: str, data: dict, key: str = None):
    try:
        producer.produce(
            topic=topic,
            key=key,
            value=json.dumps(data).encode("utf-8"),
            callback=delivery_report,
        )
        producer.flush()
    except Exception as e:
        logger.error(f"Failed to send message to topic {topic}: {e}")

def delivery_report(err, msg):
    """Delivery callback for Kafka producer."""
    if err:
        logger.error(f"❌ Delivery failed: {err}")
    else:
        logger.info(
            f"✅ Delivered message to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}"
        )

def consume_json(consumer: Consumer, timeout=1.0):
    msg = consumer.poll(timeout=timeout)
    if msg is None:
        return None
    if msg.error():
        logger.error(f"Consumer error: {msg.error()}")
        return None
    return json.loads(msg.value().decode("utf-8"))