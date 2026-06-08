"""
Генерация QR-кодов
Ничего менять не нужно
"""

import qrcode
import os

# Папка для сохранения QR-кодов
QR_DIR = "app/static/qr_codes"
os.makedirs(QR_DIR, exist_ok=True)

def generate_qr_code(team_id: int, team_name: str, captain_email: str) -> str:
    """
    Генерирует QR-код с информацией о команде
    Возвращает путь к сохранённому файлу
    """
    
    # Данные, которые будут зашиты в QR-код
    # Формат: TEAM_ID:123|NAME:Команда|EMAIL:test@mail.com
    qr_data = f"TEAM_ID:{team_id}|NAME:{team_name}|EMAIL:{captain_email}"
    
    # Создаём QR-код
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Создаём изображение
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Формируем имя файла (без пробелов)
    filename = f"team_{team_id}_{team_name.replace(' ', '_').replace('/', '_')}.png"
    filepath = os.path.join(QR_DIR, filename)
    
    # Сохраняем
    img.save(filepath)
    
    return filepath