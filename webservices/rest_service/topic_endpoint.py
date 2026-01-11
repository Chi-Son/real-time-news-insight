from fastapi import APIRouter, HTTPException
import psycopg2
import time
from datetime import datetime, timedelta, timezone

from shared.postgresql_config import DB_CONFIG
from shared.redis_connect import redis_connection

router = APIRouter(prefix="/api/topics", tags=["Topics"])

redis = redis_connection()


# =========================
# DB
# =========================
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


# =========================
# LOAD TOPIC NAME MAP (1 LẦN)
# =========================
def get_topic_map():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT topic_id, name FROM topic")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {str(tid): name for tid, name in rows}


TOPIC_NAME_MAP = get_topic_map()


# =========================
# RANKING API (READ REDIS)
# =========================
@router.get("/ranking")
def get_topic_ranking(limit: int = 20):
    raw = redis.zrevrange("topic:score", 0, limit - 1, withscores=True)

    data = []
    for topic_id, score in raw:
        tid = topic_id.decode() if isinstance(topic_id, bytes) else topic_id
        data.append({
            "topic_id": tid,
            "topic_name": TOPIC_NAME_MAP.get(tid, f"Topic {tid}"),
            "score": round(score, 6)
        })

    return {
        "data": data,
        "updated_at": int(time.time())
    }


# =========================
# TOPIC DETAIL
# =========================
@router.get("/{topic_id}")
def get_topic_detail(topic_id: int, limit: int = 50):
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. TOPIC INFO
    cur.execute(
        """
        SELECT topic_id, name, short_description
        FROM topic
        WHERE topic_id = %s
        """,
        (topic_id,),
    )
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Topic not found")

    topic = {
        "topic_id": row[0],
        "name": row[1],
        "short_description": row[2],
    }

    # TIME SPLIT
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)

    # 2. ARTICLES IN LAST 24H
    cur.execute(
        """
        SELECT
            nc.id,
            nc.title,
            nc.source,
            nl.url,
            se.sentiment,
            nc.published_at,
        FROM article_topic at
        JOIN news_content nc ON at.id = nc.id
        JOIN news_links nl ON at.id = nl.id
        JOIN article_sentiment se ON at.id = se.id
        WHERE at.topic_id = %s
          AND nc.published_at >= %s
        ORDER BY nc.published_at DESC
        LIMIT %s
        """,
        (topic_id, cutoff, limit),
    )

    articles_24h = [
        {
            "id": r[0],
            "title": r[1],
            "source": r[2],
            "url": r[3],
            "sentiment": r[4],
            "published_at": r[5],
        }
        for r in cur.fetchall()
    ]

    # 3. ARTICLES HISTORY (>24H)
    cur.execute(
        """
        SELECT
            nc.id,
            nc.title,
            nc.source,
            nl.url,
            se.sentiment,
            nc.published_at,
        FROM article_topic at
        JOIN news_content nc ON at.id = nc.id
        JOIN news_links nl ON at.id = nl.id
        JOIN article_sentiment se ON at.id = se.id
        WHERE at.topic_id = %s
          AND nc.published_at < %s
        ORDER BY nc.published_at DESC
        LIMIT %s
        """,
        (topic_id, cutoff, limit),
    )

    articles_history = [
        {
            "id": r[0],
            "title": r[1],
            "source": r[2],
            "url": r[3],
            "sentiment": r[4],
            "published_at": r[5],
        }
        for r in cur.fetchall()
    ]

    cur.close()
    conn.close()

    return {
        "topic": topic,
        "articles_24h": articles_24h,
        "articles_history": articles_history,
    }
