import re

def password_verification(password: str):
    if len(password) < 8:
        raise ValueError("Минимум 8 символов")
    if not re.search(r"[a-z]", password):
        raise ValueError("Нужна строчная буква")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Нужна заглавная буква")
    if not re.search(r"\d", password):
        raise ValueError("Нужна цифра")
    if not re.search(r"[@$!%*?&]", password):
        raise ValueError("Нужен спецсимвол")