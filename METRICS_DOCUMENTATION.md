# Tài liệu Hệ thống Chấm điểm và Cảnh báo

## Tổng quan
Hệ thống sử dụng 3 chỉ số chính để phát hiện và cảnh báo các chủ đề đang có xu hướng bất thường:
1. **Z-Score** - Đo lường mức độ bất thường của số lượng bài viết
2. **Spike** - Đo lường tốc độ tăng trưởng so với ngày trước
3. **Crisis Score** - Đo lường mức độ nghiêm trọng dựa trên Z-Score và cảm xúc tiêu cực

---

## 1. Z-Score (Điểm chuẩn hóa)

### Mục đích
Đo lường xem số lượng bài viết hôm nay có bất thường so với 7 ngày trước hay không.

### Công thức tính

```
Z-Score = (count_now - μ) / σ

Trong đó:
- count_now: Số bài viết hôm nay (từ 00:00 đến giờ hiện tại)
- μ (mu): Trung bình có trọng số của 7 ngày trước
- σ (sigma): Độ lệch chuẩn có trọng số của 7 ngày trước
```

### Chi tiết tính toán

#### Bước 1: Lấy dữ liệu 7 ngày trước
- Lấy số lượng bài viết của 7 ngày trước đó
- **Quan trọng**: Sử dụng cùng khung giờ (00:00 → giờ hiện tại) để so sánh công bằng
- Ví dụ: Nếu bây giờ là 14:23, thì lấy số bài từ 00:00-14:23 của mỗi ngày

#### Bước 2: Tính trung bình có trọng số (Weighted Mean)
```
Trọng số: [1, 2, 3, 4, 5, 6, 7]
- Ngày 1 (xa nhất): trọng số = 1
- Ngày 2: trọng số = 2
- ...
- Ngày 7 (gần nhất): trọng số = 7

μ = Σ(wᵢ × cᵢ) / 28

Trong đó:
- wᵢ: Trọng số của ngày thứ i
- cᵢ: Số bài viết của ngày thứ i
- 28: Tổng trọng số (1+2+3+4+5+6+7)
```

**Ý nghĩa**: Ngày gần đây có ảnh hưởng lớn hơn đến trung bình.

#### Bước 3: Tính độ lệch chuẩn có trọng số (Weighted Standard Deviation)
```
σ = √( Σ wᵢ(cᵢ - μ)² / 28 )

Nếu σ < 0.5 thì σ = 0.5 (tránh chia cho 0)
```

**Ý nghĩa**: Đo lường mức độ biến động của dữ liệu.

#### Bước 4: Tính Z-Score
```
z = (count_now - μ) / σ
```

### Ví dụ cụ thể

Giả sử hôm nay là 14:23, số bài viết từ 00:00-14:23:
- 7 ngày trước: [10, 12, 15, 18, 20, 22, 25] bài
- Hôm nay: 45 bài

```
Bước 1: Tính μ
μ = (1×10 + 2×12 + 3×15 + 4×18 + 5×20 + 6×22 + 7×25) / 28
μ = (10 + 24 + 45 + 72 + 100 + 132 + 175) / 28
μ = 558 / 28 = 19.93

Bước 2: Tính σ
Variance = [1×(10-19.93)² + 2×(12-19.93)² + ... + 7×(25-19.93)²] / 28
σ = √Variance ≈ 5.8

Bước 3: Tính Z-Score
z = (45 - 19.93) / 5.8 = 4.32
```

### Ngưỡng cảnh báo Z-Score

| Z-Score | Ý nghĩa | Mức độ |
|---------|---------|--------|
| **z > 2** | Tăng mạnh bất thường | 🔴 Cảnh báo tăng đột biến |
| **0 < z ≤ 2** | Tăng nhẹ | 🟡 Bình thường |
| **-2 ≤ z < 0** | Giảm nhẹ | 🟡 Bình thường |
| **z < -2** | Giảm mạnh bất thường | 🔵 Cảnh báo giảm đột ngột |

**Giải thích**:
- Z-Score = 0: Số bài hôm nay bằng trung bình
- Z-Score = 2: Số bài hôm nay cao hơn trung bình 2 độ lệch chuẩn (bất thường)
- Z-Score = -2: Số bài hôm nay thấp hơn trung bình 2 độ lệch chuẩn

---

## 2. Spike (Tốc độ tăng trưởng)

### Mục đích
Đo lường tốc độ thay đổi so với ngày hôm qua.

### Công thức tính

```
Spike = ((count_today - count_yesterday) / count_yesterday) × 100%

Trong đó:
- count_today: Số bài viết hôm nay (cùng khung giờ)
- count_yesterday: Số bài viết hôm qua (cùng khung giờ)
```

### Trường hợp đặc biệt

```python
if count_yesterday > 0:
    spike = ((count_today - count_yesterday) / count_yesterday) × 100
else:
    # Hôm qua không có bài
    if count_today > 0:
        spike = 100.0  # Tăng 100%
    else:
        spike = 0.0    # Không thay đổi
```

### Ví dụ cụ thể

**Ví dụ 1**: Tăng mạnh
```
Hôm qua (00:00-14:23): 20 bài
Hôm nay (00:00-14:23): 45 bài

Spike = ((45 - 20) / 20) × 100 = 125%
→ Tăng 125% so với hôm qua
```

**Ví dụ 2**: Giảm
```
Hôm qua: 50 bài
Hôm nay: 30 bài

Spike = ((30 - 50) / 50) × 100 = -40%
→ Giảm 40% so với hôm qua
```

**Ví dụ 3**: Hôm qua không có bài
```
Hôm qua: 0 bài
Hôm nay: 10 bài

Spike = 100%
→ Tăng đột biến từ 0
```

### Ý nghĩa

| Spike | Ý nghĩa |
|-------|---------|
| **Spike > 100%** | Tăng gấp đôi hoặc hơn |
| **50% < Spike ≤ 100%** | Tăng mạnh |
| **0% < Spike ≤ 50%** | Tăng nhẹ |
| **Spike = 0%** | Không đổi |
| **-50% < Spike < 0%** | Giảm nhẹ |
| **Spike ≤ -50%** | Giảm mạnh |

**Lưu ý**: Spike không có ngưỡng cảnh báo cố định, chỉ dùng để tham khảo tốc độ thay đổi.

---

## 3. Crisis Score (Điểm khủng hoảng)

### Mục đích
Kết hợp Z-Score và tỷ lệ cảm xúc tiêu cực để phát hiện các chủ đề đang có khủng hoảng.

### Công thức tính

```
Crisis Score = Z-Score × Negative_Ratio

Trong đó:
- Z-Score: Điểm chuẩn hóa (tính ở trên)
- Negative_Ratio: Tỷ lệ bài viết có cảm xúc tiêu cực (0.0 - 1.0)
```

### Chi tiết tính toán

#### Bước 1: Phân tích cảm xúc hôm nay
Lấy tất cả bài viết hôm nay (00:00 → hiện tại) và phân loại cảm xúc:
- **Positive (POS)**: Tích cực
- **Negative (NEG)**: Tiêu cực
- **Neutral (NEU)**: Trung lập
- **Unknown**: Không xác định → Tính là Neutral

```python
# Ví dụ kết quả
sentiment_distribution = {
    "positive": {"count": 10, "percentage": 20.0},
    "negative": {"count": 30, "percentage": 60.0},
    "neutral": {"count": 10, "percentage": 20.0}
}
```

#### Bước 2: Tính Negative Ratio
```
Negative_Ratio = Negative_Percentage / 100

Ví dụ: 60% → 0.6
```

#### Bước 3: Tính Crisis Score
```
Crisis Score = Z-Score × Negative_Ratio
```

### Ví dụ cụ thể

**Ví dụ 1**: Khủng hoảng nghiêm trọng
```
Z-Score = 4.5 (tăng rất mạnh)
Negative = 70% → Negative_Ratio = 0.7

Crisis Score = 4.5 × 0.7 = 3.15
→ Nghiêm trọng (≥2.5)
```

**Ví dụ 2**: Tăng mạnh nhưng cảm xúc tích cực
```
Z-Score = 4.5 (tăng rất mạnh)
Negative = 10% → Negative_Ratio = 0.1

Crisis Score = 4.5 × 0.1 = 0.45
→ Bình thường (<0.8)
```

**Ví dụ 3**: Cảm xúc tiêu cực nhưng không tăng đột biến
```
Z-Score = 1.2 (tăng nhẹ)
Negative = 80% → Negative_Ratio = 0.8

Crisis Score = 1.2 × 0.8 = 0.96
→ Mới nổi (≥0.8)
```

### Ngưỡng cảnh báo Crisis Score

| Crisis Score | Mức độ | Màu sắc | Hành động |
|--------------|--------|---------|-----------|
| **≥ 2.5** | 🔴 Nghiêm trọng (Severe) | Đỏ | Cực kỳ nguy hiểm |
| **≥ 1.8** | 🟠 Cảnh báo cao (High Alert) | Cam | **Cảnh báo ngay lập tức qua WebSocket** |
| **≥ 1.5** | � Cảnh báo (Warning) | Vàng | Theo dõi sát |
| **≥ 0.8** | � Mới nổi (Emerging) | Xanh nhạt | Chú ý |
| **< 0.8** | ⚪ Bình thường (Normal) | Xám | Không cần hành động |

### Điều kiện kích hoạt cảnh báo

Hệ thống chỉ **push cảnh báo qua WebSocket** khi:
```
Crisis Score ≥ 1.8 (Cảnh báo cao)
```

**Lý do**: Ngưỡng 1.8 đảm bảo phát hiện sớm các tình huống nghiêm trọng mà vẫn tránh spam cảnh báo.

---

## 4. Luồng xử lý trong hệ thống

### 4.1. Tính toán điểm (REST API)

**Endpoint**: `GET /api/topics/{topic_id}`

**Quy trình**:
1. Lấy số bài viết hôm nay (00:00 → hiện tại)
2. Lấy số bài viết 7 ngày trước (cùng khung giờ)
3. Tính Z-Score với weighted mean/std
4. Tính Spike so với hôm qua
5. Phân tích cảm xúc hôm nay
6. Tính Crisis Score = Z-Score × Negative_Ratio
7. Trả về kết quả

**Response format**:
```json
{
  "trend_analysis": {
    "count_now": 45,
    "weighted_mean": 19.93,
    "weighted_std": 5.8,
    "z_score": 4.32,
    "spike": 125.0
  },
  "sentiment_today": {
    "total_articles": 50,
    "distribution": {
      "positive": {"count": 10, "percentage": 20.0},
      "negative": {"count": 30, "percentage": 60.0},
      "neutral": {"count": 10, "percentage": 20.0}
    },
    "crisis_score": 3.02
  }
}
```

### 4.2. Cảnh báo khủng hoảng (Scoring Service)

**File**: `services/scoring_24h_service/app.py`

**Quy trình**:
1. Mỗi 50 tin nhắn Kafka, gọi hàm `check_and_push_crisis_alerts()`
2. Lấy top 20 chủ đề từ Redis
3. Với mỗi chủ đề, gọi REST API để lấy Crisis Score
4. Nếu Crisis Score ≥ 2.5:
   - Tạo alert object
   - Push qua WebSocket `/ws-push/crisis`
5. Frontend nhận alert và hiển thị trong `CrisisAlertBox`

**Alert format**:
```json
{
  "topic_id": 176,
  "topic_name": "Dịch bệnh COVID-19",
  "crisis_score": 3.15,
  "z_score": 4.5,
  "negative_percentage": 70.0,
  "count_now": 45,
  "timestamp": 1234567890
}
```

---

## 5. Timezone và thời gian

### Múi giờ sử dụng
- **Database**: UTC (Coordinated Universal Time)
- **Tính toán**: Asia/Ho_Chi_Minh (UTC+7)
- **Hiển thị**: Asia/Ho_Chi_Minh (UTC+7)

### Quy tắc chuyển đổi
```python
import pytz
from datetime import datetime

vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
now_vn = datetime.now(vn_tz)  # Giờ Việt Nam

# Chuyển sang UTC để query database
now_utc = now_vn.astimezone(pytz.UTC)
```

### Khung thời gian

| Mục đích | Khung giờ | Lý do |
|----------|-----------|-------|
| **Tính Z-Score** | 00:00 → Hiện tại | So sánh công bằng cùng khung giờ |
| **Hiển thị biểu đồ** | 00:00 → 23:59 | Hiển thị full ngày cho dễ nhìn |
| **Phân tích cảm xúc** | 00:00 → Hiện tại | Cảm xúc của bài viết hôm nay |

---

## 6. Ví dụ tổng hợp

### Tình huống: Dịch bệnh bùng phát

**Dữ liệu**:
- 7 ngày trước (00:00-14:23): [5, 6, 8, 10, 12, 15, 18] bài
- Hôm nay (00:00-14:23): 85 bài
- Cảm xúc hôm nay: 75% tiêu cực, 15% tích cực, 10% trung lập

**Tính toán**:

1. **Z-Score**:
```
μ = (1×5 + 2×6 + 3×8 + 4×10 + 5×12 + 6×15 + 7×18) / 28
μ = 336 / 28 = 12.0

σ ≈ 4.5

z = (85 - 12.0) / 4.5 = 16.22
→ Tăng cực kỳ bất thường!
```

2. **Spike**:
```
Hôm qua: 18 bài
Hôm nay: 85 bài

Spike = ((85 - 18) / 18) × 100 = 372%
→ Tăng gần 4 lần!
```

3. **Crisis Score**:
```
Negative_Ratio = 75% / 100 = 0.75

Crisis Score = 16.22 × 0.75 = 12.17
→ Cực kỳ nghiêm trọng!
```

**Kết quả**:
- ✅ Kích hoạt cảnh báo nghiêm trọng (≥2.5)
- ✅ Push alert qua WebSocket
- ✅ Hiển thị badge đỏ trên frontend
- ✅ Yêu cầu xử lý ngay lập tức

---

## 7. Câu hỏi thường gặp (FAQ)

### Q1: Tại sao dùng weighted mean thay vì mean thông thường?
**A**: Ngày gần đây có xu hướng quan trọng hơn. Nếu 6 ngày trước có 5 bài/ngày nhưng hôm qua có 50 bài, thì trung bình nên gần 50 hơn là 5.

### Q2: Tại sao min std = 0.5?
**A**: Tránh chia cho 0 khi dữ liệu ổn định (ví dụ: 7 ngày đều có 10 bài). Nếu std = 0, Z-Score sẽ là infinity.

### Q3: Tại sao Crisis Score = Z-Score × Negative_Ratio?
**A**: Vì:
- Z-Score cao + Negative cao = Khủng hoảng thực sự
- Z-Score cao + Negative thấp = Tin tốt đang lan truyền (không phải khủng hoảng)
- Z-Score thấp + Negative cao = Chưa đủ lớn để cảnh báo

### Q4: Tại sao chỉ cảnh báo khi Crisis Score ≥ 1.8?
**A**: Tránh spam cảnh báo nhưng vẫn phát hiện sớm. Ngưỡng 1.8 đảm bảo cảnh báo khi:
- Số bài tăng mạnh (Z-Score cao)
- VÀ cảm xúc tiêu cực chiếm tỷ lệ đáng kể

### Q5: Làm sao biết Z-Score = 2 là "bất thường"?
**A**: Theo quy tắc 68-95-99.7 (empirical rule):
- 68% dữ liệu nằm trong [-1, 1]
- 95% dữ liệu nằm trong [-2, 2]
- 99.7% dữ liệu nằm trong [-3, 3]

→ Z-Score > 2 nghĩa là nằm ngoài 95% dữ liệu bình thường = bất thường!

---

## 8. Tham khảo code

### File chính
- **Tính toán điểm**: `webservices/rest_service/topic_endpoint.py`
- **Cảnh báo khủng hoảng**: `services/scoring_24h_service/app.py`
- **Hiển thị frontend**: `fe_service/src/pages/TopicPage.tsx`
- **Alert box**: `fe_service/src/components/CrisisAlertBox.tsx`

### Dependencies
- `pytz`: Xử lý timezone
- `psycopg2`: Kết nối PostgreSQL
- `redis`: Lưu trữ điểm real-time

---

**Cập nhật lần cuối**: 2024
**Phiên bản**: 1.0
