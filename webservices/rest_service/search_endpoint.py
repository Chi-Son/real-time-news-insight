from fastapi import APIRouter, Query
import psycopg2
from shared.postgresql_config import DB_CONFIG

router = APIRouter(prefix="/api/search", tags=["Search"])


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


@router.get("/")
def search(
    q: str = Query(..., min_length=2, description="topic or entity keyword"),
    limit: int = Query(20, le=50)
):
    keyword = f"%{q.lower()}%"
    topic_limit = limit // 2
    entity_limit = limit - topic_limit

    conn = get_db_connection()
    cur = conn.cursor()

    # ---- SEARCH TOPIC ----
    cur.execute(
        """
        SELECT topic_id, name, short_description
        FROM topic
        WHERE LOWER(name) ILIKE %s
        ORDER BY name
        LIMIT %s
        """,
        (keyword, topic_limit),
    )

    topics = [
        {
            "result_type": "topic",
            "topic_id": row[0],
            "name": row[1],
            "short_description": row[2],
        }
        for row in cur.fetchall()
    ]

    # ---- SEARCH ENTITY ----
    cur.execute(
        """
        SELECT entity_id, type, text
        FROM entity
        WHERE LOWER(text) ILIKE %s
        ORDER BY text
        LIMIT %s
        """,
        (keyword, entity_limit),
    )

    entities = [
        {
            "result_type": "entity",
            "entity_id": row[0],
            "entity_type": row[1],
            "text": row[2],
        }
        for row in cur.fetchall()
    ]
    return {
        "query": q,
        "total": len(topics) + len(entities),
        "results": topics + entities,
    }
