import os
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer, models

# ==========================================================
# 0. ĐƯỜNG DẪN LƯU MÔ HÌNH – CHUẨN NHẤT TRÊN WINDOWS
# ==========================================================
SAVE_PATH = r"D:\ModelPhoberSim"   # Thư mục an toàn
os.makedirs(SAVE_PATH, exist_ok=True)

model_name = "VoVanPhuc/sup-SimCSE-VietNamese-phobert-base"

print("Bắt đầu tải mô hình từ Hugging Face...")

# ==========================================================
# 1. Tải model vào cache (không ảnh hưởng thư mục lưu)
# ==========================================================
AutoTokenizer.from_pretrained(model_name)
AutoModel.from_pretrained(model_name)

print(" -> Đã tải xong vào cache.")

# ==========================================================
# 2. Khởi tạo SentenceTransformer
# ==========================================================
print("Đang đóng gói thành SentenceTransformer...")

word_embedding_model = models.Transformer(model_name_or_path=model_name)
pooling_model = models.Pooling(
    word_embedding_model.get_word_embedding_dimension(),
    pooling_mode_mean_tokens=True
)

model = SentenceTransformer(modules=[word_embedding_model, pooling_model])

# ==========================================================
# 3. Lưu mô hình với cơ chế tránh lỗi file bị khóa
# ==========================================================
print("Đang lưu mô hình...")

try:
    model.save(SAVE_PATH)
    print(f"✓ Lưu thành công tại {SAVE_PATH}")

except Exception as e:
    print("⚠️ Lỗi khi lưu:", e)
    print("→ Thử lưu lại với safe_serialization=False")
    model.save(SAVE_PATH, safe_serialization=False)
    print(f"✓ Lưu thành công với safe_serialization=False tại {SAVE_PATH}")