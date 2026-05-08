from fastapi import APIRouter, status, File, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db_depends import get_async_db
from src.services.s3_storage.s3_service import s3_client
from src.models.users import Users
from src.auth.auth import get_current_user
from src.config import MINIO_CURRENT_EXTERNAL_URL

router = APIRouter(
    prefix="/profile",
    tags=["profile"]
)

@router.patch("/change-profile", status_code=status.HTTP_200_OK)
async def change_profile(
    image: UploadFile | None = File(default=None),
    db: AsyncSession = Depends(get_async_db),
    user: Users = Depends(get_current_user)
):
    if image:
        file_name = await s3_client.upload_image("avatars", image)
        user.avatar_url = file_name
        await db.commit()
    return {"url": f"{MINIO_CURRENT_EXTERNAL_URL}/avatars/{file_name}"}
