#!/bin/bash
# Test script for real-time feature pipeline

set -e

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check if services are running
check_services() {
    log_info "Checking if services are running..."
    
    # Check Docker Compose services
    if ! docker compose ps | grep -q "Up"; then
        log_error "Docker services are not running. Start with: docker compose up -d"
        exit 1
    fi
    
    # Check Kafka
    if ! docker compose exec -T kafka kafka-broker-api-versions --bootstrap-server kafka:9093 >/dev/null 2>&1; then
        log_error "Kafka is not responding"
        exit 1
    fi
    log_info "✓ Kafka is running"
    
    # Check Flink
    if ! curl -s http://localhost:8081/overview >/dev/null; then
        log_error "Flink JobManager is not responding"
        exit 1
    fi
    log_info "✓ Flink is running"
    
    # Check Redis
    if ! docker compose exec -T redis redis-cli ping >/dev/null 2>&1; then
        log_error "Redis is not responding"
        exit 1
    fi
    log_info "✓ Redis is running"
}

# Create Kafka topics
create_topics() {
    log_info "Creating Kafka topics..."
    
    docker compose exec -T kafka kafka-topics \
        --create --if-not-exists \
        --topic raw_readings \
        --bootstrap-server kafka:9093 \
        --replication-factor 1 \
        --partitions 3
    
    docker compose exec -T kafka kafka-topics \
        --create --if-not-exists \
        --topic sensor_features \
        --bootstrap-server kafka:9093 \
        --replication-factor 1 \
        --partitions 3
    
    log_info "✓ Topics created"
}

# Submit Flink job
submit_flink_job() {
    log_info "Submitting Flink job..."
    
    # First, install Python dependencies in Flink container
    docker compose exec -T flink-jobmanager pip install \
        apache-flink \
        kafka-python \
        redis \
        feast
    
    # Submit the job
    docker compose exec -T flink-jobmanager python /opt/flink/jobs/sensor_aggregation.py &
    FLINK_PID=$!
    
    sleep 5
    
    # Check if job is running
    if curl -s http://localhost:8081/jobs | grep -q "RUNNING"; then
        log_info "✓ Flink job submitted successfully"
    else
        log_error "Flink job failed to start"
        exit 1
    fi
}

# Run producer test
test_producer() {
    log_info "Testing Kafka producer..."
    
    # Run producer for 30 seconds
    docker compose exec -T kafka python3 - << 'EOF'
import sys
sys.path.append('/opt/flink/jobs')
from ingestion.kafka_producer import SensorDataProducer

producer = SensorDataProducer('kafka:9093', 'raw_readings')
producer.produce_readings(['test_sensor_001', 'test_sensor_002'], 30, 2.0)
EOF
    
    log_info "✓ Producer test completed"
}

# Check for output
check_output() {
    log_info "Checking for processed features..."
    
    # Consume from features topic
    timeout 30 docker compose exec -T kafka kafka-console-consumer \
        --bootstrap-server kafka:9093 \
        --topic sensor_features \
        --from-beginning \
        --max-messages 5 \
        --timeout-ms 30000
    
    if [ $? -eq 0 ]; then
        log_info "✓ Feature processing verified"
    else
        log_warning "No features received within timeout"
    fi
}

# Check monitoring
check_monitoring() {
    log_info "Checking monitoring endpoints..."
    
    # Check Prometheus
    if curl -s http://localhost:9090/-/healthy >/dev/null; then
        log_info "✓ Prometheus is healthy"
    else
        log_warning "Prometheus is not responding"
    fi
    
    # Check Grafana
    if curl -s http://localhost:3000/api/health >/dev/null; then
        log_info "✓ Grafana is healthy"
    else
        log_warning "Grafana is not responding"
    fi
    
    # Check Kafka UI
    if curl -s http://localhost:8090/api/clusters >/dev/null; then
        log_info "✓ Kafka UI is accessible"
    else
        log_warning "Kafka UI is not responding"
    fi
}

# Main test flow
main() {
    log_info "Starting pipeline test..."
    
    check_services
    create_topics
    submit_flink_job
    test_producer
    check_output
    check_monitoring
    
    log_info "Pipeline test completed successfully!"
    log_info ""
    log_info "Access points:"
    log_info "  - Flink UI: http://localhost:8081"
    log_info "  - Kafka UI: http://localhost:8090"
    log_info "  - Prometheus: http://localhost:9090"
    log_info "  - Grafana: http://localhost:3000 (admin/admin)"
}

# Run main function
main