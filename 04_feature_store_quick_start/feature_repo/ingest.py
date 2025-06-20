from datetime import datetime

import pandas as pd
from feast import FeatureStore

from driver_stats import driver, driver_stats_view


def main():
    store = FeatureStore(repo_path=".")

    # Register feature definitions
    store.apply([driver, driver_stats_view])

    # Load and write historical features to offline store
    df = pd.read_csv("data/driver_stats.csv")
    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"])
    store.write_to_offline_store(driver_stats_view, df)

    # Materialize latest state to online store
    store.materialize_incremental(end_date=datetime.utcnow())
    print("Ingestion complete")


if __name__ == "__main__":
    main()
