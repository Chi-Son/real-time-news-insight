import json
import logging
import math
import time
import requests
import os
from datetime import datetime, timezone

from shared.kafka_config import get_kafka_consumer
from shared.redis_connect import redis_connection
import requests

import psycopg2
from shared.postgresql_config import DB_CONFIG
# =========================
# LOGGING
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("topic_scoring_24h")

WEBSOCKET_PUSH_URL = os.getenv(
    "WEBSOCKET_PUSH_URL",
    "http://websocket_service:8000/ws-push/topics"
)
# =========================
# KAFKA CONFIG
# =========================
INPUT_TOPIC = "extractor_sentiment"
GROUP_ID = "topic_scoring_24h_group"

consumer = get_kafka_consumer(
    topic=INPUT_TOPIC,
    group_id=GROUP_ID
)

# =========================
# REDIS
# =========================
redis = redis_connection()

# =========================
# CONFIG
# =========================
WINDOW_HOURS = 24
WINDOW_MINUTES = WINDOW_HOURS * 60        
REDIS_TTL_SECONDS = 48 * 3600               
DECAY_LAMBDA = 0.0048                       


def load_topic_map():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT topic_id, name FROM topic")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return {str(topic_id): name for topic_id, name in rows}

TOPIC_NAME_MAP = load_topic_map()
# =========================
# UTILS
# =========================
def to_epoch(ts: str) -> int:
    """
    ISO8601 -> epoch seconds (UTC)
    """
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return int(dt.astimezone(timezone.utc).timestamp())


def decay_score(minutes_diff: float) -> float:
    """
    Exponential decay theo phút
    """
    return math.exp(-DECAY_LAMBDA * minutes_diff)

def push_topic_scores(redis):
    """
    Lấy toàn bộ topic score, sort desc, push websocket
    """
    raw = redis.zrevrange("topic:score", 0, -1, withscores=True)

    topics = []
    for topic_id, score in raw:
        tid = topic_id.decode() if isinstance(topic_id, bytes) else topic_id
        topics.append({
            "topic_id": tid,
            "topic_name": TOPIC_NAME_MAP.get(tid, f"Topic {tid}"),
            "score": round(score, 6)
        })

    payload = {
        "type": "topic_score_update",
        "data": topics,
        "updated_at": int(time.time())
    }

    try:
        requests.post(WEBSOCKET_PUSH_URL, json=payload, timeout=0.5)
    except Exception as e:
        logger.warning(f"WebSocket push failed: {e}")

# =========================
# MAIN LOOP
# =========================
logger.info("🚀 Topic Scoring 24h Service started")

while True:
    msg = consumer.poll(1.0)

    if msg is None:
        continue
    if msg.error():
        logger.error(msg.error())
        continue

    try:
        data = json.loads(msg.value().decode("utf-8"))

        article_id = data.get("id")
        topic_ids = data.get("topic_ids", [])
        published_at = data.get("published_at")

        if not article_id or not topic_ids or not published_at:
            continue

        pub_epoch = to_epoch(published_at)
        now_epoch = int(time.time())

        # =========================
        # CHECK WINDOW 24H (THEO PHÚT)
        # =========================
        minutes_from_now = (now_epoch - pub_epoch) / 60
        if minutes_from_now > WINDOW_MINUTES:
            logger.info(f"[SKIP] Article {article_id} older than 24h")
            continue

        # =========================
        # PROCESS EACH TOPIC
        # =========================
        for topic_id in topic_ids:
            topic_key = f"topic:window:{topic_id}"

            # Lưu article vào window (score = epoch seconds)
            redis.zadd(topic_key, {str(article_id): pub_epoch})
            redis.expire(topic_key, REDIS_TTL_SECONDS)

            # Lấy toàn bộ bài của topic
            items = redis.zrange(topic_key, 0, -1, withscores=True)

            valid_timestamps = []
            for _, ts in items:
                minutes_diff = (now_epoch - ts) / 60
                if minutes_diff <= WINDOW_MINUTES:
                    valid_timestamps.append(ts)

            # Nếu topic đã chết hoàn toàn
            if not valid_timestamps:
                redis.delete(topic_key)
                redis.zrem("topic:score", str(topic_id))
                continue

            # =========================
            # TÍNH ĐIỂM DECAY
            # =========================
            total_score = 0.0
            for ts in valid_timestamps:
                minutes_diff = (now_epoch - ts) / 60
                total_score += decay_score(minutes_diff)

            total_score = round(total_score, 6)

            # Lưu score topic
            redis.zadd(
                "topic:score",
                {str(topic_id): total_score}
            )

            logger.info(
                f"[Topic {topic_id}] "
                f"articles={len(valid_timestamps)} "
                f"score={total_score}"
            )
        push_topic_scores(redis)
    except Exception as e:
        logger.exception(e)
