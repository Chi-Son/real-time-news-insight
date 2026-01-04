from fastapi import APIRouter, HTTPException
import psycopg2
from datetime import datetime, timedelta, timezone
from shared.postgresql_config import DB_CONFIG

router = APIRouter(prefix="/api/entities", tags=["Entities"])


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


@router.get("/{entity_id}")
def get_entity_detail(entity_id: int, limit: int = 50):
    conn = get_db_connection()
    cur = conn.cursor()

    # =========================
    # 1. GET TOPIC INFO
    # =========================
    cur.execute(
        """
        SELECT entity_id, text, type
        FROM entity
        WHERE entity_id = %s
        """,
        (entity_id,),
    )
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Entiy not found")

    entity = {
        "entity_id": row[0],
        "text": row[1],
        "type": row[2],
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
        FROM article_entity at
        JOIN news_content nc ON at.id = nc.id
        JOIN news_links nl ON at.id = nl.id
        JOIN article_sentiment se ON at.id = se.id
        WHERE at.entity_id = %s
          AND nc.published_at >= %s
        ORDER BY nc.published_at DESC
        LIMIT %s
        """,
        (entity_id, cutoff, limit),
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
        FROM article_entity at
        JOIN news_content nc ON at.id = nc.id
        JOIN news_links nl ON at.id = nl.id
        JOIN article_sentiment se ON at.id = se.id
        WHERE at.entity_id = %s
          AND nc.published_at < %s
        ORDER BY nc.published_at DESC
        LIMIT %s
        """,
        (entity_id, cutoff, limit),
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
        "entity": entity,
        "articles_24h": articles_24h,
        "articles_history": articles_history,
    }
