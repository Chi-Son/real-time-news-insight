import hashlib
import re

# Lấy url theo đuôi nếu không thì dùng full chuyển về hash lưu cho gọn
def url_to_hash(url):
    match = re.search(r'-(\d+)\.html', url)
    article_id = match.group(1) if match else url
    return hashlib.sha256(article_id.encode()).hexdigest()

