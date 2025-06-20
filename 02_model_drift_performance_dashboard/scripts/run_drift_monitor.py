#!/usr/bin/env python3
"""Run Evidently drift report periodically and expose metric."""
import time
import pandas as pd
from prometheus_client import Gauge, start_http_server
from evidently.report import Report
from evidently.metrics import DataDriftPreset
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_PATH = os.getenv("DATA_PATH", "../data/predictions.csv")
INTERVAL = int(os.getenv("DRIFT_CHECK_INTERVAL", "60"))  # seconds
MIN_WINDOW_SIZE = int(os.getenv("MIN_WINDOW_SIZE", "50"))

drift_gauge = Gauge("model_drift_score", "Drift score computed by Evidently")
last_check_gauge = Gauge("model_drift_last_check_timestamp", "Timestamp of last drift check")
data_points_gauge = Gauge("model_drift_data_points", "Number of data points used for drift detection")


def compute_drift() -> float:
    """Compute drift score using sliding window approach."""
    try:
        df = pd.read_csv(DATA_PATH, header=None, names=["ts", "feature", "pred", "actual"])
        logger.info(f"Loaded {len(df)} data points")
        
        # Use sliding window approach: last N rows as current, previous N as reference
        if len(df) < 2 * MIN_WINDOW_SIZE:
            logger.warning(f"Insufficient data for drift detection: {len(df)} < {2 * MIN_WINDOW_SIZE}")
            data_points_gauge.set(len(df))
            return 0.0
        
        # Use most recent data for better drift detection
        ref = df.iloc[-2*MIN_WINDOW_SIZE:-MIN_WINDOW_SIZE]
        cur = df.iloc[-MIN_WINDOW_SIZE:]
        
        logger.info(f"Computing drift with reference window: {len(ref)}, current window: {len(cur)}")
        data_points_gauge.set(len(df))
        
        report = Report(metrics=[DataDriftPreset()])
        report.run(reference_data=ref, current_data=cur)
        score = report.as_dict()["metrics"][0]["result"]["dataset_drift"]
        
        logger.info(f"Drift score: {score}")
        return float(score)
        
    except FileNotFoundError:
        logger.error(f"Data file not found: {DATA_PATH}")
        drift_gauge.set(0.0)
        return 0.0
    except pd.errors.EmptyDataError:
        logger.error("Data file is empty")
        drift_gauge.set(0.0)
        return 0.0
    except Exception as exc:
        logger.error(f"Unexpected error in drift computation: {exc}", exc_info=True)
        return 0.0


def main():
    logger.info(f"Starting drift monitor on port 8001, checking every {INTERVAL} seconds")
    start_http_server(8001)
    
    while True:
        try:
            score = compute_drift()
            drift_gauge.set(score)
            last_check_gauge.set(time.time())
        except Exception as exc:
            logger.error(f"Drift monitoring error: {exc}", exc_info=True)
        
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
