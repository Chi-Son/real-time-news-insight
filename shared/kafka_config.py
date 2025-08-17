import json ,logging
from kafka import KafkaProducer,KafkaConsumer,TopicPartition
import os
import time
from kafka.admin import KafkaAdminClient
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
    "auto_offset_reset": "latest",  
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

"""BASE_CONSUMER_CONFIG = {
    "bootstrap_servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
    "auto_offset_reset": "earliest",
    "enable_auto_commit": True,
    "auto_commit_interval_ms": 5000,
    "key_deserializer": lambda k: k.decode('utf-8') if k else None,
    "value_deserializer": lambda v: json.loads(v.decode('utf-8')) if v else None,
    "fetch_max_bytes": 5_242_880,
    "session_timeout_ms": 45000,
    "heartbeat_interval_ms": 10000,
    # optional: provide client_id to help debugging
    #"client_id": os.getenv("KAFKA_CLIENT_ID", "url_extractor_consumer"),
}

def get_kafka_consumer(topic, group_id, max_poll_records=20, max_poll_interval_ms=300000, retries=10, delay=2):
    bootstrap = BASE_CONSUMER_CONFIG["bootstrap_servers"]
    for attempt in range(retries):
        try:
            # cố kéo metadata bằng AdminClient (không truyền timeout, vì một số phiên bản kafka-python không chấp nhận)
            try:
                admin = KafkaAdminClient(bootstrap_servers=bootstrap, client_id="admin-metadata-puller")
                _ = admin.list_topics()   # nhớ: không dùng timeout kwarg
                admin.close()
            except Exception as e:
                print("Warning: admin metadata pull failed:", e)

            # Tạo consumer **không** truyền topic vào constructor
            config = {**BASE_CONSUMER_CONFIG}
            config["group_id"] = group_id
            config["max_poll_records"] = max_poll_records
            config["max_poll_interval_ms"] = max_poll_interval_ms

            consumer = KafkaConsumer(**config)
            print(f"Kafka consumer created (not yet subscribed) bootstrap_connected={consumer.bootstrap_connected()}")

            # Subscribe để tham gia group và chờ assignment
            consumer.subscribe([topic])

            # Poll lặp để fetch metadata & join group
            for i in range(20):  # tăng/giảm nếu cần (20 * ~1s)
                consumer.poll(timeout_ms=1000)
                parts = consumer.partitions_for_topic(topic)
                assignment = consumer.assignment()
                print(f"[wait {i}] partitions_for_topic={parts} assignment={assignment}")
                if parts is None:
                    time.sleep(1)
                    continue
                if assignment:
                    print("✅ Consumer got assignment:", assignment)
                    return consumer
                # Nếu đã biết partitions nhưng chưa được assign trong vài lần, fallback: unsubscribe rồi manual-assign
                if parts is not None and i >= 5 and not assignment:
                    print("Partitions known but assignment still empty. Will unsubscribe() and manual-assign partitions for immediate consumption.")
                    try:
                        consumer.unsubscribe()
                        tps = [TopicPartition(topic, p) for p in sorted(list(parts))]
                        consumer.assign(tps)
                        print("Manual assigned partitions:", consumer.assignment())
                        return consumer
                    except Exception as e:
                        print("Manual assign failed:", e)
                        # close and retry outer loop
                        try:
                            consumer.close()
                        except:
                            pass
                        break

            # nếu chưa có assignment sau loop -> đóng consumer và retry
            try:
                consumer.close()
            except:
                pass
            print(f"Attempt {attempt+1}/{retries} - metadata/assignment not ready, retrying in {delay}s...")
            time.sleep(delay)

        except NoBrokersAvailable:
            print(f"Kafka broker not available, retrying in {delay}s... ({attempt+1}/{retries})")
            time.sleep(delay)
        except Exception as e:
            print(f"Unexpected error creating consumer: {e}. Retrying in {delay}s ({attempt+1}/{retries})")
            time.sleep(delay)

    raise RuntimeError("Failed to connect to Kafka broker and obtain assignment after retries.")"""
"""BASE_CONSUMER_CONFIG = {
    "bootstrap_servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
    "auto_offset_reset": "earliest",
    "enable_auto_commit": True,
    "auto_commit_interval_ms": 5000,
    "key_deserializer": lambda k: k.decode('utf-8') if k else None,
    "value_deserializer": lambda v: json.loads(v.decode('utf-8')) if v else None,
    "fetch_max_bytes": 5_242_880,
    "session_timeout_ms": 45000,
    "heartbeat_interval_ms": 10000,
    "client_id": os.getenv("KAFKA_CLIENT_ID", f"url_extractor_{os.getenv('HOSTNAME','unknown')}")
}

def get_kafka_consumer(topic, group_id, max_poll_records=20, max_poll_interval_ms=300000, retries=5, delay=2):
    bootstrap = BASE_CONSUMER_CONFIG["bootstrap_servers"]
    last_exc = None
    for attempt in range(retries):
        try:
            # try metadata pull (best-effort)
            try:
                admin = KafkaAdminClient(bootstrap_servers=bootstrap, client_id="admin-metadata-puller")
                _ = admin.list_topics()
                admin.close()
            except Exception as e:
                logging.getLogger("kafka").warning("Admin metadata pull failed: %s", e)

            config = {**BASE_CONSUMER_CONFIG}
            config["group_id"] = group_id
            config["max_poll_records"] = max_poll_records
            config["max_poll_interval_ms"] = max_poll_interval_ms

            # Note: **do not pass topic in constructor** to avoid implicit subscribe/assign ambiguity
            consumer = KafkaConsumer(**config)
            logging.getLogger("kafka").info("Kafka consumer created (not yet subscribed). bootstrap_connected=%s", consumer.bootstrap_connected())

            # subscribe explicitly
            consumer.subscribe([topic])
            logging.getLogger("kafka").info("Subscribed to %s, waiting for assignment...", topic)

            # wait up to 60s (poll loop) for assignment
            max_wait = 60
            start = time.time()
            while time.time() - start < max_wait:
                consumer.poll(timeout_ms=1000)
                parts = consumer.partitions_for_topic(topic)
                assignment = consumer.assignment()
                logging.getLogger("kafka").info("wait %.1fs partitions=%s assignment=%s", time.time()-start, parts, assignment)
                if assignment:
                    logging.getLogger("kafka").info("Consumer got assignment: %s", assignment)
                    return consumer
                time.sleep(0.5)

            # if here, no assignment after wait -> close and retry outer loop (do not auto assign)
            try:
                consumer.close()
            except:
                pass
            logging.getLogger("kafka").warning("No assignment after %ss; retrying (%s/%s)", max_wait, attempt+1, retries)
            time.sleep(delay)

        except NoBrokersAvailable as e:
            last_exc = e
            logging.getLogger("kafka").warning("No brokers available, retrying...")
            time.sleep(delay)
        except Exception as e:
            last_exc = e
            logging.getLogger("kafka").warning("Unexpected error creating consumer: %s", e)
            time.sleep(delay)

    raise RuntimeError("Failed to create consumer and obtain assignment.") from last_exc"""
def on_success(record_metadata):
    print(f"✅ Sent to {record_metadata.topic} "
          f"[partition {record_metadata.partition}] "
          f"offset {record_metadata.offset}")
def on_error(excp):
    print(f"❌ Failed to send message: {excp}")