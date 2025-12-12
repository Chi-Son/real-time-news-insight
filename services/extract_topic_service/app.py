import json
import logging
import os
import re
from flashtext import KeywordProcessor
from sentence_transformers import SentenceTransformer, util, models
import torch
import psycopg2
from psycopg2.extras import DictCursor
from shared.kafka_config import get_kafka_consumer, get_kafka_producer
from shared.postgresql_config import DB_CONFIG

SentenceTransformer.default_transaction_allocator = None
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("topic_ranking")

INPUT_TOPIC = "extractor_news"
GROUP_ID = "topic_ranking_group"

consumer = get_kafka_consumer(topic=INPUT_TOPIC, group_id=GROUP_ID)
producer = get_kafka_producer()

# =====================================================
# COUNTRY STOPWORDS (để tránh bắt nhầm)
# =====================================================
COUNTRY_STOPWORDS = [
    "pháp lý", "tư pháp", "luật pháp","pháp luật"
    "đức tính", "đức hạnh",
    "nga ngố", "nga ngáo"
]

# =====================================================
# Detect tên người để loại COUNTRY
# =====================================================
def is_person_name_around(entity_text, full_text):
    """
    Kiểm tra xem thực thể COUNTRY có nằm trong tên người không.
    Đức/Nga/Bỉ/Pháp → nếu nằm trong cụm tên người thì loại.
    """
    name = entity_text

    pattern_mid = rf"\b[A-ZĐ][a-zA-ZÀ-Ỵà-ỵ]+ {name} [A-ZĐ][a-zA-ZÀ-Ỵà-ỵ]+\b"
    pattern_after = rf"\b[A-ZĐ][a-zA-ZÀ-Ỵà-ỵ]+ {name}\b"
    pattern_before = rf"\b{name} [A-ZĐ][a-zA-ZÀ-Ỵà-ỵ]+\b"

    if re.search(pattern_mid, full_text):
        return True
    if re.search(pattern_after, full_text):
        return True
    if re.search(pattern_before, full_text):
        return True

    return False

# =====================================================
# Filter COUNTRY sai
# =====================================================
def filter_country_false_matches(entities, text):
    filtered = []
    text_lower = text.lower()

    for ent in entities:
        if ent["label"] != "COUNTRY":
            filtered.append(ent)
            continue

        name = ent["text"]
        name_lower = name.lower()

        # Nếu dính stopword → loại
        for sw in COUNTRY_STOPWORDS:
            if sw in text_lower:
                if name_lower in sw or name_lower == sw.split()[-1]:
                    break
        else:
            sw = None

        if sw:
            continue

        # Nếu nằm trong tên người → loại
        if is_person_name_around(name, text):
            continue

        filtered.append(ent)

    return filtered

# =====================================================
# KeywordProcessor setup
# =====================================================
keyword_processor = KeywordProcessor(case_sensitive=False)
viet_chars = set(
    "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễ"
    "ìíịỉĩòóọỏõôồốộổỗơờớợởỡ"
    "ùúụủũưừứựửữỳýỵỷỹđ"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
)
keyword_processor.non_word_boundaries = viet_chars

# =====================================================
# Load NER from DB
# =====================================================
def load_ner_data_from_db():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute("SELECT type, text, aliases FROM entity;")
        count = 0
        for ent in cur.fetchall():
            main_name = ent["text"]
            keyword_processor.add_keyword(main_name, {
                "label": ent["type"],
                "text": main_name
            })
            count += 1

            aliases = ent["aliases"] if isinstance(ent["aliases"], list) else json.loads(ent["aliases"])
            for alias in aliases:
                keyword_processor.add_keyword(alias, {
                    "label": ent["type"],
                    "text": main_name
                })
                count += 1

        logger.info(f"Đã tải {count} từ khóa NER từ DB.")
    except Exception as e:
        logger.error(f"Lỗi load NER: {e}")
    finally:
        if conn:
            conn.close()

load_ner_data_from_db()

# =====================================================
# Extract entities (dedupe) + clean text
# =====================================================
def extract_entities_and_clean(text):
    matches = keyword_processor.extract_keywords(text, span_info=True)

    unique = {}
    for ent_info, start, end in matches:
        unique[ent_info["text"]] = ent_info  # dedupe

    entities = list(unique.values())

    # Filter COUNTRY sai (tên người + stopword)
    entities = filter_country_false_matches(entities, text)

    cleaned = " ".join(text.split())
    return entities, cleaned

# =====================================================
# Load topics from DB
# =====================================================
def load_topics_from_db():
    conn = None
    topics = []
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute("SELECT topic_id, name, short_description, long_description, example FROM topic ORDER BY topic_id;")

        for row in cur.fetchall():
            examples = row["example"] if isinstance(row["example"], list) else json.loads(row["example"])
            topics.append({
                "topic_id": row["topic_id"],
                "name": row["name"],
                "short_description": row["short_description"],
                "long_description": row["long_description"],
                "examples": examples
            })

        logger.info(f"Đã tải {len(topics)} topics từ DB.")
        return topics

    except Exception as e:
        logger.error(f"Lỗi load topics: {e}")
        return []
    finally:
        if conn:
            conn.close()

topics_data = load_topics_from_db()
topic_ids = [t["topic_id"] for t in topics_data]
topic_texts = [
    f"{t['name']}. {t['short_description']} {t['long_description']} {' '.join(t['examples'])}"
    for t in topics_data
]

# =====================================================
# Load local model PhoberSim
# =====================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
LOAD_PATH = os.path.join(current_dir, "models", "ModelPhoberSim")

if not os.path.isdir(LOAD_PATH):
    logger.error(f"Không tìm thấy model tại {LOAD_PATH}")
    exit()

word_embedding_model = models.Transformer(LOAD_PATH)
pooling_model = models.Pooling(
    word_embedding_model.get_word_embedding_dimension(),
    pooling_mode_mean_tokens=True
)
model = SentenceTransformer(modules=[word_embedding_model, pooling_model])

topic_embeddings = model.encode(topic_texts, convert_to_tensor=True,show_progress_bar=False)

logger.info(f"Model loaded. Topic embeddings shape: {topic_embeddings.shape}")
logger.info("Topic Ranking Service started.")

# =====================================================
# Lấy title + 4 câu đầu content
# =====================================================
def get_text_for_ranking(title, content):
    sentences = re.split(r"(?<=[.!?])\s+", content)
    first_4 = " ".join(sentences[:4])
    return f"{title}. {first_4}"

# =====================================================
# MAIN KAFKA LOOP
# =====================================================
while True:
    message = consumer.poll(1.0)
    if message is None:
        continue
    if message.error():
        logger.error(f"Consumer error: {message.error()}")
        continue

    try:
        msg = json.loads(message.value().decode("utf-8"))
        news_id = msg.get("id")
        title = msg.get("title")
        content = msg.get("content")

        if not news_id or not content:
            logger.warning(f"Message không hợp lệ: {msg}")
            continue

        # Lấy phần dùng để phân loại
        text_for_rank = get_text_for_ranking(title, content)

        # Detect entities
        entities, cleaned_text = extract_entities_and_clean(text_for_rank)
        if entities:
            logger.info(f"ID={news_id}, Entities detected:")
            for ent in entities:
                logger.info(f" - [{ent['label']}] {ent['text']}")

        # Ranking topic
        article_embedding = model.encode([cleaned_text], convert_to_tensor=True,show_progress_bar=False)
        scores = util.cos_sim(article_embedding, topic_embeddings)

        top_score, top_idx = torch.max(scores[0], dim=0)

        if top_score.item() > 0.51:
            topic_id = topic_ids[top_idx.item()]
            topic_name = topics_data[top_idx.item()]["name"]
            logger.info(f"ID={news_id}, Top topic: [{topic_id}] {topic_name} (score={top_score.item():.4f})")

    except Exception as e:
        logger.error(f"Lỗi xử lý message: {e}")
