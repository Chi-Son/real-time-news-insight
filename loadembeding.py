import psycopg2
import json
import os
import torch
from sentence_transformers import SentenceTransformer
from psycopg2.extras import execute_values
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================
# 1. Cấu hình
# ============================
# Cấu hình DB (Sử dụng localhost cho chạy trên máy Host, hoặc host.docker.internal nếu chạy trong container)
DB_CONFIG = {
    "dbname": "news",
    "user": "chison", 
    "password": "caosychison13",
    # >>> Dùng "localhost" nếu bạn đang chạy file này ngoài Docker Container
    "host": "localhost", 
    "port": "6969"
}

# Đường dẫn đã lưu mô hình SimCSE PhoBERT (Đảm bảo trùng với SAVE_PATH trong file tải model)
LOAD_PATH = "./models/ModelPhoberSim" 
# ============================
# 2. Hàm Tải Dữ liệu Topic từ DB
# ============================

def load_topics_from_db():
    """Tải topic_id, tên và mô tả từ bảng topics."""
    conn = None
    topics_data = []
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Truy vấn các cột cần thiết từ bảng topics
        sql = """
        SELECT topic_id, name, short_description, long_description, example
        FROM topic
        ORDER BY topic_id;
        """
        cur.execute(sql)
        
        for row in cur.fetchall():
            topic_id, name, short_description, long_description, examples_json = row
            
            # Xử lý cột JSONB 'examples'
            try:
                # Nếu psycopg2 không tự chuyển đổi JSONB thành list, phải dùng json.loads
                examples = examples_json if isinstance(examples_json, list) else json.loads(examples_json)
            except (TypeError, json.JSONDecodeError):
                examples = []

            topics_data.append({
                "topic_id": topic_id,
                "name": name,
                "short_description": short_description,
                "long_description": long_description,
                "example": examples
            })
            
        cur.close()
        return topics_data
        
    except Exception as e:
        logger.error(f"Lỗi khi tải dữ liệu Topic từ DB: {e}")
        return []
    finally:
        if conn:
            conn.close()

def topic_to_text(topic):
    """Kết hợp các trường của Topic thành một chuỗi duy nhất để embedding."""
    examples_text = " ".join(topic.get("example", []))
    return (
        f"{topic.get('name','')}. "
        f"{topic.get('short_description','')} "
        f"{topic.get('long_description','')} "
        f"{examples_text}"
    )

# ============================
# 3. Hàm Import Embeddings vào DB
# ============================

def insert_embeddings(topic_ids, topic_embeddings):
    """Chèn topic_id và vector vào bảng topic_embedding."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Tạo danh sách các tuple (topic_id, vector_string)
        rows = []
        for topic_id, embedding in zip(topic_ids, topic_embeddings.tolist()):
            # Chuyển list Python thành chuỗi vector e.g., "[0.123, -0.456, ...]" cho kiểu VECTOR
            vector_str = '[' + ','.join(map(str, embedding)) + ']'
            rows.append((topic_id, vector_str))

        sql = """
        INSERT INTO topic_embedding (topic_id, embedding)
        VALUES %s
        ON CONFLICT (topic_id) DO UPDATE 
        SET embedding = EXCLUDED.embedding;
        """
        execute_values(cur, sql, rows)
        conn.commit()
        logger.info(f"📥 Đã chèn/cập nhật {len(rows)} embeddings vào DB.")
        
    except Exception as e:
        logger.error(f"Lỗi khi chèn embeddings vào DB: {e}")
    finally:
        if conn:
            conn.close()

# ============================
# 4. Main Execution
# ============================


if not os.path.isdir(LOAD_PATH):
    logger.error(f"⛔️ Lỗi: Không tìm thấy thư mục model tại {LOAD_PATH}. Hãy chạy lại file tải model trước.")
    exit()

# Bước 1: Tải dữ liệu Topic
topics_data = load_topics_from_db()
if not topics_data:
    logger.warning("Không có dữ liệu Topic để xử lý.")
    exit()

topic_texts = [topic_to_text(t) for t in topics_data]
topic_ids = [t['topic_id'] for t in topics_data]
logger.info(f"Đã tải {len(topic_texts)} văn bản Topic từ DB.")

# Bước 2: Tính toán Embeddings
try:
    # Tải mô hình từ thư mục cục bộ đã lưu
    model = SentenceTransformer(LOAD_PATH)
    logger.info("✅ Model đã được tải thành công từ thư mục cục bộ.")
    
    # Encode tất cả topic texts
    topic_embeddings = model.encode(topic_texts, convert_to_tensor=True)
    logger.info(f"Đã tạo embeddings với shape: {topic_embeddings.shape}")

    # Bước 3: Import Embeddings vào DB
    insert_embeddings(topic_ids, topic_embeddings)
    
except Exception as e:
    logger.error(f"⛔️ Lỗi trong quá trình Embedding hoặc Import: {e}")