from fastapi import APIRouter, HTTPException, UploadFile, Depends, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.users import Users
from src.database.db_depends import get_async_db
from src.auth.auth import get_current_user
from src.services.s3_storage.s3_service import s3_client
from src.models.image_analysis import ImageAnalysis as ImageAnalysisModel
from src.models.process_status import ProcessStatus 
from src.schemas.ImageAnalysisSchema import ImageAnalysis as ImageAnalysisSchema
from src.rabbitmq_service.rabbitmq_client import rabbitmq_client
from loguru import logger
from datetime import datetime, timezone, timedelta

router = APIRouter(
    prefix="/analysis"
)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def analyze_image(
    image: UploadFile,
    user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    key = await s3_client.upload_image("food-images", image)
    logger_api = logger.bind(
        path='/image-analysis/analysis/',
        image_key=key
    )
    new_obj = ImageAnalysisModel(user_id = user.id, s3_key = key)
    db.add(new_obj)
    try:
        await db.commit()
    except Exception as exp:
        await s3_client.delete_image("food-images", key)
        logger_api.error(f"Ошибка при сохранение изображения. Ошибка: {exp}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Не получилось сохранить изображение, попробуйте позже"
        )
    data = {
        "user_id": user.id,
        "key": key
    }
    try:
        await rabbitmq_client.publish_task(data)
    except Exception as exp:
        new_obj.status = ProcessStatus.FAILED
        new_obj.result = {"detail": "Сервис очередей временно недоступен"}
        await db.commit()
        logger_api.error(f"Ошибка при отправки задачи в RabbitMQ. Ошибка: {exp}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Не удалось отправить задачу в обработку"
        )
    return {"detail": "Началась обработка изображения"}
    

@router.get("/status", response_model=ImageAnalysisSchema, status_code=status.HTTP_200_OK)
async def get_analysis_result(
    user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
): 
    last_analysis = await db.scalar(
        select(ImageAnalysisModel)
        .where(ImageAnalysisModel.user_id == user.id)
        .order_by(desc(ImageAnalysisModel.create_at))
        .limit(1)
    )
    
    if not last_analysis:
        return {"status": None, "result": None, "viewed": True}
    now = datetime.now(timezone.utc)
    if last_analysis.status == ProcessStatus.PENDING:
        if now - last_analysis.create_at > timedelta(minutes=5):
            last_analysis.status = ProcessStatus.FAILED
            last_analysis.result = {"error": "Не удалось обработать изображение"}
            last_analysis.viewed = True
            await db.commit()
            return {
                "status": last_analysis.status,
                "result": last_analysis.result,
                "viewed": False
            }
        return last_analysis
    
    if not last_analysis.viewed:
        last_analysis.viewed = True
        await db.commit()
        return {
            "status": last_analysis.status,
            "result": last_analysis.result,
            "viewed": False
        }
        
    if now - last_analysis.create_at > timedelta(hours=1):
        return {"status": None, "result": None, "viewed": True}
    return last_analysis
    
    
    
    
