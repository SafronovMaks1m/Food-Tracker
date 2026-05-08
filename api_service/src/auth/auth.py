from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt, secrets, hashlib
from src.config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM
from datetime import datetime, timezone, timedelta
from src.models.users import Users
from src.models.sessions import Sessions
from src.database.db_depends import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.sessions import Sessions
from sqlalchemy import select
from sqlalchemy.orm import joinedload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login/verification-code", auto_error=False)

def create_access_token(data: dict):
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload["exp"] = expire
    return jwt.encode(payload, SECRET_KEY, ALGORITHM)

def create_refresh_token() -> dict:
    refresh_token = secrets.token_urlsafe(64)
    hashed = hashlib.sha256(refresh_token.encode()).hexdigest()
    return {"token": refresh_token, "hashed_token": hashed}

async def get_current_session(token: str = Depends(oauth2_scheme),
                           db: AsyncSession = Depends(get_async_db)):
    """
    Проверяет JWT и возвращает сессию пользователя из базы.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=[ALGORITHM])
        session_id: int = int(payload.get("sub"))
        if session_id is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as e:
        raise credentials_exception
    session = await db.scalar(select(Sessions)
                              .options(joinedload(Sessions.user)
                                       .joinedload(Users.sessions))
                              .where(Sessions.id == session_id))
    if session is None or session.revoked or not session.is_active or not session.user.is_active:
        raise credentials_exception
    return session

async def get_current_session_optional(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_db)):
    try:
        return await get_current_session(token, db)
    except HTTPException:
        return None
    
async def get_current_user(current_session: Sessions = Depends(get_current_session)):
    """
    Проверяет JWT и возвращает пользователя из базы.
    """
    return current_session.user

async def get_current_student(current_user: Users = Depends(get_current_user)):
    """
    Проверяет, что пользователь имеет роль 'client'.
    """
    if current_user.role != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only client can perform this action")
    return current_user

async def get_current_admin(current_user: Users = Depends(get_current_user)):
    """
    Проверяет, что пользователь имеет роль 'admin'.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Admin can perform this action")
    return current_user