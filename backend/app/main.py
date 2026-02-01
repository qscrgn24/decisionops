from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.db_health import router as db_health_router
from app.core.config import settings

def create_app():
    app = FastAPI(title=settings.APP_NAME)
    app.include_router(health_router)
    app.include_router(db_health_router)
    return app


app = create_app()