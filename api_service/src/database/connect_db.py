from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from src.config import PASSWORD_USER_DB, NAME_DB, NAME_USER

ASYNC_DATABASE_URL = f"postgresql+asyncpg://{NAME_USER}:{PASSWORD_USER_DB}@db:5432/{NAME_DB}"

ASYNC_DATABASE_URL_LOCAL = f"postgresql+asyncpg://{NAME_USER}:{PASSWORD_USER_DB}@localhost:5432/{NAME_DB}"

async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)

async_session_maker = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass