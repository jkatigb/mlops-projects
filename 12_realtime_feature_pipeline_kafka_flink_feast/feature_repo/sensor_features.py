from datetime import timedelta
from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float32, Int64

sensor = Entity(name="sensor_id", join_keys=["sensor_id"])

source = FileSource(
    path="data/offline.parquet",
    timestamp_field="event_timestamp",
)

sensor_features_view = FeatureView(
    name="sensor_features",
    entities=[sensor],
    ttl=timedelta(days=1),
    schema=[
        Field(name="avg_value", dtype=Float32),
    ],
    online=True,
    source=source,
)
