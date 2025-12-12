import json
import psycopg2 # Thay bằng thư viện DB bạn sử dụng (ví dụ: mysql.connector)

# ============================
# Cấu hình kết nối Database
# ============================
DB_CONFIG = {
    "dbname": "news",        
    "user": "chison",      
    "password": "caosychison13",  
    "host": "localhost",
    "port": "6969"
}

# Đường dẫn đến file JSON
NER_FILE_PATH = "data/Ner.json"   # Thay đổi đường dẫn này
TOPIC_FILE_PATH = "data/Topic_describe.json" # Thay đổi đường dẫn này

def load_json_file(file_path):
    """Đọc dữ liệu từ file JSON."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file tại {file_path}")
        return None

def import_ner_data(conn, ner_data):
    """Import dữ liệu NER vào bảng ner_data."""
    print(f"--- Bắt đầu Import NER ({len(ner_data)} entities) ---")
    cursor = conn.cursor()
    
    # Câu lệnh SQL INSERT cho bảng ner_data (sử dụng kiểu JSONB cho aliases)
    sql = """
    INSERT INTO entity (entity_id, type, text, normalized, aliases)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (entity_id) DO UPDATE 
    SET type = EXCLUDED.type, text = EXCLUDED.text, normalized = EXCLUDED.normalized, aliases = EXCLUDED.aliases;
    """
    
    count = 0
    for item in ner_data:
        # psycop2 yêu cầu chuyển đổi list/dict Python sang string JSON để chèn vào cột JSONB
        aliases_json = json.dumps(item.get("aliases", []))
        
        try:
            cursor.execute(sql, (
                item["entity_id"],
                item["type"],
                item["text"],
                item.get("normalized"),
                aliases_json
            ))
            count += 1
        except Exception as e:
            print(f"Lỗi khi import entity ID {item['entity_id']}: {e}")
            conn.rollback()
            return
            
    conn.commit()
    print(f"✅ Hoàn tất Import NER: {count} bản ghi đã được chèn/cập nhật.")


def import_topic_data(conn, topics_data):
    """Import dữ liệu Topic vào bảng topics."""
    print(f"\n--- Bắt đầu Import TOPIC ({len(topics_data)} topics) ---")
    cursor = conn.cursor()
    
    # Câu lệnh SQL INSERT cho bảng topics (sử dụng kiểu JSONB cho examples)
    sql = """
    INSERT INTO topic (topic_id, parent_id, name, short_description, long_description, example, level)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (topic_id) DO UPDATE 
    SET parent_id = EXCLUDED.parent_id, name = EXCLUDED.name, 
        short_description = EXCLUDED.short_description, 
        long_description = EXCLUDED.long_description, 
        example = EXCLUDED.example, 
        level = EXCLUDED.level;
    """
    
    count = 0
    for item in topics_data:
        # psycop2 yêu cầu chuyển đổi list/dict Python sang string JSON để chèn vào cột JSONB
        examples_json = json.dumps(item.get("examples", []))
        
        try:
            cursor.execute(sql, (
                item["topic_id"],
                item["parent_id"],
                item["name"],
                item.get("short_description"),
                item.get("long_description"),
                examples_json,
                item.get("level")
            ))
            count += 1
        except Exception as e:
            print(f"Lỗi khi import topic ID {item['topic_id']}: {e}")
            conn.rollback()
            return
            
    conn.commit()
    print(f"✅ Hoàn tất Import TOPIC: {count} bản ghi đã được chèn/cập nhật.")


def main():
    ner_data = load_json_file(NER_FILE_PATH)
    topics_data = load_json_file(TOPIC_FILE_PATH)
    
    if ner_data is None or topics_data is None:
        return

    conn = None
    try:
        # Kết nối đến DB
        conn = psycopg2.connect(**DB_CONFIG)
        
        # 1. Import NER
        import_ner_data(conn, ner_data)
        
        # 2. Import TOPIC
        import_topic_data(conn, topics_data)
        
    except Exception as e:
        print(f"Lỗi kết nối DB hoặc lỗi chung: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()