from fastapi import APIRouter, HTTPException
import psycopg2
from datetime import datetime, timedelta, timezone
from shared.postgresql_config import DB_CONFIG

router = APIRouter(prefix="/api/topics", tags=["Topics"])


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


@router.get("/{topic_id}")
def get_topic_detail(topic_id: int, limit: int = 50):
    conn = get_db_connection()
    cur = conn.cursor()

    # =========================
    # 1. GET TOPIC INFO
    # =========================
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

    # =========================
    # TIME SPLIT
    # =========================
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)

    # =========================
    # 2. ARTICLES IN LAST 24H
    # =========================
    cur.execute(
        """
        SELECT
            nc.id,
            nc.title,
            nc.source,
            nl.url,
            se.sentiment,
            nc.published_at,
            nl.category
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
            "category":r[6]
        }
        for r in cur.fetchall()
    ]

    # =========================
    # 3. ARTICLES HISTORY (>24H)
    # =========================
    cur.execute(
        """
        SELECT
            nc.id,
            nc.title,
            nc.source,
            nl.url,
            se.sentiment,
            nc.published_at,
            nl.category
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
            "category":r[6]
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
