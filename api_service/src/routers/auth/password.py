import uuid
from fastapi import APIRouter, status, Depends, HTTPException
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from src.dependencies.correct_user import get_unauthorized_user
from src.redis_service.redis_depends import get_redis_connection
from src.services.verification_code.verification_service import VerificationService
from src.services.verification_code.verification_error import VerificationError
from src.models.users import Users as UsersModel
from src.models.sessions import Sessions
from src.schemas.UserSchema import UserPasswordSetup, UserPasswordSetupAuth, UserVerificationCode
from src.database.db_depends import get_async_db
from src.auth.password_hashing import hash_password, verify_password
from src.auth.auth import get_current_session

router = APIRouter(
    prefix="/password"
)

@router.post("/get-new-code", status_code=status.HTTP_200_OK)
async def get_new_code(
    db_user: UsersModel = Depends(get_unauthorized_user),
    redis: Redis = Depends(get_redis_connection)
):
    try:
        service = VerificationService(redis)
        await service.get_code("change_pwd", db_user.email)
        return {"detail": "Код подтверждения был отправлен на ваш электронный адрес"}
    except VerificationError as exp:
        raise HTTPException(status_code=exp.status_code, detail=exp.message)

@router.post("/verification-code", status_code=status.HTTP_200_OK)
async def verification_code(
    ver_schema: UserVerificationCode,
    db: AsyncSession = Depends(get_async_db),
    redis: Redis = Depends(get_redis_connection)
):
    db_user = await get_unauthorized_user(ver_schema.email, db)
    try:
        service = VerificationService(redis)
        await service.verification_code(ver_schema.code, f"change_pwd:{ver_schema.email}", ver_schema.email)
        reset_token = str(uuid.uuid4())
        await redis.set(f"password_reset_token:{reset_token}", ver_schema.email, ex=600)
        return {"reset_token": reset_token}
    except VerificationError as exp:
        raise HTTPException(status_code=exp.status_code, detail=exp.message)

@router.patch("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_schema: UserPasswordSetup,
    db: AsyncSession = Depends(get_async_db),
    redis: Redis = Depends(get_redis_connection)
):
    key = f"password_reset_token:{password_schema.reset_token}"
    if await redis.exists(key) == 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Токен не валиден")
    email = await redis.get(key)
    db_user = await db.scalar(select(UsersModel)
                                .options(joinedload(UsersModel.sessions))
                                .where(UsersModel.email == email))
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                        detail="Пользователя с таким email не существует.")
    if not db_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                        detail="У вас нет прав доступа для этой операции")
    db_user.hashed_password = hash_password(password_schema.new_password.get_secret_value())
    for session in db_user.sessions:
        session.is_active = False
    await db.commit()
    await redis.delete(key)
    return {"detail": "Пароль успешно изменён"}

@router.get("/change-password-fast", status_code=status.HTTP_200_OK)
async def get_number_fields(
    session: Sessions = Depends(get_current_session),
):
    if session.user.google_id and not session.user.hashed_password:
        return {"old_password": False}
    return {"old_password": True}

@router.patch("/change-password-fast", status_code=status.HTTP_200_OK)
async def change_password_fast(
    password_schema: UserPasswordSetupAuth,
    session: Sessions = Depends(get_current_session),
    db: AsyncSession = Depends(get_async_db)
):
    if password_schema.old_password:
        old_password = password_schema.old_password.get_secret_value()
    else:
        old_password = None
        
    if (not session.user.google_id or session.user.hashed_password is not None) and not old_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Пожалуйста введите старый пароль"
        )
    elif session.user.google_id and not session.user.hashed_password and old_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="У вас не установлен старый пароль, так как вы входили через Google. Поле 'старый пароль' должно быть пустым"
        )
    new_password = password_schema.new_password.get_secret_value()
    db_user = session.user
    if old_password is not None:
        if not verify_password(old_password, db_user.hashed_password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Неверный старый пароль")
        if old_password == new_password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Новый пароль не должен совпадать со старым")
    db_user.hashed_password = hash_password(new_password)
    for db_session in db_user.sessions:
        if db_session.id != session.id:
            db_session.is_active = False
    await db.commit()
    return {"detail": "Пароль успешно изменён"}