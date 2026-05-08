from fastapi import APIRouter, Body, Depends, HTTPException, Header, status
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime, timezone, timedelta
from src.services.auth.session_service import SessionService
from src.dependencies.correct_user import get_unauthorized_user
from src.services.verification_code.verification_error import VerificationError
from src.services.verification_code.verification_service import VerificationService
from src.redis_service.redis_depends import get_redis_connection
from src.models.users import Users as UsersModel
from src.models.sessions import Sessions as SessionsModel
from src.schemas.UserSchema import UserLogin, UserVerificationCode
from src.database.db_depends import get_async_db
from src.auth.password_hashing import verify_password
from src.auth.auth import get_current_session_optional, create_access_token, create_refresh_token
from src.config import REFRESH_TOKEN_EXPIRE_DAYS
import hashlib

router = APIRouter(
    prefix="/login"
)

@router.get("/", status_code=status.HTTP_200_OK)
async def get_login(session: SessionsModel = Depends(get_current_session_optional)):
    if session is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are already logged in"
        )
    return {"detail": "Okay"}

@router.post("/", status_code=status.HTTP_200_OK)
async def login(
    user: UserLogin,
    db: AsyncSession = Depends(get_async_db),
    session: SessionsModel = Depends(get_current_session_optional),
    redis: Redis = Depends(get_redis_connection)
):
    db_user: UsersModel = await get_unauthorized_user(user.email, db)
    if session is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are already logged in"
        )
    if not verify_password(user.password.get_secret_value(), db_user.hashed_password):
        if db_user.google_id and not db_user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail = "У этого аккаунта нет пароля. Войдите через Google или установите пароль через кнопку 'Забыли пароль?'"
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильно введённый email или пароль"
        )
    try:
        service = VerificationService(redis)
        await service.get_code("auth", user.email)
        return {"detail": "Код подтверждения был отправлен на ваш электронный адрес"}
    except VerificationError as exp:
        raise HTTPException(status_code=exp.status_code, detail=exp.message)
    
@router.post("/get-new-code", status_code=status.HTTP_200_OK)
async def get_new_code(
    db_user: UsersModel = Depends(get_unauthorized_user),
    redis: Redis = Depends(get_redis_connection)
):
    try:
        service = VerificationService(redis)
        await service.get_code("auth", db_user.email)
        return {"detail": "Новый код подтверждения был отправлен на ваш электронный адрес"}
    except VerificationError as exp:
        raise HTTPException(status_code=exp.status_code, detail=exp.message)
        
@router.post("/verification-code", status_code=status.HTTP_200_OK)
async def verification_code(
    ver_schema: UserVerificationCode,
    device: str = Header(...),
    db: AsyncSession = Depends(get_async_db),
    redis: Redis = Depends(get_redis_connection)
):
    db_user = await db.scalar(
        select(UsersModel)
        .options(selectinload(UsersModel.sessions))
        .where(UsersModel.email == ver_schema.email,
               UsersModel.is_active)
        )
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Пользователя с таким email не существует.")
    try:
        service = VerificationService(redis)
        await service.verification_code(ver_schema.code, f"auth:{ver_schema.email}", ver_schema.email)
    except VerificationError as exp:
        raise HTTPException(status_code=exp.status_code, detail=exp.message)
    session_serv = SessionService(db_user, db)
    result = await session_serv.create_or_update_session(device)
    return result

@router.post("/refresh-token")
async def create_new_access_refresh_token(
    refresh_token: str = Body(..., embed=True), 
    db: AsyncSession = Depends(get_async_db)
):
    try:
        hashed_refresh_token = hashlib.sha256(refresh_token.encode()).hexdigest()
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh-token")
    cur_session = await db.scalar(
            select(SessionsModel)
            .options(joinedload(SessionsModel.user))
            .where(SessionsModel.refresh_token_hash == hashed_refresh_token, 
                  SessionsModel.is_active, SessionsModel.revoked == False))
    if cur_session is None or not cur_session.user.is_active:
        if cur_session:
            cur_session.is_active = False
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh-token")
    if datetime.now(timezone.utc) > cur_session.expires_at:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The token's lifetime has expired")
    
    new_refresh = create_refresh_token()
    cur_session.refresh_token_hash = new_refresh.get("hashed_token")
    cur_session.expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    await db.commit()
    
    return {
        "access_token": create_access_token(data={"sub": str(cur_session.id)}),
        "refresh_token": new_refresh.get("token"),
        "token_type": "bearer"
    }
