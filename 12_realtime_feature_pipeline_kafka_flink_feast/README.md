# Real-Time Feature Pipeline with Kafka + Flink + Feast

## Overview
Streams raw sensor data through Kafka → Flink enrichment → Feast online store (Redis) for sub-10 ms feature retrieval during inference. Docker-compose enables local reproduction; Helm charts cover production deploy.

## Why it matters
Many organisations rely on nightly batch features, blocking real-time ML products. This PoC shows how to upgrade to low-latency, fresh features without a huge platform rewrite.

## Tech Stack
* Apache Kafka & Kafka Connect
* Apache Flink job (Scala/Java or PyFlink)
* Feast online store (Redis) & offline store (S3)
* Docker-compose for local, Helm for k8s
* Sample inference notebook

## Task Checklist
- [ ] Docker-compose: `zookeeper`, `kafka`, `redis`, `feast-core`, `feast-online`  
- [ ] Kafka topic `raw_readings` + Avro schema  
- [ ] Flink job: parse → calculate rolling stats → write to Feast online  
- [ ] Feast repo with entity & feature view definitions  
- [ ] Ingestion pipeline to backfill offline store (Spark or pandas)  
- [ ] Notebook: query online store and run toy model  
- [ ] Helm chart with values for prod cluster  
- [ ] Grafana panel: ingestion lag & Redis latency  

## Demo
```bash
make compose-up
python scripts/produce_sensor_stream.py
# open notebook Inference.ipynb
```

---
*Status*: design 