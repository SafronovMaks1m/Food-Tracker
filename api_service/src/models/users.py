from src.database.connect_db import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .sessions import Sessions
    from .image_analysis import ImageAnalysis

class Users(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    name: Mapped[str] = mapped_column()
    email: Mapped[str] = mapped_column(index=True, unique=True)
    hashed_password: Mapped[str | None] = mapped_column(default=None)
    is_active: Mapped[bool] = mapped_column(default = True)
    role: Mapped[str] = mapped_column(default="client")
    google_id: Mapped[str | None] = mapped_column(index=True, default=None, unique=True)
    avatar_url: Mapped[str | None] = mapped_column(default=None)
    
    sessions: Mapped[list["Sessions"]] = relationship("Sessions", back_populates="user")
    images: Mapped[list["ImageAnalysis"]] = relationship("ImageAnalysis", back_populates="user")