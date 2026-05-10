from src.database.connect_db import Base
from sqlalchemy.orm import Mapped, mapped_column

class ProductsNutrition(Base):
    __tablename__ = "products_nutrition"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(unique=True, index=True)
    calories: Mapped[float]
    fat: Mapped[float]
    carbs: Mapped[float]
    sugar: Mapped[float]
    protein: Mapped[float]
    fiber: Mapped[float]
    cholesterol: Mapped[float]
    sodium: Mapped[float]
    iron: Mapped[float]