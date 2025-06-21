#!/usr/bin/env python3
import argparse
import requests
import time
import random
import sys
from datetime import datetime

# Sample Iris dataset features for variety
IRIS_SAMPLES = [
    [5.1, 3.5, 1.4, 0.2],  # Setosa
    [4.9, 3.0, 1.4, 0.2],  # Setosa
    [7.0, 3.2, 4.7, 1.4],  # Versicolor
    [6.4, 3.2, 4.5, 1.5],  # Versicolor
    [6.3, 3.3, 6.0, 2.5],  # Virginica
    [5.8, 2.7, 5.1, 1.9],  # Virginica
]

def generate_traffic(url, rps, duration):
    """Generate traffic to the model endpoint."""
    print(f"Starting traffic generation:")
    print(f"  URL: {url}")
    print(f"  RPS: {rps}")
    print(f"  Duration: {duration}s")
    print("-" * 50)
    
    end_time = time.time() + duration
    total_requests = 0
    successful_requests = 0
    failed_requests = 0
    
    while time.time() < end_time:
        start = time.time()
        
        # Select random sample
        sample = random.choice(IRIS_SAMPLES)
        payload = {"data": {"ndarray": [sample]}}
        
        try:
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                successful_requests += 1
            else:
                failed_requests += 1
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Request failed with status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            failed_requests += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Request error: {type(e).__name__}")
        
        total_requests += 1
        
        # Print progress every 10 seconds
        if total_requests % (rps * 10) == 0:
            success_rate = (successful_requests / total_requests) * 100 if total_requests > 0 else 0
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Sent {total_requests} requests | Success rate: {success_rate:.1f}%")
        
        # Sleep to maintain target RPS
        elapsed = time.time() - start
        sleep_time = max(0, (1.0 / rps) - elapsed)
        time.sleep(sleep_time)
    
    # Final summary
    print("-" * 50)
    print(f"Traffic generation complete:")
    print(f"  Total requests: {total_requests}")
    print(f"  Successful: {successful_requests}")
    print(f"  Failed: {failed_requests}")
    print(f"  Success rate: {(successful_requests / total_requests) * 100:.1f}%")

def main():
    parser = argparse.ArgumentParser(description='Generate traffic to ML model endpoint')
    parser.add_argument('--url', 
                        default='http://iris-model.default.svc.cluster.local/api/v1.0/predictions',
                        help='Model endpoint URL')
    parser.add_argument('--rps', 
                        type=int, 
                        default=10,
                        help='Requests per second')
    parser.add_argument('--duration', 
                        type=int, 
                        default=300,
                        help='Duration in seconds')
    args = parser.parse_args()
    
    try:
        generate_traffic(args.url, args.rps, args.duration)
    except KeyboardInterrupt:
        print("\nTraffic generation interrupted by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
