import os
import redis
def redis_connection():
    # Kết nối đến Redis
    redis_host = os.getenv("REDIS_HOST", "redis")  
    return redis.Redis(host=redis_host, port=6379, db=0, decode_responses=False)