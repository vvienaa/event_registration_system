import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_qr_email(to_email: str, team_name: str, qr_filepath: str):
    print(f"📧 Отправка письма на {to_email}...")
    
    msg = MIMEMultipart()
    msg["Subject"] = f"✅ Ваш QR-код для мероприятия | Команда {team_name}"
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    # Текстовый логотип (без картинки, чтобы не было ошибок)
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <div style="background-color: #2E75B6; color: white; padding: 15px; text-align: center; border-radius: 10px;">
            <h2 style="margin: 0;">🏢 ООО «CodeStorage»</h2>
            <p style="margin: 5px 0 0 0;">Разработка веб-приложений</p>
        </div>
        <h2>Здравствуйте!</h2>
        <p>Ваша команда <strong>"{team_name}"</strong> успешно зарегистрирована.</p>
        <p>Ваш QR-код для входа находится во вложении.</p>
        <p>Сохраните его на телефон или распечатайте.</p>
        <hr>
        <p style="color: gray;">С уважением,<br>OOO CodeStorage</p>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html_content, "html"))

    # Прикрепляем QR-код
    with open(qr_filepath, "rb") as f:
        img = MIMEImage(f.read())
        img.add_header("Content-Disposition", "attachment", filename="qr_code.png")
        msg.attach(img)

    # Отправляем письмо
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
    
    print(f"✅ Письмо отправлено на {to_email}")