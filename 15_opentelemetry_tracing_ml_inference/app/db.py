import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@db/postgres",
)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)


async def fetch_feature(value: float) -> float:
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT :val + 1"), {"val": value})
        row = result.fetchone()
        return row[0]
