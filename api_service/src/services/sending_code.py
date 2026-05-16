from src.models.users import Users
from datetime import datetime, timezone, timedelta
from src.config import APPLICATION_PASSWORD_GMAIL
from email.message import EmailMessage
import smtplib
import secrets, hashlib

class SendCode:
    CONTEXT = {
        "auth": "Введите эти цифры на экране для входа в приложение.",
        "change_pwd": "Введите эти цифры на экране для смены пароля.",
        "change_email": "Введите эти цифры на экране для смены email.",
        "register": "Введите эти цифры на экране для окончания регистрации.",
    }
    
    @classmethod
    def send_code_email(cls, email: str, cnt: str, code: str):
        msg = EmailMessage()
        msg["From"] = "safranov01@gmail.com"
        msg["To"] = email
        msg["Subject"] = cls.CONTEXT[cnt]
        msg.set_content(code)
        
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login("safranov01@gmail.com", APPLICATION_PASSWORD_GMAIL)
            smtp.send_message(msg)