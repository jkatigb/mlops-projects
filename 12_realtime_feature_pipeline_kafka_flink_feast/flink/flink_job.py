from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment
from feast import FeatureStore


def main():
    env = StreamExecutionEnvironment.get_execution_environment()
    t_env = StreamTableEnvironment.create(env)

    t_env.execute_sql(
        """
        CREATE TABLE raw_readings (
            sensor_id STRING,
            timestamp BIGINT,
            value DOUBLE,
            WATERMARK FOR timestamp AS TO_TIMESTAMP_LTZ(timestamp, 3)
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'raw_readings',
            'properties.bootstrap.servers' = 'kafka:9092',
            'format' = 'json'
        )
        """
    )

    stmt_set = t_env.create_statement_set()
    result_table = t_env.sql_query(
        """
        SELECT
            sensor_id,
            AVG(value) AS avg_value,
            TUMBLE_END(TO_TIMESTAMP_LTZ(timestamp,3), INTERVAL '1' MINUTE) AS ts
        FROM raw_readings
        GROUP BY
            sensor_id,
            TUMBLE(TO_TIMESTAMP_LTZ(timestamp,3), INTERVAL '1' MINUTE)
        """
    )
    t_env.create_temporary_view("feature_view", result_table)

    store = FeatureStore(repo_path="../feature_repo")

    with t_env.to_pandas(result_table) as pdf:
        if not pdf.empty:
            store.write_to_online_store(
                "sensor_features",
                pdf.rename(columns={"ts": "event_timestamp"})
            )

    env.execute("flink_feature_enrichment")


if __name__ == "__main__":
    main()
