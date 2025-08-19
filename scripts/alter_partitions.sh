#!/bin/bash

TOPIC_NAME=$1
PARTITIONS=$2

if [ -z "$TOPIC_NAME" ] || [ -z "$PARTITIONS" ]; then
  echo "Usage: ./alter_partitions.sh <topic_name> <num_partitions>"
  exit 1
fi

docker exec -i realtimenews_kafka kafka-topics.sh \
  --alter \
  --topic "$TOPIC_NAME" \
  --partitions "$PARTITIONS" \
  --bootstrap-server kafka:9092