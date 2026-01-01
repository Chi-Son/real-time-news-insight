FROM python:3.10-slim-bullseye

# Cài các gói cần thiết để build fastText và kết nối DB
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    wget \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements và cài dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ project
COPY . .

# 🚀 CHẠY FASTAPI BẰNG UVICORN 
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]


