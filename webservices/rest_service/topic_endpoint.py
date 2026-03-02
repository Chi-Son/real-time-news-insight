from fastapi import APIRouter, HTTPException
import psycopg2
import time
from datetime import datetime, timedelta, timezone
import pytz

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
            nc.published_at
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
            nc.published_at
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

    # 4. DAILY HISTORY (7 DAYS) - Phục vụ tính Z-score
    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    now_vn = datetime.now(vn_tz)
    current_time = now_vn.time()
    
    # Lấy count hôm nay (từ 00:00 đến giờ hiện tại) - Dùng cho Z-score
    today_start_vn = vn_tz.localize(
        datetime.combine(now_vn.date(), datetime.min.time())
    )
    today_end_vn = now_vn
    
    today_start_utc = today_start_vn.astimezone(pytz.UTC)
    today_end_utc = today_end_vn.astimezone(pytz.UTC)
    
    cur.execute(
        """
        SELECT COUNT(DISTINCT at.id)
        FROM article_topic at
        JOIN news_content nc ON at.id = nc.id
        WHERE at.topic_id = %s
          AND nc.published_at >= %s
          AND nc.published_at <= %s
        """,
        (topic_id, today_start_utc, today_end_utc)
    )
    count_now = cur.fetchone()[0]
    
    # Map sentiment từ database sang format chuẩn (định nghĩa trước khi dùng)
    sentiment_map = {
        "POS": "positive",
        "NEG": "negative", 
        "NEU": "neutral",
        "unknown": "neutral"  # Bài không có sentiment → neutral
    }
    
    # Lấy count của 7 ngày trước
    daily_counts = []  # Hiển thị FULL ngày (00h-23h59)
    historical_counts = []  # Cùng khung giờ (00h-hiện tại) - Dùng cho Z-score
    
    for days_ago in range(1, 8):  # 7 ngày trước (không bao gồm hôm nay)
        target_date = now_vn - timedelta(days=days_ago)
        
        # === COUNT FULL NGÀY (00:00:00 → 23:59:59) - Hiển thị ===
        full_start_vn = vn_tz.localize(
            datetime.combine(target_date.date(), datetime.min.time())
        )
        full_end_vn = vn_tz.localize(
            datetime.combine(target_date.date(), datetime.max.time())
        )
        
        full_start_utc = full_start_vn.astimezone(pytz.UTC)
        full_end_utc = full_end_vn.astimezone(pytz.UTC)
        
        cur.execute(
            """
            SELECT COUNT(DISTINCT at.id)
            FROM article_topic at
            JOIN news_content nc ON at.id = nc.id
            WHERE at.topic_id = %s
              AND nc.published_at >= %s
              AND nc.published_at <= %s
            """,
            (topic_id, full_start_utc, full_end_utc)
        )
        full_count = cur.fetchone()[0]
        
        # === COUNT CÙNG KHUNG GIỜ (00:00:00 → giờ hiện tại) - Tính Z-score ===
        same_time_start_vn = vn_tz.localize(
            datetime.combine(target_date.date(), datetime.min.time())
        )
        same_time_end_vn = vn_tz.localize(
            datetime.combine(target_date.date(), current_time)
        )
        
        same_time_start_utc = same_time_start_vn.astimezone(pytz.UTC)
        same_time_end_utc = same_time_end_vn.astimezone(pytz.UTC)
        
        cur.execute(
            """
            SELECT COUNT(DISTINCT at.id)
            FROM article_topic at
            JOIN news_content nc ON at.id = nc.id
            WHERE at.topic_id = %s
              AND nc.published_at >= %s
              AND nc.published_at <= %s
            """,
            (topic_id, same_time_start_utc, same_time_end_utc)
        )
        same_time_count = cur.fetchone()[0]
        
        # === SENTIMENT DISTRIBUTION CHO NGÀY NÀY (FULL NGÀY) ===
        cur.execute(
            """
            SELECT 
                COALESCE(se.sentiment, 'unknown') as sentiment,
                COUNT(*) as count
            FROM article_topic at
            JOIN news_content nc ON at.id = nc.id
            LEFT JOIN article_sentiment se ON at.id = se.id
            WHERE at.topic_id = %s
              AND nc.published_at >= %s
              AND nc.published_at <= %s
            GROUP BY se.sentiment
            """,
            (topic_id, full_start_utc, full_end_utc)
        )
        
        sentiment_rows = cur.fetchall()
        total_sentiment = sum(row[1] for row in sentiment_rows)
        
        sentiment_dist = {
            "positive": {"count": 0, "percentage": 0.0},
            "negative": {"count": 0, "percentage": 0.0},
            "neutral": {"count": 0, "percentage": 0.0}
        }
        
        if total_sentiment > 0:
            for sentiment, count in sentiment_rows:
                mapped = sentiment_map.get(sentiment, "neutral")
                sentiment_dist[mapped]["count"] += count
            
            for sentiment_type in ["positive", "negative", "neutral"]:
                count = sentiment_dist[sentiment_type]["count"]
                percentage = round((count / total_sentiment) * 100, 2)
                sentiment_dist[sentiment_type]["percentage"] = percentage
        
        # Lưu full count để hiển thị
        daily_counts.append({
            "date": target_date.strftime("%Y-%m-%d"),
            "count": full_count,
            "sentiment": sentiment_dist
        })
        
        # Lưu same time count để tính Z-score
        historical_counts.append(same_time_count)
    
    # Đảo ngược để có thứ tự từ cũ → mới
    daily_counts.reverse()
    historical_counts.reverse()
    
    # 5. TÍNH Z-SCORE VÀ SPIKE CHO TỪNG NGÀY
    # Weights: [1, 2, 3, 4, 5, 6, 7] cho 7 ngày (ngày gần nhất có trọng số cao nhất)
    weights = [1, 2, 3, 4, 5, 6, 7]
    total_weight = sum(weights)  # 28
    
    # Tính z-score và spike cho từng ngày trong lịch sử
    for i, day_data in enumerate(daily_counts):
        # Lấy 7 ngày trước ngày này để tính z-score
        # Nếu không đủ data, dùng những gì có
        if i >= 7:
            prev_7_days = historical_counts[i-7:i]
            prev_weights = weights
        else:
            # Ngày đầu tiên, không có đủ 7 ngày trước
            prev_7_days = historical_counts[:i] if i > 0 else [0]
            prev_weights = weights[:len(prev_7_days)] if prev_7_days else [1]
        
        if len(prev_7_days) > 0 and sum(prev_weights) > 0:
            # Weighted mean
            weighted_sum_day = sum(w * c for w, c in zip(prev_weights, prev_7_days))
            mean_day = weighted_sum_day / sum(prev_weights)
            
            # Weighted std
            weighted_variance_day = sum(w * (c - mean_day) ** 2 for w, c in zip(prev_weights, prev_7_days)) / sum(prev_weights)
            std_day = max(weighted_variance_day ** 0.5, 0.5)
            
            # Z-score cho ngày này
            current_count = historical_counts[i] if i < len(historical_counts) else 0
            z_score_day = (current_count - mean_day) / std_day
            
            # Spike: so sánh với ngày hôm trước
            if i > 0:
                prev_count = historical_counts[i-1]
                if prev_count > 0:
                    spike = ((current_count - prev_count) / prev_count) * 100
                else:
                    spike = 100.0 if current_count > 0 else 0.0
            else:
                spike = 0.0
            
            day_data["z_score"] = round(z_score_day, 2)
            day_data["spike"] = round(spike, 2)
        else:
            day_data["z_score"] = 0.0
            day_data["spike"] = 0.0
    
    # 6. TÍNH Z-SCORE HÔM NAY (dựa trên cùng khung giờ)
    # Weighted mean: μ = Σ(wᵢ × cᵢ) / 28
    weighted_sum = sum(w * c for w, c in zip(weights, historical_counts))
    mean = weighted_sum / total_weight
    
    # Weighted std: σ = √( Σ wᵢ(cᵢ - μ)² / 28 )
    weighted_variance = sum(w * (c - mean) ** 2 for w, c in zip(weights, historical_counts)) / total_weight
    std = weighted_variance ** 0.5
    
    # Min std = 0.5 để tránh chia cho 0
    std = max(std, 0.5)
    
    # Z-score: z = (count_now - μ) / σ
    z_score = (count_now - mean) / std
    
    # Spike hôm nay: so sánh với hôm qua
    yesterday_count = historical_counts[-1] if len(historical_counts) > 0 else 0
    if yesterday_count > 0:
        spike_today = ((count_now - yesterday_count) / yesterday_count) * 100
    else:
        spike_today = 100.0 if count_now > 0 else 0.0

    # 6. PHÂN TÍCH CẢM XÚC HÔM NAY (00h - hiện tại)
    cur.execute(
        """
        SELECT 
            COALESCE(se.sentiment, 'unknown') as sentiment,
            COUNT(*) as count
        FROM article_topic at
        JOIN news_content nc ON at.id = nc.id
        LEFT JOIN article_sentiment se ON at.id = se.id
        WHERE at.topic_id = %s
          AND nc.published_at >= %s
          AND nc.published_at <= %s
        GROUP BY se.sentiment
        """,
        (topic_id, today_start_utc, today_end_utc)
    )
    
    sentiment_rows = cur.fetchall()
    
    # Tính tổng và phần trăm
    total_sentiment_count = sum(row[1] for row in sentiment_rows)
    
    sentiment_distribution = {
        "positive": {"count": 0, "percentage": 0.0},
        "negative": {"count": 0, "percentage": 0.0},
        "neutral": {"count": 0, "percentage": 0.0}
    }
    
    if total_sentiment_count > 0:
        for sentiment, count in sentiment_rows:
            # Map sentiment key
            mapped_sentiment = sentiment_map.get(sentiment, "neutral")
            
            # Cộng dồn count (vì có thể có nhiều key map về cùng 1 sentiment)
            sentiment_distribution[mapped_sentiment]["count"] += count
        
        # Tính phần trăm sau khi đã cộng dồn
        for sentiment_type in ["positive", "negative", "neutral"]:
            count = sentiment_distribution[sentiment_type]["count"]
            percentage = round((count / total_sentiment_count) * 100, 2)
            sentiment_distribution[sentiment_type]["percentage"] = percentage
    
    # 7. TÍNH CRISIS SCORE
    # crisis_score = z_score × negative_ratio
    negative_ratio = sentiment_distribution["negative"]["percentage"] / 100.0
    crisis_score = z_score * negative_ratio

    cur.close()
    conn.close()

    return {
        "topic": topic,
        "articles_24h": articles_24h,
        "articles_history": articles_history,
        "daily_history": daily_counts,  # Full ngày (00h-23h59)
        "trend_analysis": {
            "count_now": count_now,  # Hôm nay từ 00h-hiện tại
            "weighted_mean": round(mean, 2),
            "weighted_std": round(std, 2),
            "z_score": round(z_score, 2),
            "spike": round(spike_today, 2)
        },
        "sentiment_today": {
            "total_articles": total_sentiment_count,
            "distribution": sentiment_distribution,
            "crisis_score": round(crisis_score, 2)
        }
    }
