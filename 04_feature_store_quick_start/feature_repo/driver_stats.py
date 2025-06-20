from datetime import timedelta

from feast import Entity, Field, FeatureView, FileSource
from feast.types import Float32, Int64

# Source file for offline features
driver_stats_source = FileSource(
    path="data/driver_stats.csv",
    event_timestamp_column="event_timestamp",
    timestamp_format="%Y-%m-%dT%H:%M:%SZ",
)

# Entity definition
driver = Entity(name="driver_id", join_key="driver_id", value_type=Int64)

# Feature view mapping offline file to online store
driver_stats_view = FeatureView(
    name="driver_stats",
    entities=["driver_id"],
    ttl=timedelta(days=1),
    schema=[
        Field(name="conv_rate", dtype=Float32),
        Field(name="acc_rate", dtype=Float32),
        Field(name="avg_daily_trips", dtype=Int64),
    ],
    online=True,
    batch_source=driver_stats_source,
)
