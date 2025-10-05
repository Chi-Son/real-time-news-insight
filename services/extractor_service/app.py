import requests
from bs4 import BeautifulSoup
import logging
import psycopg2
import json
import os
import time
from urllib.parse import urlparse
from dateutil import parser
from shared.kafka_config import get_kafka_consumer
from shared.postgresql_config import DB_CONFIG
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import re

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

consumer = get_kafka_consumer(topic=INPUT_TOPIC, group_id=GROUP_ID)
logger.info("URL Extractor service started.")

def get_db_cursor():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    return conn, conn.cursor()

# -------------------------------
# Parse date helper
# -------------------------------
def parse_date(date_str: str):
    if not date_str:
        return None
    try:
        cleaned = re.sub(r"Thứ\s+\w+,\s*", "", date_str)
        cleaned = re.sub(r"\(GMT[^\)]*\)", "", cleaned)
        cleaned = re.sub(r"Cập nhật:\s*", "", cleaned)
        cleaned = cleaned.strip()
        dt = parser.parse(cleaned, dayfirst=True)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
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
        domain = urlparse(url).netloc.replace("www.", "")
        DOMAIN_TO_SOURCE[domain] = source_name

def detect_source(url):
    domain = urlparse(url).netloc.replace("www.", "")
    return DOMAIN_TO_SOURCE.get(domain, "Unknown")

# -------------------------------
# Extract article
# -------------------------------
def extract_article(url, source_name, driver=None):
    try:
        # 🟩 NHÓM CẦN SELENIUM (JS-rendered)
        if source_name in ["Tuổi trẻ", "VTV", "Thanh niên", "Người lao động"] and driver:
            driver.get(url)
            driver.implicitly_wait(3)

            # Lấy nội dung chính
            content = driver.find_element(By.CSS_SELECTOR, "div.detail-content.afcbc-body").text

            # Lấy title
            title = None
            try:
                title = driver.find_element(By.CSS_SELECTOR, "meta[property='og:title']").get_attribute("content")
            except:
                try:
                    title_elem = driver.find_element(By.TAG_NAME, "title")
                    title = title_elem.text.split(" - ")[0] if title_elem else None
                except:
                    pass

            # Lấy ngày đăng
            published_at = None
            try:
                published_at = driver.find_element(
                    By.CSS_SELECTOR, "meta[property='article:published_time']"
                ).get_attribute("content")
            except:
                pass

            return {"title": title, "content": content, "published_at": published_at}

        # 🟦 NHÓM TRANG TĨNH (Requests + BeautifulSoup)
        else:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                logger.warning(f"URL {url} trả về status {resp.status_code}")
                return None

            soup = BeautifulSoup(resp.text, "html.parser")

            # Map từng trang vào class riêng
            content_classes = {
                "Nhân dân": "article__body zce-content-body cms-body",
                "Dân trí": "singular-content",
                "VN Express": "fck_detail",
            }

            # Xác định class container
            container_class = content_classes.get(source_name)

            if not container_class:
                article_tag = soup.find("article")
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
                p.get_text(strip=True)
                for p in article_tag.find_all("p")
                if len(p.get_text(strip=True)) > 30
            ]
            clean_paragraphs = [
                text
                for text in paragraphs
                if not text.startswith(("Ảnh:", "Hình:", "Photo:"))
                and not re.search(r"\S+@\S+", text)
                and not re.search(r"0\d{9,10}", text)
                and "bình luận" not in text.lower()
                and not any(text.startswith(x) for x in ("©", "Đăng bởi", "By", "Phóng viên"))
            ]

            if clean_paragraphs:
                last_line = clean_paragraphs[-1].strip()
                if re.match(r"^[A-ZÀ-Ỹ][a-zà-ỹ]+(\s[A-ZÀ-Ỹ][a-zà-ỹ]+){0,2}$", last_line):
                    clean_paragraphs = clean_paragraphs[:-1]

            content = " ".join(clean_paragraphs)

            # Title
            title = None
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                title = og_title["content"].strip()
            elif soup.title:
                title = soup.title.string.strip().rsplit(" - ", 1)[0]

            # Date
            published_at = None
            meta_date = soup.find("meta", property="article:published_time")
            if meta_date and meta_date.get("content"):
                published_at = meta_date["content"]
            else:
                date_div = soup.find("span", class_="date") or soup.find("div", class_="date")
                if date_div:
                    published_at = parse_date(date_div.get_text(strip=True))

            return {"title": title, "content": content, "published_at": published_at}

    except Exception as e:
        logger.error(f"Lỗi extract {url}: {e}")
        return None


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
        if message is None:
            continue
        if message.error():
            logger.error(f"Consumer error: {message.error()}")
            continue

        try:
            msg = json.loads(message.value().decode("utf-8"))
            news_id = msg.get("id")
            url = msg.get("url")

            if not news_id or not url:
                logger.warning(f"Bỏ qua message không hợp lệ: {msg}")
                continue

            source = detect_source(url)
            logger.info(f"Đang xử lý ID={news_id}, URL={url}, source={source}")

            article = extract_article(url, source_name=source, driver=driver)
            if not article:
                continue

            conn, cur = get_db_cursor()
            try:
                cur.execute("""
                    INSERT INTO news_content(id, title, content, source, published_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (news_id, article["title"], article["content"], source, article["published_at"]))
                logger.info(f"Đã lưu bài ID={news_id}, source={source}")
            finally:
                cur.close()
                conn.close()

        except Exception as e:
            logger.error(f"Lỗi xử lý message: {e}")
            time.sleep(1)

finally:
    consumer.close()
    driver.quit()
