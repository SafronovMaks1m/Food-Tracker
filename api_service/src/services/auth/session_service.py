from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.auth import create_access_token, create_refresh_token
from src.config import REFRESH_TOKEN_EXPIRE_DAYS
from src.models.sessions import Sessions
from src.models.users import Users

class SessionService:
    def __init__(self, user: Users, db: AsyncSession):
        self.db_user = user
        self.db = db
    
    async def create_or_update_session(self, device: str):
        cur_session = await self.db.scalar(
            select(Sessions).where(
                Sessions.user_id == self.db_user.id,
                Sessions.device_id == device
            )
        )
        tmp = create_refresh_token()
        if cur_session is None:
            cur_session = Sessions(
                device_id = device,
                refresh_token_hash = tmp.get("hashed_token"),
                expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
                user_id = self.db_user.id
            )
            self.db.add(cur_session)
        else:
            if not cur_session.is_active or cur_session.revoked:
                cur_session.revoked = False
                cur_session.is_active = True
            cur_session.refresh_token_hash = tmp.get("hashed_token")
            cur_session.expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        await self.db.commit()
        await self.db.refresh(cur_session)
        access_token = create_access_token(data={"sub": str(cur_session.id)})
        return {"access_token": access_token,
                "refresh_token": tmp.get("token"),
                "token_type": "bearer"}