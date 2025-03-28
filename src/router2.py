import qrcode
from io import BytesIO

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse



router = APIRouter(prefix='/links')


# Создает QR для url
@router.post("/get_QR/")
async def generate_qr(
        url: str,
):
    try:
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

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong. Details: {str(e)}"
        )


    # Возвращаем изображение как файл для скачивания
    return StreamingResponse(img_byte_arr, media_type="image/png",
                             headers={"Content-Disposition": "attachment; filename=qr_code.png"}
                             )



