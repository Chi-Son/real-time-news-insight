from fastapi import FastAPI, Query
from datetime import datetime, timezone
import time
import psycopg2

from shared.redis_connect import redis_connection
from shared.postgresql_config import DB_CONFIG

app = FastAPI()
redis = redis_connection()

WINDOW_SECONDS = 24 * 3600


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


@app.get("/api/topics/{topic_id}/articles")
def get_articles_by_topic(
    topic_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    redis_key = f"topic:window:{topic_id}"

    if not redis.exists(redis_key):
        return {
            "topic_id": topic_id,
            "window": "24h",
            "total": 0,
            "articles": []
        }

    now_epoch = int(time.time())
    min_epoch = now_epoch - WINDOW_SECONDS

    # 1. Lấy article_id từ Redis (mới nhất trước)
    redis_items = redis.zrevrangebyscore(
        redis_key,
        max=now_epoch,
        min=min_epoch,
        start=offset,
        num=limit,
        withscores=False
    )

    article_ids = [
        aid.decode() if isinstance(aid, bytes) else aid
        for aid in redis_items
    ]

    if not article_ids:
        return {
            "topic_id": topic_id,
            "window": "24h",
            "total": 0,
            "articles": []
        }

    total = redis.zcount(redis_key, min_epoch, now_epoch)

    # 2. Query PostgreSQL để enrich
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            a.id,
            a.title,
            a.url,
            a.published_at,
            s.sentiment
        FROM article a
        LEFT JOIN article_sentiment s ON a.id = s.id
        WHERE a.id = ANY(%s)
    """, (article_ids,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Map để giữ thứ tự theo Redis
    row_map = {r[0]: r for r in rows}

    articles = []
    for aid in article_ids:
        r = row_map.get(aid)
        if not r:
            continue

        articles.append({
            "article_id": r[0],
            "title": r[1],
            "url": r[2],
            "published_at": r[3].isoformat() if r[3] else None,
            "sentiment": r[4]
        })

    return {
        "topic_id": topic_id,
        "window": "24h",
        "total": total,
        "articles": articles
    }
