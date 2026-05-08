from fastapi import APIRouter
from .analysis import router as router_analysis

router = APIRouter(
    prefix="/image-analysis",
    tags=["image-analysis"]
)

router.include_router(router_analysis)