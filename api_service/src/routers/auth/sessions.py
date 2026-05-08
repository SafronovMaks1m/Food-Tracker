from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from src.models.sessions import Sessions as SessionsModel
from src.models.users import Users as UsersModel
from src.database.db_depends import get_async_db
from src.auth.auth import get_current_session, get_current_user

router = APIRouter(
    prefix="/sessions"
)

@router.delete("/one", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session: SessionsModel = Depends(get_current_session), 
                         db: AsyncSession = Depends(get_async_db)):
    session.is_active = False
    await db.commit()
    
@router.delete("/all", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_session(user: UsersModel = Depends(get_current_user), 
                         db: AsyncSession = Depends(get_async_db)):
    await db.execute(
        update(SessionsModel)
        .where(SessionsModel.user_id == user.id)
        .values(is_active=False)
    )
    await db.commit()