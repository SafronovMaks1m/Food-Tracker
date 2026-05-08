from src.database.connect_db import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import JSON, ForeignKey, Enum, DateTime, func
from datetime import datetime
from typing import TYPE_CHECKING
from .process_status import ProcessStatus

if TYPE_CHECKING:
    from src.models.users import Users

class ImageAnalysis(Base):
    __tablename__ = "image_analysis"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    
    s3_key: Mapped[str] = mapped_column(unique=True, index=True)
    status: Mapped["ProcessStatus"] = mapped_column(Enum(ProcessStatus, native_enum=False), default=ProcessStatus.PENDING)
    result: Mapped[dict | None]= mapped_column(JSON, default=None)
    create_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    viewed: Mapped[bool] = mapped_column(default=False)
    
    user: Mapped["Users"] = relationship("Users", back_populates="images")
     