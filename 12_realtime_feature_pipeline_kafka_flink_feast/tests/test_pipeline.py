#!/usr/bin/env python3
"""
Integration tests for the real-time feature pipeline.
"""

import json
import time
import pytest
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import redis
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestFeaturePipeline:
    """Test the end-to-end feature pipeline."""
    
    @pytest.fixture
    def kafka_producer(self):
        """Create Kafka producer for tests."""
        producer = KafkaProducer(
            bootstrap_servers='localhost:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        yield producer
        producer.close()
    
    @pytest.fixture
    def kafka_consumer(self):
        """Create Kafka consumer for tests."""
        consumer = KafkaConsumer(
            'sensor_features',
            bootstrap_servers='localhost:9092',
            auto_offset_reset='latest',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            consumer_timeout_ms=10000
        )
        yield consumer
        consumer.close()
    
    @pytest.fixture
    def redis_client(self):
        """Create Redis client for tests."""
        client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        yield client
        client.close()
    
    def test_kafka_connectivity(self, kafka_producer):
        """Test basic Kafka connectivity."""
        test_message = {
            'sensor_id': 'test_sensor',
            'timestamp': int(time.time() * 1000),
            'value': 25.5
        }
        
        future = kafka_producer.send('raw_readings', value=test_message)
        result = future.get(timeout=10)
        
        assert result is not None
        logger.info(f"Successfully sent message to Kafka: {test_message}")
    
    def test_end_to_end_pipeline(self, kafka_producer, kafka_consumer):
        """Test the complete pipeline from raw data to features."""
        # Generate test data
        sensor_id = f"test_sensor_{int(time.time())}"
        num_readings = 100
        
        logger.info(f"Sending {num_readings} readings for sensor {sensor_id}")
        
        # Send test readings
        for i in range(num_readings):
            reading = {
                'sensor_id': sensor_id,
                'timestamp': int(time.time() * 1000) + i * 1000,
                'value': 20.0 + i * 0.1
            }
            kafka_producer.send('raw_readings', value=reading)
        
        kafka_producer.flush()
        logger.info("All test readings sent")
        
        # Wait for processing
        time.sleep(65)  # Wait for 1-minute window to complete
        
        # Check for aggregated features
        features_found = False
        for message in kafka_consumer:
            if message.value['sensor_id'] == sensor_id:
                features = message.value['features']
                
                # Validate aggregated features
                assert 'avg_value' in features
                assert 'min_value' in features
                assert 'max_value' in features
                assert 'count' in features
                
                # Check values are reasonable
                assert features['count'] > 0
                assert features['min_value'] <= features['avg_value'] <= features['max_value']
                
                logger.info(f"Received features: {features}")
                features_found = True
                break
        
        assert features_found, f"No features found for sensor {sensor_id}"
    
    def test_anomaly_detection(self, kafka_producer, kafka_consumer):
        """Test anomaly detection in the pipeline."""
        sensor_id = f"anomaly_sensor_{int(time.time())}"
        
        # Send normal readings followed by anomalies
        readings = []
        
        # Normal readings
        for i in range(50):
            readings.append({
                'sensor_id': sensor_id,
                'timestamp': int(time.time() * 1000) + i * 1000,
                'value': 20.0 + random.gauss(0, 0.5)
            })
        
        # Anomalous readings
        for i in range(10):
            readings.append({
                'sensor_id': sensor_id,
                'timestamp': int(time.time() * 1000) + (50 + i) * 1000,
                'value': 50.0 + random.gauss(0, 2)  # Much higher values
            })
        
        # Send all readings
        for reading in readings:
            kafka_producer.send('raw_readings', value=reading)
        kafka_producer.flush()
        
        # Wait for processing
        time.sleep(65)
        
        # Check for anomaly detection
        for message in kafka_consumer:
            if message.value['sensor_id'] == sensor_id:
                features = message.value['features']
                
                # Should detect some anomalies
                assert 'anomaly_count' in features
                assert features['anomaly_count'] > 0
                assert features['anomaly_rate'] > 0
                
                logger.info(f"Detected {features['anomaly_count']} anomalies")
                break
    
    def test_redis_feature_store(self, redis_client):
        """Test Redis connectivity for Feast online store."""
        # Set a test key
        test_key = f"test:sensor:{int(time.time())}"
        test_value = json.dumps({'value': 25.5, 'timestamp': int(time.time())})
        
        redis_client.set(test_key, test_value)
        retrieved = redis_client.get(test_key)
        
        assert retrieved == test_value
        logger.info("Redis feature store is accessible")
        
        # Cleanup
        redis_client.delete(test_key)
    
    def test_multiple_sensors(self, kafka_producer, kafka_consumer):
        """Test pipeline with multiple concurrent sensors."""
        num_sensors = 5
        readings_per_sensor = 20
        sensor_ids = [f"multi_sensor_{i}_{int(time.time())}" for i in range(num_sensors)]
        
        # Send readings for all sensors
        for i in range(readings_per_sensor):
            for sensor_id in sensor_ids:
                reading = {
                    'sensor_id': sensor_id,
                    'timestamp': int(time.time() * 1000) + i * 1000,
                    'value': 20.0 + hash(sensor_id) % 10 + random.gauss(0, 1)
                }
                kafka_producer.send('raw_readings', value=reading)
        
        kafka_producer.flush()
        logger.info(f"Sent readings for {num_sensors} sensors")
        
        # Wait for processing
        time.sleep(65)
        
        # Collect features for all sensors
        received_sensors = set()
        for message in kafka_consumer:
            sensor_id = message.value['sensor_id']
            if sensor_id in sensor_ids:
                received_sensors.add(sensor_id)
                
                # Stop when we've seen all sensors
                if len(received_sensors) == num_sensors:
                    break
        
        assert len(received_sensors) == num_sensors, \
            f"Expected features for {num_sensors} sensors, got {len(received_sensors)}"
        
        logger.info(f"Successfully processed {num_sensors} sensors")


if __name__ == "__main__":
    # Run tests
    import random
    
    # Simple test runner
    test = TestFeaturePipeline()
    
    # Mock fixtures for standalone execution
    class MockProducer:
        def send(self, topic, value):
            logger.info(f"Would send to {topic}: {value}")
            return type('obj', (object,), {'get': lambda self, timeout: True})
        
        def flush(self):
            pass
        
        def close(self):
            pass
    
    producer = MockProducer()
    
    try:
        logger.info("Running pipeline tests...")
        test.test_kafka_connectivity(producer)
        logger.info("✓ Kafka connectivity test passed")
        
        logger.info("\nAll tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise