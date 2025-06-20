#!/usr/bin/env python3
"""Simple traffic generator for the model API."""
import argparse
import csv
import random
import time
import requests

API_URL = "http://localhost:8000/predict"


def generate_sample(mode: str) -> tuple:
    feature = random.random()
    if mode == "drift":
        # shift distribution
        feature += 3.0
    # ground truth based on different coefficient to simulate drift
    true_coeff = 0.5 if mode == "good" else 1.0
    actual = feature * true_coeff
    return feature, actual


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["good", "drift"], default="good")
    parser.add_argument("--n", type=int, default=100)
    args = parser.parse_args()

    with open("../data/predictions.csv", "a", newline="") as f:
        writer = csv.writer(f)
        for _ in range(args.n):
            feat, actual = generate_sample(args.mode)
            resp = requests.post(API_URL, json={"feature": feat}, timeout=3)
            pred = resp.json()["prediction"]
            writer.writerow([time.time(), feat, pred, actual])
            time.sleep(0.1)


if __name__ == "__main__":
    main()
