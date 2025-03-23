from collections.abc import AsyncGenerator
from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Table, UUID
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.orm import DeclarativeBase
from src.config import DATABASE_URL
import datetime


class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    registered_at = Column(DateTime, nullable=False, default=datetime.datetime.now())


class URLAddresses(Base):
    __tablename__ = 'url'

    # Определяем столбцы таблицы urls
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID, ForeignKey('user.id'), nullable=True)  # Задаем внешний ключ
    initial_url = Column(String, nullable=False)
    shorten_url = Column(String, nullable=False, unique=True)
    open_url_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now())
    last_used_at = Column(DateTime, nullable=True, default=None)


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)