from fastapi import Request, Response
from fastapi.responses import JSONResponse
from loguru import logger

async def log_middleware(request: Request, call_next):
    try:
        response: Response = await call_next(request)
        if 400 <= response.status_code < 500:
            logger.warning(f"Request to {request.url.path} failed. Method: {request.method}. Status_code: {response.status_code}")
    except Exception as ex:
        logger.error(f"Request to {request.url.path} failed: {ex}. Method: {request.method}")
        response = JSONResponse(
            content={"success": False, "message": "Internal Server Error"},
            status_code=500
        )
    return response