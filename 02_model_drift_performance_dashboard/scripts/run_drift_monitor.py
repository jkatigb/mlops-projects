#!/usr/bin/env python3
"""Run Evidently drift report periodically and expose metric."""
import time
import pandas as pd
from prometheus_client import Gauge, start_http_server
from evidently.report import Report
from evidently.metrics import DataDriftPreset

DATA_PATH = "../data/predictions.csv"
INTERVAL = 60  # seconds

drift_gauge = Gauge("model_drift_score", "Drift score computed by Evidently")


def compute_drift() -> float:
    df = pd.read_csv(DATA_PATH, header=None, names=["ts", "feature", "pred", "actual"])
    if len(df) < 2:
        return 0.0
    ref, cur = df.iloc[: len(df)//2], df.iloc[len(df)//2 :]
    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=ref, current_data=cur)
    score = report.as_dict()["metrics"][0]["result"]["dataset_drift"]
    return float(score)


def main():
    start_http_server(8001)
    while True:
        try:
            score = compute_drift()
            drift_gauge.set(score)
        except Exception as exc:
            print(f"drift computation failed: {exc}")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
