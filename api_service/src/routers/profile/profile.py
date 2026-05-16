from fastapi import APIRouter, Body, status, File, UploadFile, Depends, HTTPException
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.redis_service.redis_depends import get_redis_connection
from src.schemas.UserSchema import UserVerificationCode
from src.services.verification_code.verification_error import VerificationError
from src.database.db_depends import get_async_db
from src.services.s3_storage.s3_service import s3_client
from src.models.users import Users
from src.schemas.ProfileShema import ChangeProfile, ChangeEmail
from src.auth.password_hashing import verify_password
from src.auth.auth import get_current_user
from src.services.verification_code.verification_service import VerificationService
from src.config import MINIO_CURRENT_EXTERNAL_URL
from redis import Redis

router = APIRouter(
    prefix="/change-profile",
    tags=["profile"]
)

@router.patch("/", status_code=status.HTTP_200_OK)
async def change_profile(
    schema : ChangeProfile = Depends(ChangeProfile.as_form),
    image: UploadFile | None = File(default=None),
    db: AsyncSession = Depends(get_async_db),
    user: Users = Depends(get_current_user)
):
    if schema.name:
        user.name = schema.name
    if image:
        if user.avatar_url:
            await s3_client.delete_image("avatars", user.avatar_url)
        file_name = await s3_client.upload_image("avatars", image)
        print(file_name)
        user.avatar_url = file_name
    await db.commit()
    
    avatar_url = f"{MINIO_CURRENT_EXTERNAL_URL}/avatars/{user.avatar_url}" if user.avatar_url else None
    return {"url": avatar_url, "name": user.name}

@router.post("/email", status_code=status.HTTP_200_OK)
async def change_email(
    schema: ChangeEmail,
    db: AsyncSession = Depends(get_async_db),
    user: Users = Depends(get_current_user),
    redis: Redis = Depends(get_redis_connection)
):
    if not verify_password(schema.password.get_secret_value(), user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="неверный пароль"
        )
    if user.email == schema.new_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="новый email должен отличаться от старого"
        )
        
    db_email = await db.scalar(select(Users).where(Users.email == schema.new_email))
    if db_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="аккаунт с таким Email уже существует"
        )
    try:
        service = VerificationService(redis)
        await service.get_code("change_email", schema.new_email)
    except VerificationError as exp:
        raise HTTPException(status_code=exp.status_code, detail=exp.message)
    return {"detail": "Код подтверждения был отправлен на новый электронный адрес"}

@router.post("/get-new-code/email", status_code=status.HTTP_200_OK)
async def get_new_code(
    new_email: EmailStr = Body(embed=True),
    redis: Redis = Depends(get_redis_connection),
    user: Users = Depends(get_current_user)
):
    try:
        service = VerificationService(redis)
        await service.get_code("change_email", new_email)
        return {"detail": "Код подтверждения был отправлен на ваш электронный адрес"}
    except VerificationError as exp:
        raise HTTPException(status_code=exp.status_code, detail=exp.message)

@router.post("/verification-code/email")
async def setup_new_email(
    setup_schema: UserVerificationCode,
    db: AsyncSession = Depends(get_async_db),
    redis: Redis = Depends(get_redis_connection),
    user: Users = Depends(get_current_user)
):
    db_email = await db.scalar(select(Users).where(Users.email == setup_schema.email))
    if db_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Этот Email уже был кем-то занят, пока вы вводили код"
        )
    try:
        service = VerificationService(redis)
        await service.verification_code(setup_schema.code, f"change_email:{setup_schema.email}", setup_schema.email)
    except VerificationError as exp:
        raise HTTPException(status_code=exp.status_code, detail=exp.message)
    user.email = setup_schema.email
    await db.commit()
    return {"detail": "Ваш email успешно изменён"}