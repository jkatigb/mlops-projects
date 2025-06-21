# Real-time Feature Pipeline with Kafka, Flink, and Feast

A production-ready demonstration of building a real-time feature engineering pipeline for ML applications, showcasing streaming data processing, feature computation, and feature serving.

## 🎯 Overview

This project demonstrates a complete real-time feature pipeline that:
- Ingests streaming sensor data via Kafka
- Processes data in real-time using Apache Flink
- Computes windowed aggregations and detects anomalies
- Stores features in Feast for ML model serving
- Provides monitoring via Prometheus and Grafana

## 🏗️ Architecture

```
┌─────────────┐     ┌───────────┐     ┌─────────────────┐     ┌─────────────┐
│   Sensors   │────▶│   Kafka   │────▶│     Flink       │────▶│    Feast    │
│  (Producer) │     │  (Broker) │     │  (Processing)   │     │(Feature Store)│
└─────────────┘     └───────────┘     └─────────────────┘     └─────────────┘
                                               │                        │
                                               ▼                        ▼
                                       ┌───────────────┐       ┌────────────┐
                                       │  Prometheus   │       │   Redis    │
                                       │  (Metrics)    │       │  (Online)  │
                                       └───────────────┘       └────────────┘
```

## 📦 Components

### Data Ingestion
- **Kafka Producer**: Simulates IoT sensors generating temperature readings
- **Kafka Topics**: `raw_readings` for raw data, `sensor_features` for processed features

### Stream Processing
- **Flink Job**: Real-time processing with:
  - Windowed aggregations (1-minute tumbling windows)
  - Statistical computations (avg, min, max, std dev)
  - Anomaly detection using z-score method
  - Exactly-once processing guarantees

### Feature Store
- **Feast**: Feature management and serving
- **Redis**: Low-latency online feature store
- **Feature Registry**: Tracks feature definitions and metadata

### Monitoring
- **Prometheus**: Metrics collection from Flink
- **Grafana**: Dashboards for pipeline monitoring
- **Kafka UI**: Visual interface for Kafka management

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.8+
- 8GB RAM minimum

### Setup

1. **Clone and navigate to the project**:
   ```bash
   cd 12_realtime_feature_pipeline_kafka_flink_feast
   ```

2. **Start all services**:
   ```bash
   docker compose up -d
   ```

3. **Wait for services to be healthy**:
   ```bash
   docker compose ps
   ```

4. **Create Kafka topics**:
   ```bash
   ./scripts/create_topics.sh
   ```

5. **Submit Flink job**:
   ```bash
   docker compose exec flink-jobmanager flink run -py /opt/flink/jobs/sensor_aggregation.py
   ```

6. **Start data producer**:
   ```bash
   python ingestion/kafka_producer.py --sensors 10 --duration 300 --rate 1.0
   ```

### Testing

Run the automated test suite:
```bash
./scripts/test_pipeline.sh
```

Or test individual components:
```bash
# Test Kafka connectivity
docker compose exec kafka kafka-topics --list --bootstrap-server kafka:9093

# Test Flink job status
curl http://localhost:8081/jobs

# Test Redis connectivity
docker compose exec redis redis-cli ping
```

## 📊 Feature Engineering

### Computed Features

The pipeline computes the following features in 1-minute windows:

| Feature | Description | Use Case |
|---------|-------------|----------|
| `avg_value` | Average sensor reading | Baseline behavior |
| `min_value` | Minimum reading | Lower bounds detection |
| `max_value` | Maximum reading | Upper bounds detection |
| `std_dev` | Standard deviation | Variability measure |
| `anomaly_count` | Number of anomalies | Alert triggering |
| `anomaly_rate` | Percentage of anomalies | System health |

### Anomaly Detection

Anomalies are detected using the z-score method:
- Maintains running statistics using Welford's algorithm
- Flags readings > 2.5 standard deviations from mean
- Adapts to changing baselines over time

## 🔧 Configuration

### Kafka Producer Options
```bash
python ingestion/kafka_producer.py \
  --bootstrap-servers localhost:9092 \
  --topic raw_readings \
  --sensors 20 \              # Number of sensors
  --duration 600 \            # Runtime in seconds
  --rate 2.0 \               # Readings per second per sensor
  --format json              # Message format (json/avro)
```

### Flink Job Configuration
- Parallelism: 4 (configurable)
- Checkpointing: Every 30 seconds
- State backend: Filesystem
- Window size: 1 minute (tumbling)

### Feast Configuration
Edit `feature_repo/feature_store.yaml`:
```yaml
project: sensor_features
registry: data/registry.db
provider: local
online_store:
  type: redis
  redis_type: redis
  connection_string: redis:6379
```

## 📈 Monitoring

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Flink UI | http://localhost:8081 | - |
| Kafka UI | http://localhost:8090 | - |
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3000 | admin/admin |
| Feast UI | http://localhost:8080 | - |

### Key Metrics

**Flink Metrics**:
- `flink_jobmanager_job_uptime`: Job uptime
- `flink_taskmanager_job_task_numRecordsIn`: Input throughput
- `flink_taskmanager_job_task_numRecordsOut`: Output throughput
- `flink_jobmanager_job_lastCheckpointDuration`: Checkpoint performance

**Kafka Metrics**:
- Messages in/out rate
- Consumer lag
- Partition distribution

## 🧪 Development

### Project Structure
```
.
├── avro/                    # Avro schemas
├── flink/                   # Flink job definitions
│   ├── flink_job.py        # Table API job
│   └── sensor_aggregation.py # DataStream API job
├── feature_repo/           # Feast feature definitions
├── ingestion/              # Data ingestion scripts
├── monitoring/             # Prometheus/Grafana configs
├── scripts/                # Utility scripts
├── tests/                  # Integration tests
├── docker-compose.yml      # Service orchestration
└── requirements.txt        # Python dependencies
```

### Adding New Features

1. **Update Flink job** in `flink/sensor_aggregation.py`:
   ```python
   # Add new computation in WindowAggregator
   new_feature = compute_custom_metric(values)
   ```

2. **Update Feast schema** in `feature_repo/sensor_features.py`:
   ```python
   Field(name="new_feature", dtype=Float32)
   ```

3. **Apply Feast changes**:
   ```bash
   feast apply
   ```

## 🐛 Troubleshooting

### Common Issues

1. **Kafka connection refused**:
   ```bash
   # Check Kafka is running
   docker compose logs kafka
   # Verify listeners configuration
   docker compose exec kafka cat /etc/kafka/server.properties
   ```

2. **Flink job not starting**:
   ```bash
   # Check job manager logs
   docker compose logs flink-jobmanager
   # Verify Python dependencies
   docker compose exec flink-jobmanager pip list
   ```

3. **No features in output**:
   ```bash
   # Check topic content
   docker compose exec kafka kafka-console-consumer \
     --bootstrap-server kafka:9093 \
     --topic sensor_features \
     --from-beginning
   ```

### Performance Tuning

- **Increase Kafka partitions** for higher throughput
- **Adjust Flink parallelism** based on CPU cores
- **Tune window size** based on latency requirements
- **Configure Redis persistence** for durability

## 🔐 Production Considerations

1. **Security**:
   - Enable Kafka SSL/SASL authentication
   - Secure Flink REST API
   - Use Redis AUTH password
   - Network isolation with proper firewalls

2. **Scalability**:
   - Deploy on Kubernetes for auto-scaling
   - Use Kafka partition strategy
   - Distribute Flink across multiple nodes
   - Consider Redis Cluster mode

3. **Reliability**:
   - Configure Kafka replication factor > 1
   - Enable Flink HA mode
   - Set up Redis persistence
   - Implement dead letter queues

4. **Monitoring**:
   - Set up alerting rules in Prometheus
   - Create SLI/SLO dashboards
   - Log aggregation with ELK stack
   - Distributed tracing with Jaeger

## 📚 References

- [Apache Flink Documentation](https://flink.apache.org/)
- [Feast Documentation](https://docs.feast.dev/)
- [Kafka Best Practices](https://kafka.apache.org/documentation/#bestpractices)
- [Streaming Systems Book](http://streamingsystems.net/)

## Files

- `docker-compose.yml` – All services with health checks and monitoring
- `avro/raw_reading.avsc` – Avro schema for sensor readings
- `flink/sensor_aggregation.py` – Enhanced PyFlink job with anomaly detection
- `flink/flink_job.py` – Table API job for Feast integration
- `feature_repo/` – Feast feature definitions
- `ingestion/kafka_producer.py` – Configurable sensor data generator
- `ingestion/offline_ingestion.py` – Batch loader for offline store
- `monitoring/` – Prometheus and Grafana configurations
- `scripts/test_pipeline.sh` – Automated test script
- `tests/test_pipeline.py` – Integration tests
- `requirements.txt` – Python dependencies
- `Dockerfile.feast` – Feast server container