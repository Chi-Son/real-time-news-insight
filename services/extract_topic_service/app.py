import json
import logging
import os
import re
import torch
import psycopg2
from psycopg2.extras import DictCursor
from flashtext import KeywordProcessor
from sentence_transformers import SentenceTransformer, util
from shared.kafka_config import get_kafka_consumer,get_kafka_producer
from shared.postgresql_config import DB_CONFIG
import ast
import numpy as np
import time
# =========================
# LOGGING
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("topic_ranking")

# =========================
# KAFKA CONFIG
# =========================
INPUT_TOPIC = "extractor_news"
GROUP_ID = "topic_ranking_group"
OUTPUT_TOPIC = "extractor_topic"
producer = get_kafka_producer()
consumer = get_kafka_consumer(topic=INPUT_TOPIC, group_id=GROUP_ID)
BATCH_SIZE = 10
BATCH_TIMEOUT = 20 
batch_messages = []
last_flush_time = time.time()

# =========================
# COUNTRY STOPWORDS
# =========================
COUNTRY_STOPWORDS = [
    "pháp lý", "tư pháp", "luật pháp","pháp luật",
    "đức tính", "đức hạnh",
    "nga ngố", "nga ngáo"
]

# =========================
# PERSON NAME CHECK
# =========================
def is_person_name_around(entity_text, full_text):
    name = entity_text
    pattern_mid = rf"\b[A-ZĐ][a-zA-ZÀ-Ỵà-ỵ]+ {name} [A-ZĐ][a-zA-ZÀ-Ỵà-ỵ]+\b"
    pattern_after = rf"\b[A-ZĐ][a-zA-ZÀ-Ỵà-ỵ]+ {name}\b"
    pattern_before = rf"\b{name} [A-ZĐ][a-zA-ZÀ-Ỵà-ỵ]+\b"

    return (
        re.search(pattern_mid, full_text)
        or re.search(pattern_after, full_text)
        or re.search(pattern_before, full_text)
    )

# =========================
# FILTER COUNTRY FALSE MATCH
# =========================
def filter_country_false_matches(entities, text):
    filtered = []
    text_lower = text.lower()

    for ent in entities:
        if ent["label"] != "COUNTRY":
            filtered.append(ent)
            continue

        name = ent["text"].lower()

        if any(name in sw and sw in text_lower for sw in COUNTRY_STOPWORDS):
            continue

        if is_person_name_around(ent["text"], text):
            continue

        filtered.append(ent)

    return filtered

# =========================
# KEYWORD PROCESSOR
# =========================
keyword_processor = KeywordProcessor(case_sensitive=False)
viet_chars = set(
    "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễ"
    "ìíịỉĩòóọỏõôồốộổỗơờớợởỡ"
    "ùúụủũưừứựửữỳýỵỷỹđ"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
)
keyword_processor.non_word_boundaries = viet_chars

# =========================
# LOAD NER DATA
# =========================
def load_ner_data_from_db():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=DictCursor)

    cur.execute("SELECT type, text, aliases FROM entity;")
    count = 0

    for row in cur.fetchall():
        keyword_processor.add_keyword(row["text"], {
            "label": row["type"],
            "text": row["text"]
        })
        count += 1

        aliases = row["aliases"] or []
        if not isinstance(aliases, list):
            aliases = json.loads(aliases)

        for a in aliases:
            keyword_processor.add_keyword(a, {
                "label": row["type"],
                "text": row["text"]
            })
            count += 1

    conn.close()
    logger.info(f"Loaded {count} NER keywords")

load_ner_data_from_db()

# =========================
# ENTITY + CLEAN TEXT
# =========================
def extract_entities_and_clean(text):
    matches = keyword_processor.extract_keywords(text, span_info=True)
    unique = {m[0]["text"]: m[0] for m in matches}
    entities = filter_country_false_matches(list(unique.values()), text)
    return entities, " ".join(text.split())

# =========================
# LOAD TOPIC EMBEDDINGS
# =========================
def load_topic_embeddings():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=DictCursor)

    cur.execute("""
        SELECT t.topic_id, t.name, e.embedding
        FROM topic_embedding e
        JOIN topic t ON t.topic_id = e.topic_id
        ORDER BY t.topic_id
    """)

    topic_ids = []
    topic_names = []
    vectors = []

    for row in cur.fetchall():
        topic_ids.append(row["topic_id"])
        topic_names.append(row["name"])

        emb = row["embedding"]

        # pgvector → Python
        if not isinstance(emb, (list, tuple)):
            emb = ast.literal_eval(emb)

        vectors.append(emb)

    conn.close()

    embeddings = torch.from_numpy(
        np.asarray(vectors, dtype="float32")
    )
    embeddings = torch.nn.functional.normalize(embeddings, dim=1)

    logger.info(f"Loaded {len(topic_ids)} topic embeddings")
    return topic_ids, topic_names, embeddings

topic_ids, topic_names, topic_embeddings = load_topic_embeddings()

# =========================
# LOAD ARTICLE MODEL
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "ModelPhoberSim")

model = SentenceTransformer(MODEL_PATH)
logger.info("SentenceTransformer loaded")

# =========================
# ARTICLE TEXT FOR RANKING
# =========================
def get_text_for_ranking(title, content):
    sentences = re.split(r"(?<=[.!?])\s+", content)
    return f"{title}. {' '.join(sentences[:3])}"

logger.info("🚀 Topic Ranking Service started")

# =========================
# MAIN LOOP
# =========================

while True:
    msg = consumer.poll(1.0)
    current_time = time.time()

    # Kiểm tra timeout batch
    if batch_messages and (len(batch_messages) >= BATCH_SIZE or current_time - last_flush_time >= BATCH_TIMEOUT):
        for m in batch_messages:
            producer.produce(
                OUTPUT_TOPIC,
                key=str(m["id"]),
                value=json.dumps(m).encode("utf-8")
            )
        producer.flush()
        batch_messages.clear()
        last_flush_time = current_time

    if msg is None:
        continue
    if msg.error():
        logger.error(msg.error())
        continue

    try:
        data = json.loads(msg.value().decode("utf-8"))
        news_id = data.get("id")
        title = data.get("title")
        content = data.get("content")

        if not title or not content:
            continue

        text = get_text_for_ranking(title, content)
        entities, clean_text = extract_entities_and_clean(text)

        article_embedding = model.encode(
            [clean_text],
            convert_to_tensor=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )

        scores = util.cos_sim(article_embedding, topic_embeddings)
        top_k = min(3, len(topic_ids))
        top_scores, top_indices = torch.topk(scores[0], k=top_k)
        matched_topic_ids = [
            topic_ids[top_indices[i].item()] 
            for i in range(top_k) 
            if top_scores[i].item() > 0.65
        ]
        if matched_topic_ids:
                    logger.info(f"[NEWS {news_id}] '{title}' → Topics: {matched_topic_ids}")
                    
                    msg_out = {
                        "id": news_id,
                        "title": title,
                        "content": content,
                        "published_at": data.get("published_at"),
                        "topic_ids": matched_topic_ids,  
                        "entities": entities 
                    }
                    batch_messages.append(msg_out)

    except Exception as e:
        logger.exception(e)