# utils/qr.py
import qrcode
from django.core.files.base import ContentFile
from io import BytesIO
from django.conf import settings 

def generate_qr(qr_code_obj):

    qr_url =  f"{settings.SITE_URL}/scan/{qr_code_obj.qr_id}/"

    qr = qrcode.make(qr_url)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    file_name = f"{qr_code_obj.seat.lab.name}_{qr_code_obj.seat.seat_number}.png"
    qr_code_obj.qr_image.save(
        file_name,
        ContentFile(buffer.getvalue()),
        save=True
    )
