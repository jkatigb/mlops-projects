# Real-Time Feature Pipeline with Kafka + Flink + Feast

This demo streams raw sensor readings through Kafka, enriches them with a PyFlink job and publishes features to a Feast online store backed by Redis.  A minimal ingestion pipeline loads historical data into the offline store and a sample notebook demonstrates feature retrieval at inference time.  Helm charts are provided for deploying the Flink job in production and Grafana dashboards monitor ingestion lag and Redis latency.

## Usage

```bash
# start all services
docker compose up -d

# create Kafka topics
./scripts/create_topics.sh

# run the Flink enrichment job (local)
python flink/flink_job.py
```

Open `notebooks/Inference.ipynb` to query features from the online store.

## Contents
- `docker-compose.yml` – Zookeeper, Kafka, Redis, Feast and Flink services
- `avro/raw_reading.avsc` – Avro schema for the `raw_readings` topic
- `flink/flink_job.py` – PyFlink job that computes rolling averages and writes to Feast
- `feature_repo/` – Feast repository with feature definitions
- `ingestion/offline_ingestion.py` – batch loader for offline store
- `helm/` – example Helm chart for deploying the Flink job
- `grafana/dashboard.json` – Grafana panels for ingestion lag and Redis latency
