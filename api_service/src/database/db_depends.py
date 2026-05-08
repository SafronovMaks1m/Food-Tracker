from .connect_db import async_session_maker
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session