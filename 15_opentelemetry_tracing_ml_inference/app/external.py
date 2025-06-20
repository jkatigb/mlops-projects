import httpx


async def call_external() -> None:
    async with httpx.AsyncClient() as client:
        await client.get("https://httpbin.org/delay/0.1")
