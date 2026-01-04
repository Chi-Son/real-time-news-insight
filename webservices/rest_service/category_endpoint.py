from fastapi import APIRouter, HTTPException
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime, timedelta, timezone
from shared.postgresql_config import DB_CONFIG

router = APIRouter(prefix="/api/category", tags=["Category"])

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

@router.get("/{category}")
def get_category_articles(category: str):
    """
    Trả về 2 danh sách bài viết:
    - articles_24h: trong vòng 24h gần đây
    - articles_history: ngoài 24h
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=DictCursor)

        # Thời gian hiện tại
        now = datetime.now(timezone.utc)
        last_24h = now - timedelta(hours=24)

        # =============================
        # Lấy bài viết trong 24h
        # =============================
        cur.execute("""
            SELECT nl.id, nc.title, nl.url, nc.published_at
            FROM news_links nl
            LEFT JOIN news_content nc 
            ON nl.id = nc.id
            WHERE nl.category = %s
              AND nc.published_at >= %s
            ORDER BY nc.published_at DESC
        """, (category, last_24h))

        articles_24h = [dict(row) for row in cur.fetchall()]

        # =============================
        # Lấy bài viết ngoài 24h
        # =============================
        cur.execute("""
            SELECT nl.id, nc.title, nl.url, nc.published_at
            FROM news_links nl
            LEFT JOIN news_content nc 
            ON nl.id = nc.id
            WHERE nl.category = %s
              AND nc.published_at < %s
            ORDER BY nc.published_at DESC
            LIMIT 100
        """, (category, last_24h))

        articles_history = [dict(row) for row in cur.fetchall()]

        cur.close()
        conn.close()

        return {
            "category": category,
            "articles_24h": articles_24h,
            "articles_history": articles_history
        }

    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {e}")
