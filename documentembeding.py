import psycopg2
import os
import torch
import numpy as np
from sentence_transformers import SentenceTransformer
from psycopg2.extras import execute_values
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================
# 1. Config
# ============================

DB_CONFIG = {
    "dbname": "news",
    "user": "chison",
    "password": "caosychison13",
    "host": "localhost",
    "port": "6969"
}

LOAD_PATH = "./models/ModelPhoberSim"
BATCH_SIZE = 64   # tăng nếu RAM/GPU cho phép (128 cũng ok)

# ============================
# 2. Load ALL topic_documents
# ============================

def load_all_topic_documents():
    """
    Return:
    - topic_ids: list[int]
    - texts: list[str]
    - weights: torch.Tensor [N]
    """
    conn = None
    topic_ids = []
    texts = []
    weights = []

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        sql = """
        SELECT topic_id, text, weight
        FROM topic_documents
        ORDER BY topic_id;
        """
        cur.execute(sql)

        for topic_id, text, weight in cur.fetchall():
            topic_ids.append(topic_id)
            texts.append(text)
            weights.append(float(weight))

        cur.close()

    except Exception as e:
        logger.error(f"Lỗi load topic_documents: {e}")
        return [], [], None

    finally:
        if conn:
            conn.close()

    return topic_ids, texts, torch.tensor(weights, dtype=torch.float32)

# ============================
# 3. Insert centroids
# ============================

def insert_centroids(topic_ids, centroids):
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        rows = []
        for topic_id, centroid in zip(topic_ids, centroids):
            vector_str = '[' + ','.join(map(str, centroid.tolist())) + ']'
            rows.append((topic_id, vector_str))

        sql = """
        INSERT INTO topic_embedding (topic_id, embedding)
        VALUES %s
        ON CONFLICT (topic_id) DO UPDATE
        SET embedding = EXCLUDED.embedding;
        """
        execute_values(cur, sql, rows)
        conn.commit()

        logger.info(f"📥 Insert/Update {len(rows)} topic centroids")

    except Exception as e:
        logger.error(f"Lỗi insert centroid: {e}")

    finally:
        if conn:
            conn.close()

# ============================
# 4. Main (FAST VERSION)
# ============================

if not os.path.isdir(LOAD_PATH):
    logger.error(f"⛔ Không tìm thấy model tại {LOAD_PATH}")
    exit()

# Load data
topic_ids_all, texts_all, weights_all = load_all_topic_documents()
if not texts_all:
    logger.error("⛔ Không có dữ liệu topic_documents")
    exit()

logger.info(f"📄 Loaded {len(texts_all)} documents")

# Load model
model = SentenceTransformer(LOAD_PATH)
logger.info("✅ Model loaded")

# ============================
# EMBED 1 PHÁT DUY NHẤT
# ============================

embeddings_all = model.encode(
    texts_all,
    batch_size=BATCH_SIZE,
    convert_to_tensor=True,
    normalize_embeddings=True,
    show_progress_bar=True
)

logger.info(f"🧠 Embedding shape: {embeddings_all.shape}")

# ============================
# GROUP + WEIGHTED CENTROID
# ============================

topic_to_indices = defaultdict(list)
for idx, topic_id in enumerate(topic_ids_all):
    topic_to_indices[topic_id].append(idx)

final_topic_ids = []
final_centroids = []

for topic_id, indices in topic_to_indices.items():
    emb = embeddings_all[indices]              # [N, D]
    w = weights_all[indices].unsqueeze(1)       # [N, 1]

    centroid = torch.sum(emb * w, dim=0) / torch.sum(w)
    centroid = torch.nn.functional.normalize(centroid, p=2, dim=0)

    final_topic_ids.append(topic_id)
    final_centroids.append(centroid)

logger.info(f"🎯 Computed centroids for {len(final_topic_ids)} topics")

# ============================
# SAVE TO DB
# ============================

insert_centroids(final_topic_ids, final_centroids)
