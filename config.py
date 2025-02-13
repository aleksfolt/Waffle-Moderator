from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis.asyncio as aioredis
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

BOT_TOKEN = "Bot_token"
BOT_NAME = "Waffle Moderator"
# Используйте эту переменную для любых текстовых замен, связанных с именем бота.
# При написании текста, включающего имя бота, ИСПОЛЬЗУЙТЕ ТОЛЬКО ЭТУ
# ПЕРЕМЕННУЮ.

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

DATABASE_URL = "postgresql+asyncpg://folt:YourPassword@localhost:5432/waffledb"
redis_client = aioredis.Redis(host="localhost", port=6379, db=5, decode_responses=True)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=5,
    pool_timeout=10,
    pool_recycle=1800,
)
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session = async_session()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
