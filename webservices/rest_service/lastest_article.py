from fastapi import APIRouter, HTTPException, Query
import psycopg2

from shared.postgresql_config import DB_CONFIG

router = APIRouter(prefix="/api", tags=["Articles"])


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


@router.get("/articles/latest")
def get_latest_articles(
    limit: int = Query(20, ge=1, le=100)
):
    """
    Lấy danh sách bài viết mới nhất (không giới hạn thời gian)
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        query = f"""
        SELECT
            nl.id,
            nc.title,
            nc.published_at,
            nc.source,
            nl.url,
            se.sentiment,
            -- topics (bắt buộc có topic)
            COALESCE(
                json_agg(
                    DISTINCT jsonb_build_object(
                        'topic_id', t.topic_id,
                        'name', t.name
                    )
                ) FILTER (WHERE t.topic_id IS NOT NULL),
                '[]'
            ) AS topics,
            -- entities (có hay không đều được)
            COALESCE(
                json_agg(
                    DISTINCT jsonb_build_object(
                        'entity_id', e.entity_id,
                        'text', e.text
                    )
                ) FILTER (WHERE e.entity_id IS NOT NULL),
                '[]'
            ) AS entities
        FROM news_links nl
        JOIN news_content nc
            ON nc.id = nl.id
        LEFT JOIN article_sentiment se
            ON se.id = nl.id
        JOIN article_topic at
            ON at.id = nl.id
        LEFT JOIN topic t
            ON t.topic_id = at.topic_id
        LEFT JOIN article_entity ae
            ON ae.id = nl.id          
        LEFT JOIN entity e
            ON e.entity_id = ae.entity_id
        GROUP BY
            nl.id,
            nc.title,
            nc.published_at,
            nc.source,
            nl.url,
            se.sentiment
        ORDER BY nc.published_at DESC
        LIMIT {limit};
        """

        cur.execute(query)
        rows = cur.fetchall()

        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in rows]

        cur.close()
        conn.close()

        return {
            "count": len(results),
            "articles": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
