from pydantic import BaseModel, Field, ConfigDict


class ImageAnalysis(BaseModel):
    status: str | None = Field("Статус анализа изображения")
    result: dict | None = Field("Подробный результат анализа изображения")
    viewed: bool = Field("Просмотрен ли результат пользователем")
    
    model_config = ConfigDict(from_attributes=True)