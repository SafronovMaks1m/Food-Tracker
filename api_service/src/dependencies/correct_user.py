from fastapi import HTTPException, Depends, status
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.users import Users
from src.database.db_depends import get_async_db

async def get_unauthorized_user(email: EmailStr, db: AsyncSession):
    db_user = await db.scalar(
        select(Users)
        .where(Users.email == email, 
            Users.is_active)
        )
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Пользователя с таким email не существует.")
    return db_user

async def get_unauthorized_user(email: EmailStr, db: AsyncSession = Depends(get_async_db)) -> Users:
    db_user = await db.scalar(
        select(Users)
        .where(Users.email == email, 
            Users.is_active)
        )
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Пользователя с таким email не существует.")
    return db_user

def check_user_blocked(db_user: Users):
    if not db_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="У вас нет прав на эту операцию")