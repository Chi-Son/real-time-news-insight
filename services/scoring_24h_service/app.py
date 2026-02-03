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

def cleanup_old_articles(redis, topic_id: str, now_epoch: int):
    """
    Xóa các bài viết cũ hơn 24h khỏi Redis sorted set
    """
    topic_key = f"topic:window:{topic_id}"
    cutoff_epoch = now_epoch - (WINDOW_MINUTES * 60)
    
    # Xóa tất cả bài viết có timestamp < cutoff
    removed = redis.zremrangebyscore(topic_key, '-inf', cutoff_epoch)
    
    if removed > 0:
        logger.info(f"[CLEANUP] Removed {removed} old articles from topic {topic_id}")
    
    return removed

def cleanup_all_topics(redis):
    """
    Dọn dẹp tất cả topics, xóa bài cũ và cập nhật điểm
    """
    now_epoch = int(time.time())
    cutoff_epoch = now_epoch - (WINDOW_MINUTES * 60)
    
    # Lấy tất cả topic keys
    topic_keys = redis.keys("topic:window:*")
    
    for topic_key in topic_keys:
        topic_key_str = topic_key.decode() if isinstance(topic_key, bytes) else topic_key
        topic_id = topic_key_str.replace("topic:window:", "")
        
        # Xóa bài cũ
        removed = redis.zremrangebyscore(topic_key_str, '-inf', cutoff_epoch)
        
        # Lấy các bài còn lại
        items = redis.zrange(topic_key_str, 0, -1, withscores=True)
        
        if not items:
            # Topic không còn bài nào, xóa luôn
            redis.delete(topic_key_str)
            redis.zrem("topic:score", str(topic_id))
            logger.info(f"[CLEANUP] Deleted empty topic {topic_id}")
            continue
        
        # Tính lại điểm
        total_score = 0.0
        for _, ts in items:
            minutes_diff = (now_epoch - ts) / 60
            if minutes_diff <= WINDOW_MINUTES:
                total_score += decay_score(minutes_diff)
        
        total_score = round(total_score, 6)
        
        # Cập nhật score
        redis.zadd("topic:score", {str(topic_id): total_score})
        
        if removed > 0:
            logger.info(
                f"[CLEANUP] Topic {topic_id}: removed {removed} old articles, "
                f"remaining {len(items)}, score={total_score}"
            )
    
    # Push cập nhật sau khi cleanup
    push_topic_scores(redis)

# =========================
# STARTUP CLEANUP
# =========================
def startup_cleanup(redis):
    """
    Dọn dẹp toàn bộ dữ liệu cũ khi service khởi động
    Giải quyết vấn đề: Redis bị tắt → TTL không chạy → data cũ tồn đọng
    """
    logger.info("=" * 60)
    logger.info("🧹 STARTUP CLEANUP: Cleaning old data from Redis...")
    logger.info("=" * 60)
    
    now_epoch = int(time.time())
    cutoff_epoch = now_epoch - (WINDOW_MINUTES * 60)
    
    # Lấy tất cả topic keys
    topic_keys = redis.keys("topic:window:*")
    
    total_removed = 0
    total_topics = len(topic_keys)
    empty_topics = 0
    
    for topic_key in topic_keys:
        topic_key_str = topic_key.decode() if isinstance(topic_key, bytes) else topic_key
        topic_id = topic_key_str.replace("topic:window:", "")
        
        # Xóa bài cũ hơn 24h
        removed = redis.zremrangebyscore(topic_key_str, '-inf', cutoff_epoch)
        total_removed += removed
        
        # Lấy các bài còn lại
        items = redis.zrange(topic_key_str, 0, -1, withscores=True)
        
        if not items:
            # Topic không còn bài nào, xóa luôn
            redis.delete(topic_key_str)
            redis.zrem("topic:score", str(topic_id))
            empty_topics += 1
            logger.info(f"  ❌ Deleted empty topic {topic_id}")
            continue
        
        # Tính lại điểm cho topic còn data
        total_score = 0.0
        for _, ts in items:
            minutes_diff = (now_epoch - ts) / 60
            if minutes_diff <= WINDOW_MINUTES:
                total_score += decay_score(minutes_diff)
        
        total_score = round(total_score, 6)
        redis.zadd("topic:score", {str(topic_id): total_score})
        
        logger.info(
            f"  ✓ Topic {topic_id}: removed {removed} old articles, "
            f"kept {len(items)}, score={total_score}"
        )
    
    logger.info("=" * 60)
    logger.info(f"✅ STARTUP CLEANUP COMPLETE:")
    logger.info(f"   - Total topics processed: {total_topics}")
    logger.info(f"   - Empty topics deleted: {empty_topics}")
    logger.info(f"   - Old articles removed: {total_removed}")
    logger.info("=" * 60)
    
    # Push dữ liệu sạch lên WebSocket
    push_topic_scores(redis)

# =========================
# MAIN LOOP
# =========================
logger.info("🚀 Topic Scoring 24h Service started")

# Chạy cleanup khi khởi động
startup_cleanup(redis)

# Biến đếm để chạy cleanup định kỳ
message_count = 0
CLEANUP_INTERVAL = 100  # Cleanup sau mỗi 100 messages

while True:
    msg = consumer.poll(1.0)

    if msg is None:
        continue
    if msg.error():
        logger.error(msg.error())
        continue

    try:
        message_count += 1
        
        # Chạy cleanup định kỳ
        if message_count % CLEANUP_INTERVAL == 0:
            logger.info(f"[PERIODIC CLEANUP] Running cleanup after {message_count} messages")
            cleanup_all_topics(redis)
            message_count = 0  # Reset counter
            continue
        
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

            # XÓA CÁC BÀI CŨ TRƯỚC KHI TÍNH ĐIỂM
            cleanup_old_articles(redis, str(topic_id), now_epoch)

            # Lấy toàn bộ bài của topic (sau khi đã cleanup)
            items = redis.zrange(topic_key, 0, -1, withscores=True)

            # Nếu topic đã chết hoàn toàn
            if not items:
                redis.delete(topic_key)
                redis.zrem("topic:score", str(topic_id))
                continue

            # =========================
            # TÍNH ĐIỂM DECAY
            # =========================
            total_score = 0.0
            for _, ts in items:
                minutes_diff = (now_epoch - ts) / 60
                if minutes_diff <= WINDOW_MINUTES:
                    total_score += decay_score(minutes_diff)

            total_score = round(total_score, 6)

            # Lưu score topic
            redis.zadd(
                "topic:score",
                {str(topic_id): total_score}
            )

            logger.info(
                f"[Topic {topic_id}] "
                f"articles={len(items)} "
                f"score={total_score}"
            )
        push_topic_scores(redis)
    except Exception as e:
        logger.exception(e)
