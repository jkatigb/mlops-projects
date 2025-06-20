import os
from feast import FeatureStore


def main():
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    store = FeatureStore(repo_path=repo_dir)
    features = store.get_online_features(
        features=[
            "driver_stats:conv_rate",
            "driver_stats:acc_rate",
            "driver_stats:avg_daily_trips",
        ],
        entity_rows=[{"driver_id": 1001}],
    ).to_dict()
    print(features)


if __name__ == "__main__":
    main()
