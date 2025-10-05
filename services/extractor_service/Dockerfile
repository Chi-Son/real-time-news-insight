FROM python:3.10-slim-bullseye

# -----------------------
# Cài các gói cần thiết
# -----------------------
RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg fonts-liberation libnss3 libxss1 libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libpango1.0-0 libpangocairo-1.0-0 libgtk-3-0 \
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# -----------------------
# Thiết lập thư mục làm việc
# -----------------------
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ project
COPY . .

# Biến môi trường cho Selenium dùng Chromium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_DRIVER=/usr/bin/chromedriver

# CMD mặc định
CMD ["python", "app.py"]
