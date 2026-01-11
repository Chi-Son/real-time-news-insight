from fastapi import APIRouter, HTTPException, Query
import psycopg2
from psycopg2.extras import DictCursor
from shared.postgresql_config import DB_CONFIG

router = APIRouter(prefix="/api/category", tags=["Category"])

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

@router.get("/{category}")
def get_category_articles(
    category: str,
    limit: int = Query(100, ge=1, le=500)
):
    """
    Lấy danh sách bài viết theo category/topic
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=DictCursor)

        query = """
        SELECT
            nc.id,
            nc.title,
            nc.published_at,
            nc.source,
            nl.url,
            se.sentiment,
            COALESCE(
                json_agg(
                    DISTINCT jsonb_build_object(
                        'topic_id', t.topic_id,
                        'name', t.name
                    )
                ) FILTER (WHERE t.topic_id IS NOT NULL),
                '[]'
            ) AS topics,
            COALESCE(
                json_agg(
                    DISTINCT jsonb_build_object(
                        'entity_id', e.entity_id,
                        'text', e.text
                    )
                ) FILTER (WHERE e.entity_id IS NOT NULL),
                '[]'
            ) AS entities
        FROM news_content nc
        LEFT JOIN news_links nl
            ON nc.id = nl.id
        LEFT JOIN article_sentiment se
            ON se.id = nl.id
        LEFT JOIN article_topic at
            ON at.id = nl.id
        LEFT JOIN topic t
            ON t.topic_id = at.topic_id
        LEFT JOIN article_entity ae
            ON ae.id = nl.id          
        LEFT JOIN entity e
            ON e.entity_id = ae.entity_id
        WHERE nl.category = %s
            AND nc.title IS NOT NULL
            AND nc.title != ''
            AND nc.content IS NOT NULL
            AND nc.content != ''
            AND nc.published_at IS NOT NULL
        GROUP BY
            nc.id,
            nc.title,
            nc.published_at,
            nc.source,
            nl.url,
            se.sentiment
        ORDER BY nc.published_at DESC
        LIMIT %s;
        """

        cur.execute(query, (category, limit))
        rows = cur.fetchall()

        results = [dict(row) for row in rows]

        cur.close()
        conn.close()

        return {
            "category": category,
            "count": len(results),
            "articles": results
        }

    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {e}")