import datetime
from collections.abc import AsyncGenerator
from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from config import DATABASE_URL
from sqlalchemy import String, Integer, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
import datetime


# Создаем базовый класс для декларативного стиля
class Base(DeclarativeBase):
    pass

class User(SQLAlchemyBaseUserTableUUID, Base):
    # Определяем столбцы таблицы users
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    username: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String(length=320), nullable=False, unique=True)
    hashed_password = mapped_column(
        String(length=1000),
        nullable=False
    )
    registered_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now())
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_superuser = mapped_column(Boolean, nullable=False, default=True)
    is_verified = mapped_column(Boolean, nullable=False, default=True)


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)

