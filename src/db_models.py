from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Table
from sqlalchemy.orm import relationship, declarative_base
import datetime

# Создаем базовый класс для декларативного стиля
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    # Определяем столбцы таблицы users
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    registered_at = Column(DateTime, nullable=False, default=datetime.datetime.now())
    is_active = Column(Boolean, nullable=False, default=True)
    is_superuser = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=True)
    # Устанавливаем обратную связь с таблицей url
    url = relationship("URLAddresses", back_populates="user")


class URLAddresses(Base):
    __tablename__ = 'url'

    # Определяем столбцы таблицы urls
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)  # Задаем внешний ключ
    initial_url = Column(String, nullable=False)
    shorten_url = Column(String, nullable=False, unique=True)
    open_url_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now())
    last_used_at = Column(DateTime, nullable=True, default=None)
    # Устанавливаем обратную связь с таблицей Users
    user = relationship("User", back_populates="url")