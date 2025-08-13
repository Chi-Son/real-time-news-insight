#!/bin/bash
set -e

# Thay path này bằng path bạn cấu hình log.dirs trong server.properties
KAFKA_DATA_DIR="${KAFKA_DATA_DIR:-/var/lib/kafka/data}"
META_FILE="$KAFKA_DATA_DIR/meta.properties"

# Tạo thư mục nếu chưa có (giúp cho bind-mount mới)
mkdir -p "$KAFKA_DATA_DIR"
chown -R kafka:kafka "$KAFKA_DATA_DIR" 2>/dev/null || true

if [ ! -f "$META_FILE" ]; then
  echo "[entrypoint] Kafka storage not formatted. Running kafka-storage.sh format..."
  /opt/kafka/bin/kafka-storage.sh format -t realtime-cluster -c /opt/kafka/config/kraft/server.properties
else
  echo "[entrypoint] Kafka storage already formatted, skipping format."
fi

echo "[entrypoint] Starting Kafka broker..."
exec /opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/kraft/server.properties
