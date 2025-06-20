"""Load historical sensor data into Feast offline store."""
import pandas as pd
from feast import FeatureStore

store = FeatureStore(repo_path="../feature_repo")

# Expect data/offline.csv with columns: sensor_id, event_timestamp, avg_value
source_df = pd.read_csv("data/offline.csv", parse_dates=["event_timestamp"])

store.apply([
    store.get_entity("sensor_id"),
    store.get_feature_view("sensor_features"),
])

store.ingest(
    feature_view_name="sensor_features",
    source_df=source_df,
)
