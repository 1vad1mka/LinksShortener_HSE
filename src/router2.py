import asyncio
from datetime import datetime
import qrcode
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel

from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_async_session
from src.db import URLAddresses


router = APIRouter(prefix='/links')


# Создает QR для url
@router.post("/get_QR/")
async def generate_qr(
        url: str,
):
    # Генерация QR-кода
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Сохранение изображения в байтовый поток
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    # Возвращаем изображение как файл для скачивания
    return StreamingResponse(img_byte_arr, media_type="image/png",
                             headers={"Content-Disposition": "attachment; filename=qr_code.png"}
                             )



