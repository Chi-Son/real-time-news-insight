import requests
from bs4 import BeautifulSoup
import logging
import psycopg2
import json
import os
import time
from urllib.parse import urlparse
from dateutil import parser
from shared.kafka_config import get_kafka_consumer, get_kafka_producer
from shared.postgresql_config import DB_CONFIG
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import re
from datetime import timezone, timedelta, datetime

# -------------------------------
# Logging setup
# -------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("extractor")

# -------------------------------
# Kafka & DB config
# -------------------------------
INPUT_TOPIC = "raw_links"
GROUP_ID = "extractor_group"
OUTPUT_TOPIC = "extractor_news"

consumer = get_kafka_consumer(topic=INPUT_TOPIC, group_id=GROUP_ID)
producer = get_kafka_producer()
logger.info("URL Extractor service started.")

VN_TZ = timezone(timedelta(hours=7))

# -------------------------------
# Batch config (NEW)
# -------------------------------
BATCH_SIZE = 10
BATCH_TIMEOUT = 5  # seconds

buffer = []
last_flush_time = time.time()
pending_messages = []

def get_db_cursor():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    return conn, conn.cursor()

# -------------------------------
# Parse date helper
# -------------------------------
VN_WEEKDAY_PATTERN = re.compile(
    r"^(Thứ\s+(hai|ba|tư|năm|sáu|bảy)|Chủ\s+nhật)\s*,?\s*",
    flags=re.I
)

def parse_date_by_source(date_str: str, source: str):
    if not date_str:
        return None

    # ❌ bỏ (GMT+7)
    cleaned = re.sub(r"\(GMT[^\)]*\)", "", date_str)

    # ❌ bỏ "Cập nhật:"
    cleaned = re.sub(r"Cập nhật:\s*", "", cleaned, flags=re.I)

    # ❌ bỏ weekday tiếng Việt (VNExpress, Tuổi Trẻ, ...)
    cleaned = VN_WEEKDAY_PATTERN.sub("", cleaned)

    cleaned = cleaned.strip()

    try:
        # 1️⃣ ISO có timezone
        if re.search(r"[+-]\d{2}:\d{2}$", cleaned):
            dt = parser.isoparse(cleaned)
            return dt.astimezone(timezone.utc).isoformat(timespec="seconds")

        # 2️⃣ ISO không tz (format: YYYY-MM-DD HH:MM hoặc YYYY-MM-DD HH:MM:SS)
        if re.match(r"\d{4}-\d{2}-\d{2}", cleaned):
            dt = parser.parse(cleaned)
            dt = dt.replace(tzinfo=VN_TZ)
            return dt.astimezone(timezone.utc).isoformat(timespec="seconds")

        # 3️⃣ VN format dd/mm/yyyy HH:MM
        # Ví dụ: "28/02/2026 - 06:10" hoặc "28/02/2026, 06:10"
        if re.match(r"\d{2}/\d{2}/\d{4}", cleaned):
            dt = parser.parse(cleaned, dayfirst=True)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=VN_TZ)
            return dt.astimezone(timezone.utc).isoformat(timespec="seconds")

        # 4️⃣ Fallback: parse tự động
        dt = parser.parse(cleaned, dayfirst=True)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=VN_TZ)

        return dt.astimezone(timezone.utc).isoformat(timespec="seconds")

    except Exception as e:
        logger.warning(
            f"[DATE_PARSE_FAIL] source={source} | raw='{date_str}' | cleaned='{cleaned}' | err={e}"
        )
        return None



# -------------------------------
# Detect source from URL
# -------------------------------
SOURCES_FILE = os.path.join(os.path.dirname(__file__), "rss_sources.json")
with open(SOURCES_FILE, "r", encoding="utf-8") as f:
    SOURCES_MAP = json.load(f)

DOMAIN_TO_SOURCE = {}
for source_name, urls in SOURCES_MAP.items():
    for url in urls:
        DOMAIN_TO_SOURCE[urlparse(url).netloc.replace("www.", "")] = source_name

def detect_source(url):
    return DOMAIN_TO_SOURCE.get(urlparse(url).netloc.replace("www.", ""), "Unknown")





# -------------------------------
# Extract article
# -------------------------------
def extract_article(url, source_name, driver=None):
    try:
        # 🟩 Nhóm cần Selenium (JS-rendered)
        if source_name in ["Tuổi trẻ", "VTV", "Thanh niên", "Người lao động", "Dân trí"] and driver:
            driver.get(url)
            driver.implicitly_wait(3)

            # Nội dung - Dân Trí có selector riêng
            content = None
            if source_name == "Dân trí":
                # Thử các selector của Dân Trí
                content_selectors = [
                    "div.singular-content",
                    "div.e-magazine__body", 
                    "div.dnews__body",
                    "article.singular-content"
                ]
                for selector in content_selectors:
                    try:
                        elem = driver.find_element(By.CSS_SELECTOR, selector)
                        # Lấy text từ các thẻ p
                        paragraphs = elem.find_elements(By.TAG_NAME, "p")
                        content = " ".join([p.text.strip() for p in paragraphs if len(p.text.strip()) > 30])
                        if content:
                            break
                    except:
                        continue
            else:
                # Các báo khác dùng selector chung
                try:
                    content = driver.find_element(By.CSS_SELECTOR, "div.detail-content.afcbc-body").text
                except:
                    pass
            
            if not content or len(content.split()) < 70:
                logger.info(f"Bỏ bài {url} vì nội dung quá ít")
                return None

            # Title
            title = None
            try:
                title = driver.find_element(By.CSS_SELECTOR, "meta[property='og:title']").get_attribute("content")
            except:
                try:
                    title_elem = driver.find_element(By.TAG_NAME, "title")
                    title = title_elem.text.split(" - ")[0] if title_elem else None
                except:
                    pass
            
            if title and title.strip().startswith("Tin tức"):
                logger.info(f"Bỏ qua bài viết {url} vì tiêu đề bắt đầu bằng 'Tin tức'")
                return None
            # Date
            published_at = None

            # 1️⃣ meta tag
            try:
                meta_date = driver.find_elements(By.CSS_SELECTOR, "meta[property='article:published_time']")
                if meta_date:
                    published_at = meta_date[0].get_attribute("content")
            except:
                pass

            # 2️⃣ span/div.date hoặc time.dt-flex (Dân Trí)
            if not published_at:
                try:
                    date_elem = driver.find_elements(By.CSS_SELECTOR, "span.date, div.date, time.dt-flex")
                    if date_elem:
                        datetime_attr = date_elem[0].get_attribute("datetime")
                        text_attr = date_elem[0].text.strip()
                        published_at = parse_date_by_source(datetime_attr or text_attr, source_name)
                except:
                    pass

            # 3️⃣ thẻ <time> (author-time, e-magazine_meta-item, time)
            if not published_at:
                try:
                    time_elem = driver.find_elements(
                        By.CSS_SELECTOR,
                        "time.author-time, time.e-magazine_meta-item, div.article_meta time.time, time"
                    )
                    if time_elem:
                        datetime_attr = time_elem[0].get_attribute("datetime")
                        text_attr = time_elem[0].text.strip()
                        published_at = parse_date_by_source(datetime_attr or text_attr,source_name)
                except:
                    pass
            

            return {"title": title, "content": content, "published_at": published_at}

        # 🟦 Nhóm trang tĩnh (Requests + BeautifulSoup)
        else:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                logger.warning(f"URL {url} trả về status {resp.status_code}")
                return None

            soup = BeautifulSoup(resp.text, "html.parser")

            # Map class nội dung
            content_classes = {
                "Nhân dân": "article__body zce-content-body cms-body",
                "Dân trí": ["singular-content", "e-magazine__body", "dnews__body"],
                "VN Express": "fck_detail",
            }

            container_class = content_classes.get(source_name)
            if not container_class:
                article_tag = soup.find("article")
            else:
                if isinstance(container_class, list):
                    article_tag = None
                    for cls in container_class:
                        article_tag = (
                            soup.find("div", class_=cls)
                            or soup.find("article", class_=cls)
                        )
                        if article_tag:
                            break
                else:
                    article_tag = (
                        soup.find("div", class_=container_class)
                        or soup.find("article", class_=container_class)
                    )

            if not article_tag:
                logger.warning(f"Không tìm thấy nội dung {source_name}: {url}")
                return None

            # Clean paragraphs
            paragraphs = [
                p.get_text(" ", strip=True)
                for p in article_tag.find_all(["p", "div"])
                if len(p.get_text(strip=True)) > 30
            ]

            clean_paragraphs = []
            for text in paragraphs:
                text_lower = text.lower()
                if (
                    not text.startswith(("Ảnh:", "Hình:", "Photo:"))
                    and not re.search(r"\S+@\S+", text)
                    and not re.search(r"0\d{9,10}", text)
                    and "bình luận" not in text_lower
                    and not any(text.startswith(x) for x in ("©", "Đăng bởi", "By", "Phóng viên"))
                    and not any(kw in text_lower for kw in ["dành cho bạn", "có thể bạn quan tâm", "xem thêm"])
                ):
                    clean_paragraphs.append(text)

            # Nếu dòng cuối là tên tác giả, bỏ
            if clean_paragraphs:
                last_line = clean_paragraphs[-1].strip()
                if re.match(r"^[A-ZÀ-Ỹ][a-zà-ỹ]+(\s[A-ZÀ-Ỹ][a-zà-ỹ]+){0,2}$", last_line):
                    clean_paragraphs = clean_paragraphs[:-1]

            content = " ".join(clean_paragraphs)
            if not content or len(content.split()) < 70:
                logger.info(f"Bỏ bài {url} vì nội dung quá ít")
                return None


            # Title
            title = None
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                title = og_title["content"].strip()
            elif soup.title:
                title = soup.title.string.strip().rsplit(" - ", 1)[0]

            # 📅 Date (đầy đủ, tương thích nhiều loại báo)
            published_at = None

            # 1️⃣ meta property
            meta_date = soup.find("meta", property="article:published_time")
            if meta_date and meta_date.get("content"):
                published_at = parse_date_by_source(meta_date["content"],source_name)

            # 2️⃣ span/div date (bao gồm VNExpress)
            if not published_at:
                date_div = (
                    soup.select_one("div.header-content span.date")  # VNExpress
                    or soup.find("span", class_="date")
                    or soup.find("div", class_="date")
                )
                if date_div:
                    published_at = parse_date_by_source(
    date_div.get_text(strip=True),
    source_name
)

            # 3️⃣ <time> dạng đặc biệt (VTV, Nhân Dân, Dân Trí e-magazine)
            if not published_at:
                time_tag = (
                    soup.select_one("div.article_meta time.time")
                    or soup.find("time", class_="author-time")
                    or soup.find("time", class_="e-magazine_meta-item")
                    or soup.find("time", class_="dt-flex")  # Dân Trí mới
                    or soup.find("time")
                )
                if time_tag:
                    # Ưu tiên lấy datetime attribute
                    datetime_attr = time_tag.get("datetime")
                    text_content = time_tag.text.strip()
                    
                    published_at = parse_date_by_source(
                        datetime_attr or text_content,
                        source_name
                    )

            return {"title": title, "content": content, "published_at": published_at}

    except Exception as e:
        logger.error(f"Lỗi extract {url}: {e}")
        return None
def normalize_to_vn_timezone(article):
    """
    Chuyển article['published_at'] sang timezone VN (+07)
    """
    if not article or not article.get("published_at"):
        return article

    try:
        dt = parser.isoparse(article["published_at"])
        dt_vn = dt.astimezone(VN_TZ)
        article["published_at"] = dt_vn.isoformat(timespec="seconds")
    except Exception as e:
        logger.warning(f"Không chuẩn hóa được date bài ID={article.get('id')}, giữ nguyên: {e}")

    return article

# -------------------------------
# Main loop
# -------------------------------


chrome_options = Options()
chrome_options.add_argument("--headless=new")  # hoặc "--headless"
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--remote-debugging-port=9222")  # tạo DevToolsActivePort

driver = webdriver.Chrome(
    service=Service("/usr/bin/chromedriver"),
    options=chrome_options
)

try:
    while True:
        message = consumer.poll(1.0)
        if message is None: continue
        if message.error():
            logger.error(f"Consumer error: {message.error()}")
            continue

        # Bắt đầu đếm thời gian xử lý
        start_time = time.time()
        TIMEOUT_SECONDS = 240  # 4 phút (để có buffer trước 5 phút)

        try:
            msg = json.loads(message.value().decode("utf-8"))
            news_id, url, category = msg.get("id"), msg.get("url"), msg.get("category")

            if not news_id or not url: 
                consumer.commit(message)
                continue

            # Kiểm tra timeout trước khi xử lý
            if time.time() - start_time > TIMEOUT_SECONDS:
                logger.warning(f"⏱️ Timeout trước khi xử lý ID={news_id}, bỏ qua")
                consumer.commit(message)
                continue

            source = detect_source(url)
            article = extract_article(url, source_name=source, driver=driver)

            # Kiểm tra timeout sau extract
            if time.time() - start_time > TIMEOUT_SECONDS:
                logger.warning(f"⏱️ Timeout sau extract ID={news_id}, bỏ qua và commit")
                consumer.commit(message)
                continue

            # Chuẩn hóa múi giờ về +07
            article = normalize_to_vn_timezone(article)

            
            # 🛑 CHẶN Ở ĐÂY: Nếu không có ngày hoặc nội dung, không làm gì cả
            if not article or not article.get("published_at"):
                logger.warning(f"Bỏ qua ID={news_id} vì thiếu ngày xuất bản (published_at=null)")
                # Vẫn commit offset để không bị lặp lại message lỗi này
                consumer.commit(message) 
                continue

            # Chỉ khi có ngày mới tiến hành lưu DB và gửi Kafka
            conn, cur = get_db_cursor()
            try:
                cur.execute("""
                    INSERT INTO news_content(id, title, content, source, published_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (news_id, article["title"], article["content"], source, article["published_at"]))
                
                msg_out = {
                    "id": news_id,
                    "title": article["title"],
                    "content": article["content"],
                    "published_at": article["published_at"],
                    "category": category  
                }
                
                producer.produce(
                    OUTPUT_TOPIC,
                    key=str(news_id),
                    value=json.dumps(msg_out, ensure_ascii=False).encode("utf-8")
                )
                producer.flush()
                
                elapsed = time.time() - start_time
                logger.info(f"✔ Thành công ID={news_id} | Date={article['published_at']} | Time={elapsed:.1f}s")
                consumer.commit(asynchronous=False)
            finally:
                cur.close()
                conn.close()

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Lỗi xử lý message (time={elapsed:.1f}s): {e}")
            # Commit để không bị stuck
            consumer.commit(message)

finally:
    consumer.close()
    driver.quit()
