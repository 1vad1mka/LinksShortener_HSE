import random
import string
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from shorturl import shorten_url_hash
from pydantic_schemas import (
    ShortenURLModelRequest,
    ShortenURLModelResponse,
    ShortCodeStatsResponse
)
from db_models import URLAddresses
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_async_session
from manager import current_user, current_active_user
from database import User
from typing import List

router = APIRouter(prefix='/links')

@router.post("/shorten") #response_model=ShortenURLModelResponse
async def shorten_url(
        url: ShortenURLModelRequest,
        user: User = Depends(current_user),
        session: AsyncSession = Depends(get_async_session)
):
    # Извлекаем из БД все shorten_url
    query = select(URLAddresses.shorten_url)
    shorten_urls_db = await session.execute(query)
    shorten_urls_db = shorten_urls_db.scalars().all()

    # Если пользователь передает кастомный alias
    if url.custom_alias:
        if url.custom_alias in shorten_urls_db:
            raise HTTPException(status_code=400, detail="This alias is already taken!")
        url_hash = url.custom_alias
    else:
        url_hash = shorten_url_hash(url.url)

    # Проверяем, есть ли такой хеш уже в базе данных, чтобы избежать коллизий
    while url_hash in shorten_urls_db:
        additional_letters = ''.join(random.choices(string.ascii_letters, k=4))
        url_hash = shorten_url_hash(url.url + additional_letters)

    # Проверяем, есть ли авторизованный пользователь
    if user:
        user_id = user.id
    else:
        user_id = None

    # Определяем, какие значения вставлять в БД
    values_to_insert = {
         'user_id': user_id,
         'initial_url': url.url,
         'shorten_url': url_hash,
         'open_url_count': 0,
    }

    # Записываем данные в БД
    query = insert(URLAddresses).values(**values_to_insert)
    shorten_urls_db = await session.execute(query)
    await session.commit()

    # Возвращаем данные
    return  ShortenURLModelResponse(shorten_url=url_hash, status='success')


# Поиск ссылки по оригинальному URL:
@router.get("/search")
async def search_url_alias(
        url: str,
        session: AsyncSession = Depends(get_async_session)
):
    query = select(URLAddresses.shorten_url).where(URLAddresses.initial_url==url)
    initial_url = await session.execute(query)
    initial_url = initial_url.scalars().all()

    return  initial_url

@router.get("/{short_code}") # response_model=RedirectResponse
async def redirect_to_initial_url(
        short_code: str,
        session: AsyncSession = Depends(get_async_session)
):

    # Извлекаем известные Url из БД
    query = select(URLAddresses.shorten_url)
    shorten_urls_db = await session.execute(query)
    shorten_urls_db = shorten_urls_db.scalars().all()

    if short_code not in shorten_urls_db:
        raise HTTPException(status_code=404, detail="There's no url with such alias!")

    try:
        query = select(URLAddresses.initial_url).where(URLAddresses.shorten_url==short_code)
        initial_url = await session.execute(query)
        initial_url = initial_url.scalars().all()[0]

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Something went wrong. details: {e}")

    # Если url невалиден, может возникнуть ошибка
    try:
        return RedirectResponse(url=initial_url)
    except:
        raise HTTPException(
            status_code=400,
            detail="Error: something went wrong. Perhaps url is not valid."
        )


# Выводим статистику по alias'у
# Отображает оригинальный URL, возвращает дату создания, количество переходов,
# дату последнего использовани.
@router.get("/links/{short_code}/stats", response_model=ShortCodeStatsResponse)
async def short_code_stats(
        short_code: str,
        session: AsyncSession = Depends(get_async_session)
):
    query = select(
        URLAddresses.id,
        URLAddresses.initial_url,
        URLAddresses.open_url_count,
        URLAddresses.created_at,
        URLAddresses.last_used_at
    ).where(URLAddresses.shorten_url==short_code)

    short_code_info = await session.execute(query)

    for row in short_code_info:
        result = {
            'initial_url': row[1],
            'redirect_count': row[2],
            'created_at': row[3],
            'last_used_at': row[4]
        }

    response = ShortCodeStatsResponse(
        initial_url=result['initial_url'],
        redirect_count=result['redirect_count'],
        created_at=result['created_at'],
        last_used_at=result['last_used_at']
    )

    return response