#!/usr/bin/env python3
"""
Kafka Producer for Sensor Data

Generates random sensor readings and publishes them to Kafka topic.
Supports both JSON and Avro serialization.
"""

import json
import time
import random
import argparse
import logging
import math
from datetime import datetime
from typing import Dict, Any
from kafka import KafkaProducer
from kafka.errors import KafkaError
import avro.io
import avro.schema
import io


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SensorDataProducer:
    """Produces sensor data to Kafka topic."""
    
    def __init__(self, bootstrap_servers: str, topic: str, format: str = 'json'):
        self.topic = topic
        self.format = format
        
        # Configure producer based on format
        if format == 'json':
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
        elif format == 'avro':
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=self._avro_serializer,
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            # Load Avro schema
            with open('../avro/raw_reading.avsc', 'r') as f:
                self.avro_schema = avro.schema.parse(f.read())
        else:
            raise ValueError(f"Unsupported format: {format}")
            
        logger.info(f"Producer initialized for {bootstrap_servers}, topic: {topic}, format: {format}")
    
    def _avro_serializer(self, data: Dict[str, Any]) -> bytes:
        """Serialize data using Avro schema."""
        writer = avro.io.DatumWriter(self.avro_schema)
        bytes_writer = io.BytesIO()
        encoder = avro.io.BinaryEncoder(bytes_writer)
        writer.write(data, encoder)
        return bytes_writer.getvalue()
    
    def generate_reading(self, sensor_id: str) -> Dict[str, Any]:
        """Generate a random sensor reading."""
        # Simulate temperature sensor with some noise
        base_temp = 20.0 + (hash(sensor_id) % 10)  # Different base for each sensor
        noise = random.gauss(0, 2)  # Random noise
        value = base_temp + noise + 5 * math.sin(time.time() / 100)  # Time-based variation
        
        return {
            'sensor_id': sensor_id,
            'timestamp': int(time.time() * 1000),  # Milliseconds since epoch
            'value': round(value, 2)
        }
    
    def produce_readings(self, sensor_ids: list, duration: int, rate: float):
        """
        Produce sensor readings for specified duration.
        
        Args:
            sensor_ids: List of sensor IDs to simulate
            duration: Duration in seconds to produce data
            rate: Readings per second per sensor
        """
        start_time = time.time()
        total_sent = 0
        total_errors = 0
        
        logger.info(f"Starting production for {len(sensor_ids)} sensors at {rate} readings/sec each")
        
        try:
            while time.time() - start_time < duration:
                for sensor_id in sensor_ids:
                    reading = self.generate_reading(sensor_id)
                    
                    try:
                        future = self.producer.send(
                            self.topic,
                            key=sensor_id,
                            value=reading
                        )
                        # Wait for send to complete
                        future.get(timeout=10)
                        total_sent += 1
                        
                        if total_sent % 100 == 0:
                            logger.info(f"Sent {total_sent} readings")
                            
                    except KafkaError as e:
                        logger.error(f"Failed to send reading: {e}")
                        total_errors += 1
                
                # Sleep to maintain desired rate
                time.sleep(1.0 / rate)
                
        except KeyboardInterrupt:
            logger.info("Production interrupted by user")
        finally:
            # Flush remaining messages
            self.producer.flush()
            self.producer.close()
            
            elapsed = time.time() - start_time
            logger.info(f"Production completed:")
            logger.info(f"  Duration: {elapsed:.2f} seconds")
            logger.info(f"  Total sent: {total_sent}")
            logger.info(f"  Total errors: {total_errors}")
            logger.info(f"  Effective rate: {total_sent/elapsed:.2f} messages/sec")


def main():
    parser = argparse.ArgumentParser(description='Produce sensor data to Kafka')
    parser.add_argument('--bootstrap-servers', default='localhost:9092',
                        help='Kafka bootstrap servers')
    parser.add_argument('--topic', default='raw_readings',
                        help='Kafka topic to produce to')
    parser.add_argument('--sensors', type=int, default=10,
                        help='Number of sensors to simulate')
    parser.add_argument('--duration', type=int, default=300,
                        help='Duration to produce data in seconds')
    parser.add_argument('--rate', type=float, default=1.0,
                        help='Readings per second per sensor')
    parser.add_argument('--format', choices=['json', 'avro'], default='json',
                        help='Message format')
    
    args = parser.parse_args()
    
    # Generate sensor IDs
    sensor_ids = [f"sensor_{i:03d}" for i in range(args.sensors)]
    
    # Create and run producer
    producer = SensorDataProducer(
        args.bootstrap_servers,
        args.topic,
        args.format
    )
    
    producer.produce_readings(sensor_ids, args.duration, args.rate)


if __name__ == '__main__':
    main()