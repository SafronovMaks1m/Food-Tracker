from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    """
    Преобразует пароль в хеш с использованием Argon2.
    """
    return password_hash.hash(password)

def verify_password(password: str, password_hashed: str) -> bool:
    """
    Проверяет, соответствует ли введённый пароль сохранённому хешу.
    """
    if password_hashed is None:
        return False
    return password_hash.verify(password, password_hashed)