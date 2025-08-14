
FROM python:3.10-slim-bullseye

# Cập nhật, cài curl/wget để test HTTP, ca-certificates để xử lý HTTPS
RUN apt-get update && apt-get install -y \
    gcc \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy file requirements trước để tận dụng cache
COPY requirements.txt .

# Cài thư viện Python
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ project
COPY . .
# Set biến môi trường để Python không tạo __pycache__
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Mặc định chạy file app.py
CMD ["python", "app.py"]
