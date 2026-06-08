from dotenv import load_dotenv
import os
import smtplib

load_dotenv()

print("Проверка настроек почты...")
print(f"SMTP_HOST: {os.getenv('SMTP_HOST')}")
print(f"SMTP_PORT: {os.getenv('SMTP_PORT')}")
print(f"SMTP_USER: {os.getenv('SMTP_USER')}")

try:
    server = smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT")))
    server.starttls()
    server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
    print("✅ Почта настроена правильно! Письма будут отправляться.")
    server.quit()
except Exception as e:
    print(f"❌ Ошибка: {e}")
    print("Проверь пароль приложения в файле .env")