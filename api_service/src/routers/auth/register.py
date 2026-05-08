from fastapi import APIRouter, Body, File, Header, UploadFile, status, Depends, HTTPException
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.auth.auth import get_current_session_optional
from src.models.sessions import Sessions
from src.models.users import Users as UsersModel
from src.schemas.UserSchema import UserCreate, UserVerificationCode
from src.database.db_depends import get_async_db
from src.auth.password_hashing import hash_password
from src.services.verification_code.verification_service import VerificationService, VerificationError
from src.services.auth.session_service import SessionService
from pydantic import EmailStr
from src.redis_service.redis_depends import get_redis_connection
import json

router = APIRouter(
    prefix="/register"
)

@router.get("/", status_code=status.HTTP_200_OK)
async def get_login(session: Sessions = Depends(get_current_session_optional)):
    if session is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are already logged in"
        )
    return {"detail": "Okay"}

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_async_db),
    session: Sessions = Depends(get_current_session_optional),
    redis: Redis = Depends(get_redis_connection)
):
    if session is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are already logged in"
        )
    db_user = await db.scalar(select(UsersModel).where(UsersModel.email == user.email))
    if db_user:
        if db_user.google_id and not db_user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Аккаунт с таким email уже существует. Войдите через Google или установите пароль через кнопку 'Забыли пароль?'"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Аккаунт c таким email уже существует"
        )
    try:
        service = VerificationService(redis)
        await service.get_code("register", user.email)
        password = hash_password(user.password.get_secret_value())
        data = {
            "name": user.name,
            "email": user.email,
            "password": password
        }
        await redis.set(f"password_setup_register:{user.email}", json.dumps(data), ex=600)
        return {
            "detail": "Код подтверждения был отправлен на ваш электронный адрес"
        }
    except VerificationError as exp:
        raise HTTPException(status_code=exp.status_code, detail=exp.message)

@router.post("/get-new-code", status_code=status.HTTP_200_OK)
async def get_new_code(
    email: EmailStr = Body(embed=True),
    redis: Redis = Depends(get_redis_connection)
):
    try:
        service = VerificationService(redis)
        await service.get_code("register", email)
        return {"detail": "Код подтверждения был отправлен на ваш электронный адрес"}
    except VerificationError as exp:
        raise HTTPException(status_code=exp.status_code, detail=exp.message)

@router.post("/verification-code", status_code=status.HTTP_200_OK)
async def setup_user(
    setup_schema: UserVerificationCode,
    device: str = Header(...),
    db: AsyncSession = Depends(get_async_db),
    redis: Redis = Depends(get_redis_connection)
):
    try:
        service = VerificationService(redis)
        await service.verification_code(setup_schema.code, f"register:{setup_schema.email}", setup_schema.email)
    except VerificationError as exp:
        raise HTTPException(status_code=exp.status_code, detail=exp.message)
    key = f"password_setup_register:{setup_schema.email}"
    if await redis.exists(key) == 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Что то пошло не так, попробуйте снова")
    data = json.loads((await redis.get(key)))
    new_user = UsersModel(
        name = data["name"],
        email = data["email"],
        hashed_password = data["password"]
    )
    
    db.add(new_user)
    await db.commit()
    await redis.delete(key)

    session_serv = SessionService(new_user, db)
    result = await session_serv.create_or_update_session(device)
    return result