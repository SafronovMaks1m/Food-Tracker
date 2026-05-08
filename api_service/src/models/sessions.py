from src.database.connect_db import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import DateTime, ForeignKey
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from users import Users

class Sessions(Base):
    __tablename__ = "sessions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    
    device_id: Mapped[str] 
    refresh_token_hash: Mapped[str]
    revoked: Mapped[bool] = mapped_column(default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(default=True)
    
    user: Mapped["Users"] = relationship("Users", back_populates="sessions")
    
    