#!/usr/bin/env python3
"""Simple traffic generator for the model API."""
import argparse
import csv
import random
import time
import requests
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://localhost:8000/predict")
DATA_FILE = Path(os.getenv("DATA_FILE", "../data/predictions.csv"))


def generate_sample(mode: str) -> tuple:
    """Generate feature and ground truth value based on mode."""
    feature = random.random()
    if mode == "drift":
        # shift distribution
        feature += 3.0
    # ground truth based on different coefficient to simulate drift
    true_coeff = 0.5 if mode == "good" else 1.0
    actual = feature * true_coeff
    return feature, actual


def main():
    parser = argparse.ArgumentParser(description="Generate traffic for model drift demo")
    parser.add_argument("--mode", choices=["good", "drift"], default="good",
                        help="Traffic mode: 'good' for normal, 'drift' for shifted distribution")
    parser.add_argument("--n", type=int, default=100,
                        help="Number of requests to generate")
    parser.add_argument("--delay", type=float, default=0.1,
                        help="Delay between requests in seconds")
    args = parser.parse_args()
    
    # Ensure data directory exists
    DATA_FILE.parent.mkdir(exist_ok=True)
    
    # Check if file is empty to add header
    add_header = not DATA_FILE.exists() or DATA_FILE.stat().st_size == 0
    
    logger.info(f"Generating {args.n} requests in '{args.mode}' mode")
    logger.info(f"API URL: {API_URL}")
    logger.info(f"Data file: {DATA_FILE}")
    
    success_count = 0
    error_count = 0
    
    with open(DATA_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if add_header:
            writer.writerow(["timestamp", "feature", "prediction", "actual"])
        
        for i in range(args.n):
            try:
                feat, actual = generate_sample(args.mode)
                resp = requests.post(API_URL, json={"feature": feat}, timeout=3)
                resp.raise_for_status()
                
                pred = resp.json()["prediction"]
                writer.writerow([time.time(), feat, pred, actual])
                f.flush()  # Ensure data is written immediately
                
                success_count += 1
                if (i + 1) % 10 == 0:
                    logger.info(f"Progress: {i + 1}/{args.n} requests sent")
                    
            except requests.exceptions.RequestException as e:
                error_count += 1
                logger.error(f"Request failed: {e}")
            except KeyError as e:
                error_count += 1
                logger.error(f"Invalid response format: {e}")
            except Exception as e:
                error_count += 1
                logger.error(f"Unexpected error: {e}")
            
            time.sleep(args.delay)
    
    logger.info(f"Completed: {success_count} successful, {error_count} errors")


if __name__ == "__main__":
    main()
