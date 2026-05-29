"""One-off script to verify the DATABASE_URL in .env actually connects.

Run with: python check_db.py
"""

import asyncio

from sqlalchemy import text

from app.db import engine


async def main() -> None:
    async with engine.connect() as conn:
        version = (await conn.execute(text("SELECT version()"))).scalar_one()
        one = (await conn.execute(text("SELECT 1"))).scalar_one()
    print(f"Connected. SELECT 1 -> {one}")
    print(f"Server: {version}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
