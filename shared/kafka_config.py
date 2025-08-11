import json
from kafka import KafkaProducer
import os
# cấu hình kafka producer
def get_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        acks='all',#xác nhận đã gửi data nhưng để all có thể chậm vì phỉa chờ toàn bộ tin xác nhận
        retries=5,# gửi lại >0 nên 3-5 lần retries nếu có lỗi
        batch_size=32768,#kích thước tối đa 1 batch 
        linger_ms=50,# thời gian chờ tối đa để gửi batch
        buffer_memory=67108864,# tổng dung lượng bộ nhớ có thể lưu batch
        compression_type='lz4',#nén tin gửi dạng lz4
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )