from fastapi import APIRouter, Query
import psycopg2

from shared.redis_connect import redis_connection
from shared.postgresql_config import DB_CONFIG

router = APIRouter()
redis = redis_connection()

def get_db():
    return psycopg2.connect(**DB_CONFIG)

# -------------------------
# Topic detail – 24h
# -------------------------
@router.get("/{topic_id}/articles")
def get_topic_articles(
    topic_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    redis_key = f"topic:window:{topic_id}"

    if not redis.exists(redis_key):
        return {"topic_id": topic_id, "window": "24h", "total": 0, "articles": []}

    ids = redis.zrevrange(redis_key, offset, offset + limit - 1)
    article_ids = [i.decode() for i in ids]
    total = redis.zcard(redis_key)

    if not article_ids:
        return {"topic_id": topic_id, "window": "24h", "total": 0, "articles": []}

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.id, a.title, l.url, a.published_at, a.source, s.sentiment
        FROM news_content a
        LEFT JOIN news_links l ON a.id = l.id
        LEFT JOIN article_sentiment s ON a.id = s.id
        WHERE a.id = ANY(%s)
    """, (article_ids,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    row_map = {r[0]: r for r in rows}

    articles = [{
        "article_id": r[0],
        "title": r[1],
        "url": r[2],
        "published_at": r[3],
        "source": r[4],
        "sentiment": r[5]
    } for aid in article_ids if (r := row_map.get(aid))]

    return {
        "topic_id": topic_id,
        "window": "24h",
        "total": total,
        "articles": articles
    }

# -------------------------
# Topic history
# -------------------------
@router.get("/{topic_id}/articles/history")
def get_topic_history(topic_id: str):
    return {"topic_id": topic_id, "message": "TODO: history"}

# -------------------------
# Topic summary
# -------------------------
@router.get("/{topic_id}/summary")
def get_topic_summary(topic_id: str):
    return {"topic_id": topic_id, "message": "TODO: summary"}