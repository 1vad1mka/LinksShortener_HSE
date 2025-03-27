import datetime
import random
import string
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from functions import shorten_url_hash
from pydantic_schemas import (
    ShortenURLModelRequest,
    ShortenURLModelResponse,
    ShortCodeStatsResponse,
    DeleteShortCodeResponse,
    ChangeShortCodeResponse
)
from sqlalchemy import select, insert, update, and_, or_, distinct, delete, TIMESTAMP
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from db import get_async_session
from users import current_user, current_active_user
from db import User, URLAddresses, ExpiredURLHistory
from typing import List
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache

router = APIRouter(prefix='/links')


async def delete_expired(session, n_days_expired=30):
    """
    Функция для удаления истекших ссылок, а также для удаления неиспользуемых ссылок:
        - session: сессия БД
        - n_days_expired: число дней, после которых url удаляются из БД
    """
    # Добавляем все истекшие ссылки в таблицу с url
    query = select(URLAddresses).where(
        or_(
            URLAddresses.expires_at <= func.now(),
            func.extract('day', (func.now() - URLAddresses.created_at)) > n_days_expired
        )
    )


    records_to_insert = await session.execute(query)
    records_to_insert = records_to_insert.scalars().all()

    if records_to_insert:
        for record in records_to_insert:
            values_to_insert = {
                 'user_id': record.user_id,
                 'initial_url': record.initial_url,
                 'shorten_url': record.shorten_url,
                 'open_url_count': record.open_url_count,
                 'created_at': record.created_at,
                 'last_used_at': record.last_used_at,
                 'expired_at': record.expires_at
            }

            # Записываем данные в БД
            try:
                query = insert(ExpiredURLHistory).values(**values_to_insert)
                await session.execute(query)
                await session.commit()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Something went wrong. Details: {e}")

        # Удаляем все ссылки, срок действия которых истек
        try:
            query = delete(URLAddresses).where(
        or_(
            URLAddresses.expires_at <= func.now(),
            func.extract('day', (func.now() - URLAddresses.created_at)) > n_days_expired
        )
    )
            await session.execute(query)
            await session.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Something went wrong. Details: {e}")

        return None


@router.post("/shorten") #response_model=ShortenURLModelResponse
async def shorten_url(
        url: ShortenURLModelRequest,
        user: User = Depends(current_user),
        session: AsyncSession = Depends(get_async_session)
):
    # Предварительно удаляем истекшие ссылки
    try:
        _ = await delete_expired(session)
    except Exception as e:
       raise HTTPException(status_code=500, detail=f"Something went wrong. Details: {e}")

    # Извлекаем из БД все shorten_url
    try:
        query = select(URLAddresses.shorten_url)
        shorten_urls_db = await session.execute(query)
        shorten_urls_db = shorten_urls_db.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong. Details: {e}")

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
         'expires_at': url.expires_at.replace(tzinfo=None)
    }

    # Записываем данные в БД
    try:
        query = insert(URLAddresses).values(**values_to_insert)
        shorten_urls_db = await session.execute(query)
        await session.commit()
    except Exception as e:
       raise HTTPException(status_code=500, detail=f"Something went wrong. Details: {e}")

    # Возвращаем данные
    return  ShortenURLModelResponse(shorten_url=url_hash, status='success')


# Поиск ссылки по оригинальному URL:
@router.get("/search")
@cache(expire=60)
async def search_url_alias(
        url: str,
        session: AsyncSession = Depends(get_async_session)
):
    # Предварительно удаляем истекшие ссылки
    try:
        _ = await delete_expired(session)
    except Exception as e:
       raise HTTPException(status_code=500, detail=f"Something went wrong. Details: {e}")

    try:
        query = select(URLAddresses.shorten_url).where(URLAddresses.initial_url==url)
        initial_url = await session.execute(query)
        initial_url = initial_url.scalars().all()
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Something went wrong. Perhaps url is not valid. Details: {e}"
        )

    return  initial_url


@router.get("/{short_code}") # response_model=RedirectResponse
async def redirect_to_initial_url(
        short_code: str,
        session: AsyncSession = Depends(get_async_session)
):
    # Предварительно удаляем истекшие ссылки
    try:
        _ = await delete_expired(session)
    except Exception as e:
       raise HTTPException(status_code=500, detail=f"Something went wrong. Details: {e}")


    # Удаляем кэш, т.к. редирект инкрементирует counter перехода по ссылке
    await FastAPICache.clear()

    try:
        # Извлекаем известные Url из БД
        query = select(URLAddresses.shorten_url)
        shorten_urls_db = await session.execute(query)
        shorten_urls_db = shorten_urls_db.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong. Details: {e}")

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
        # Увеличиваем счетчик использования ссылки
        query = update(URLAddresses)\
                .where(URLAddresses.shorten_url == short_code)\
                .values({URLAddresses.open_url_count: URLAddresses.open_url_count + 1})
        await session.execute(query)
        await session.commit()

        # Обновляем дату последнего использования
        query = update(URLAddresses)\
                .where(URLAddresses.shorten_url == short_code)\
                .values({URLAddresses.last_used_at: datetime.datetime.now()})
        await session.execute(query)
        await session.commit()

        return RedirectResponse(url=initial_url)
    except:
        raise HTTPException(
            status_code=400,
            detail="Error: something went wrong. Perhaps url is not valid."
        )


# Выводим статистику по alias'у
# Отображает оригинальный URL, возвращает дату создания, количество переходов,
# дату последнего использования.
@router.get("/{short_code}/stats", response_model=ShortCodeStatsResponse)
@cache(expire=60)
async def short_code_stats(
        short_code: str,
        session: AsyncSession = Depends(get_async_session)
):
    # Предварительно удаляем истекшие ссылки
    try:
        _ = await delete_expired(session)
    except Exception as e:
       raise HTTPException(status_code=500, detail=f"Something went wrong. Details: {e}")

    # Проверяем, есть ли такой short_code
    query = select(distinct(URLAddresses.shorten_url))
    short_codes_db = await session.execute(query)
    short_codes_db = short_codes_db.scalars().all()

    if short_code not in short_codes_db:
        raise HTTPException(
            status_code=404,
            detail=f"URL Alias '{short_code}' doesn't exist! Try another one."
        )

    # Работаем со статистикой
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong. Details: {e}")

    return response


# Endpoint, который удаляет связь
@router.delete("/{short_code}")
async def delete_url_alias(
        short_code: str,
        session: AsyncSession = Depends(get_async_session),
        user: User = Depends(current_active_user)
):
    # Предварительно удаляем истекшие ссылки
    try:
        _ = await delete_expired(session)
    except Exception as e:
       raise HTTPException(status_code=500, detail=f"Something went wrong. Details: {e}")

    # Очищаем кэш
    await FastAPICache.clear()

    # Проверяем, создавал ли данный пользователь ссылки
    query = select(distinct(URLAddresses.user_id))
    unique_ids = await session.execute(query)
    unique_ids = unique_ids.scalars().all()

    if user.id not in unique_ids:
        raise HTTPException(status_code=400, detail="You haven't created any url's aliases yet!")

    # Проверяем, создал ли пользователь данный alias
    query = select(distinct(URLAddresses.user_id))\
            .where(URLAddresses.shorten_url == short_code)
    unique_ids = await session.execute(query)
    unique_ids = unique_ids.scalars().all()

    if user.id not in unique_ids:
        raise HTTPException(
            status_code=400,
            detail="You haven't created this url's aliases! Permission denied!"
        )

    # Удаляем url
    query = delete(URLAddresses).where(
        and_(URLAddresses.user_id == user.id, URLAddresses.shorten_url == short_code)
    )
    initial_url = await session.execute(query)
    await session.commit()

    # Формируем ответ
    response = DeleteShortCodeResponse(
        status="success",
        details=f"URL's alias '{short_code}' was deleted!"
    )

    return  response


# PUT /links/{short_code} – обновляет URL (То есть, короткий адрес.
# Будем засчитывать и другую реализацию - когда к короткой ссылке привязывается новая длинная).
@router.put("/{short_code}")
async def change_short_code(
        initial_short_code: str,
        new_short_code: str,
        session: AsyncSession = Depends(get_async_session),
        user: User = Depends(current_active_user)
):
    # Предварительно удаляем истекшие ссылки
    try:
        _ = await delete_expired(session)
    except Exception as e:
       raise HTTPException(status_code=500, detail=f"Something went wrong. Details: {e}")

    # Очищаем кэш
    await FastAPICache.clear()

    # Проверяем, создавал ли данный пользователь ссылки
    query = select(distinct(URLAddresses.user_id))
    unique_ids = await session.execute(query)
    unique_ids = unique_ids.scalars().all()

    if user.id not in unique_ids:
        raise HTTPException(status_code=400, detail="You haven't created any url's aliases yet!")

    # Проверяем, создал ли пользователь данный alias
    query = select(distinct(URLAddresses.user_id))\
            .where(URLAddresses.shorten_url == initial_short_code)
    unique_ids = await session.execute(query)
    unique_ids = unique_ids.scalars().all()

    if user.id not in unique_ids:
        raise HTTPException(
            status_code=400,
            detail="You haven't created this url's aliases! Permission denied!"
        )

    # Проверяем, что нового short_code'а ещё нет в БД
    query = select(distinct(URLAddresses.shorten_url))
    unique_aliases = await session.execute(query)
    unique_aliases  = unique_aliases.scalars().all()

    if new_short_code in unique_aliases:
        raise HTTPException(
            status_code=400,
            detail=f"URL Alias {initial_short_code} already exists! Try another one!"
        )

    # Изменяем url
    query = update(URLAddresses) \
        .where(
        and_(URLAddresses.shorten_url == initial_short_code, URLAddresses.user_id == user.id)
    )\
        .values({URLAddresses.shorten_url: new_short_code})
    await session.execute(query)
    await session.commit()

    # Формируем ответ
    response = ChangeShortCodeResponse(
        status="success",
        details=f"URL's alias '{initial_short_code}' was changed to {new_short_code}!"
    )

    return  response