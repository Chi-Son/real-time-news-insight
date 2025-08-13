import hashlib
import re

# Lấy url theo đuôi nếu không thì dùng full chuyển về hash lưu cho gọn
def url_to_hash(url):
    match = re.search(r'-(\d+)\.html', url)
    article_id = match.group(1) if match else url
    return hashlib.sha256(article_id.encode()).hexdigest()

# kiểm tra duplicate
def is_duplicate(r, redis_key: str, url: str, expire_seconds: int = 43200) -> bool:
    url_hash = url_to_hash(url)
    
    if r.sismember(redis_key, url_hash):
        return True  
    
    r.sadd(redis_key, url_hash)
    r.expire(redis_key, expire_seconds)
    return False
