from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.db_health import router as db_health_router
from app.api.datasets import router as datasets_router
from app.api.runs import router as runs_router
from app.core.config import settings
from app.auth.router import router as auth_router

from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

def create_app():
    app = FastAPI(title=settings.APP_NAME)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(db_health_router)
    app.include_router(datasets_router)
    app.include_router(runs_router)
    app.include_router(auth_router)
    return app


app = create_app()