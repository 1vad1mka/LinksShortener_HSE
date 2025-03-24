import asyncio
from collections.abc import AsyncIterator
from datetime import datetime

from fastapi import APIRouter

from sqlalchemy import delete

from contextlib import asynccontextmanager

from src.db import get_async_session
from src.db import URLAddresses


async def get_db():
    async with get_async_session() as session:
        yield session

@asynccontextmanager
async def delete_expired_links(_: APIRouter):
    async with get_db() as session:
        while True:
            now = datetime.now()
            await session.execute(
                delete(URLAddresses).where(URLAddresses.expires_at <= now)
            )
            await session.commit()
            await asyncio.sleep(300)
            yield


router = APIRouter(lifespan=delete_expired_links)


