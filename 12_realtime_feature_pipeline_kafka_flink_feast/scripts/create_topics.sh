#!/bin/bash
# Creates Kafka topic for raw sensor readings
set -e

KAFKA_CONTAINER=${1:-kafka}

docker compose exec $KAFKA_CONTAINER kafka-topics \
  --create --if-not-exists \
  --topic raw_readings \
  --bootstrap-server localhost:9092 \
  --replication-factor 1 \
  --partitions 1

