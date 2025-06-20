import argparse
import requests
import time

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://iris-model/v1/api/v1.0/predictions')
parser.add_argument('--rps', type=int, default=10)
parser.add_argument('--duration', type=int, default=60)
args = parser.parse_args()

payload = {"data": {"ndarray": [[5.1, 3.5, 1.4, 0.2]]}}

end = time.time() + args.duration
while time.time() < end:
    start = time.time()
    try:
        requests.post(args.url, json=payload, timeout=5)
    except Exception as e:
        print('request failed', e)
    sleep = max(0, (1.0/args.rps) - (time.time() - start))
    time.sleep(sleep)
