
FROM python:3.10-slim-bullseye

# Cập nhật, cài curl/wget để test HTTP, ca-certificates để xử lý HTTPS
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy file requirements trước để tận dụng cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ project
COPY . .

# Mặc định chạy file app.py
CMD ["python", "app.py"]
