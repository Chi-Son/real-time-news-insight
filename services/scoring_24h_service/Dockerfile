FROM python:3.10-slim-bullseye


RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    librdkafka-dev \
    curl \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app


COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
