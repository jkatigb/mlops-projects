import asyncio
import random
import httpx
import argparse


async def send_requests(url: str) -> None:
    async with httpx.AsyncClient() as client:
        while True:
            payload = {"feature": random.random()}
            await client.post(f"{url}/predict", json=payload)
            await asyncio.sleep(random.uniform(0.05, 0.5))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    args = parser.parse_args()
    asyncio.run(send_requests(args.url))


if __name__ == "__main__":
    main()
