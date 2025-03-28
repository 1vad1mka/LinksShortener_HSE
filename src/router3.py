from typing import Union
from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func

from db import get_async_session
from db import ExpiredURLHistory


router = APIRouter(prefix='/links')


# Создает QR для url
@router.post("/show_expired_url")
async def generate_qr(
        short_code: Union[str, None] = None,
        session: AsyncSession = Depends(get_async_session)
):
    if not short_code:
        try:
            query = select(ExpiredURLHistory)
            expired_urls = await session.execute(query)
            expired_urls= expired_urls.scalars().all()
            return expired_urls
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong. Details: {e}"
            )

    query = select(ExpiredURLHistory)
    expired_urls = await session.execute(query)
    expired_urls = expired_urls.scalars().all()

    if short_code not in expired_urls:
        raise HTTPException(
            status_code=400,
            detail=f"There's no such url alias in the database!"
        )


    try:
        query = select(ExpiredURLHistory).where(ExpiredURLHistory.shorten_url == short_code)
        expired_urls = await session.execute(query)
        expired_urls = expired_urls.scalars().all()
        return expired_urls
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong. Details: {e}"
        )