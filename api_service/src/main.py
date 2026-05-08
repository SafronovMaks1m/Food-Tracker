from fastapi import FastAPI
from src.routers.auth import users
from src.routers.profile import profile
from src.routers.image_analysis import main_router
from src.services.lifespan import lifespan
from .logging_config import setup_logging
from src.middlewares.logging_middleware import log_middleware

setup_logging()

app = FastAPI(
    lifespan=lifespan,
    title="website of the food_tracker",
    version="0.1.0"
)

app.middleware("http")(log_middleware)

@app.get("/")
async def root():
    return {"message": "Hello on site"}

app.include_router(router=users.router)
app.include_router(router=profile.router)
app.include_router(router=main_router.router)
