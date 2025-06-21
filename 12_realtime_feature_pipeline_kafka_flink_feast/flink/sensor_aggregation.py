#!/usr/bin/env python3
"""
Enhanced Flink Job for Real-time Feature Processing

This job consumes sensor data from Kafka, performs windowed aggregations,
detects anomalies, and writes features to both Kafka and Feast feature store.
"""

import json
import logging
from datetime import datetime
from typing import Iterator

from pyflink.common import Duration, WatermarkStrategy
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.typeinfo import Types
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import (
    KafkaOffsetsInitializer,
    KafkaRecordSerializationSchema,
    KafkaSink,
    KafkaSource,
)
from pyflink.datastream.functions import ProcessWindowFunction, RuntimeContext
from pyflink.datastream.state import ValueStateDescriptor
from pyflink.datastream.window import TumblingEventTimeWindows
from pyflink.table import StreamTableEnvironment

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SensorDataProcessor:
    """Process sensor data with aggregations and anomaly detection."""
    
    @staticmethod
    def parse_json(value: str) -> Iterator[dict]:
        """Parse JSON with error handling."""
        try:
            data = json.loads(value)
            if all(k in data for k in ['sensor_id', 'timestamp', 'value']):
                yield data
            else:
                logger.warning(f"Missing required fields: {value}")
        except Exception as e:
            logger.error(f"Parse error: {e}")
    
    @staticmethod
    def compute_features(elements: list) -> dict:
        """Compute statistical features from sensor readings."""
        if not elements:
            return {}
            
        values = [e['value'] for e in elements]
        
        # Basic statistics
        avg_val = sum(values) / len(values)
        min_val = min(values)
        max_val = max(values)
        
        # Standard deviation
        variance = sum((x - avg_val) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        # Detect anomalies (values > 2.5 std devs)
        anomalies = [v for v in values if abs(v - avg_val) > 2.5 * std_dev]
        
        return {
            'avg_value': round(avg_val, 2),
            'min_value': round(min_val, 2),
            'max_value': round(max_val, 2),
            'std_dev': round(std_dev, 2),
            'count': len(values),
            'anomaly_count': len(anomalies),
            'anomaly_rate': round(len(anomalies) / len(values), 3) if values else 0
        }


class WindowAggregator(ProcessWindowFunction):
    """Aggregate sensor data over time windows."""
    
    def process(self, key: str, context: ProcessWindowFunction.Context, 
                elements: Iterator[dict]) -> Iterator[str]:
        """Process window and yield aggregated features."""
        readings = list(elements)
        
        if not readings:
            return
            
        features = SensorDataProcessor.compute_features(readings)
        
        result = {
            'sensor_id': key,
            'window_start': context.window().start,
            'window_end': context.window().end,
            'event_time': datetime.fromtimestamp(context.window().end / 1000).isoformat(),
            'features': features
        }
        
        logger.info(f"Processed window for {key}: {features}")
        yield json.dumps(result)


def create_flink_job():
    """Create and configure the Flink streaming job."""
    # Environment setup
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(2)
    
    # Enable checkpointing
    env.enable_checkpointing(30000)  # 30 seconds
    
    # Kafka configuration
    KAFKA_SERVERS = "kafka:9092"
    INPUT_TOPIC = "raw_readings"
    OUTPUT_TOPIC = "sensor_features"
    
    # Create Kafka source
    kafka_source = KafkaSource.builder() \
        .set_bootstrap_servers(KAFKA_SERVERS) \
        .set_topics(INPUT_TOPIC) \
        .set_group_id("sensor-feature-processor") \
        .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
        .set_value_only_deserializer(SimpleStringSchema()) \
        .build()
    
    # Create stream with watermarks
    raw_stream = env.from_source(
        kafka_source,
        WatermarkStrategy.for_bounded_out_of_orderness(Duration.of_seconds(5))
            .with_timestamp_assigner(lambda x: json.loads(x).get('timestamp', 0)),
        "Kafka Source"
    )
    
    # Process pipeline
    feature_stream = raw_stream \
        .flat_map(SensorDataProcessor.parse_json) \
        .key_by(lambda x: x['sensor_id']) \
        .window(TumblingEventTimeWindows.of(Duration.of_minutes(1))) \
        .process(WindowAggregator())
    
    # Create Kafka sink
    kafka_sink = KafkaSink.builder() \
        .set_bootstrap_servers(KAFKA_SERVERS) \
        .set_record_serializer(
            KafkaRecordSerializationSchema.builder()
            .set_topic(OUTPUT_TOPIC)
            .set_value_serialization_schema(SimpleStringSchema())
            .build()
        ) \
        .set_delivery_guarantee(KafkaSink.DeliveryGuarantee.AT_LEAST_ONCE) \
        .build()
    
    # Write to Kafka
    feature_stream.sink_to(kafka_sink).name("Feature Sink")
    
    # Also print for debugging
    feature_stream.print().name("Debug Output")
    
    return env


def main():
    """Main entry point."""
    logger.info("Starting Sensor Feature Processing Job")
    
    try:
        env = create_flink_job()
        env.execute("Sensor Feature Processing")
    except Exception as e:
        logger.error(f"Job failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()