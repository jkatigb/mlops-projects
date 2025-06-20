import os
from datetime import datetime

import pandas as pd
from feast import FeatureStore

from driver_stats import driver, driver_stats_view


def main():
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    store = FeatureStore(repo_path=repo_dir)

    # Register feature definitions
    store.apply([driver, driver_stats_view])

    # Load and write historical features to offline store
    csv_path = os.path.join(repo_dir, "data", "driver_stats.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    df = pd.read_csv(csv_path)
    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"])
    store.write_to_offline_store(driver_stats_view, df)

    # Materialize latest state to online store
    store.materialize_incremental(end_date=datetime.utcnow())
    print("Ingestion complete")


if __name__ == "__main__":
    main()
