from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import FileResponse

from app.api.datasets import router as datasets_router
from app.api.db_health import router as db_health_router
from app.api.health import router as health_router
from app.api.runs import router as runs_router
from app.auth.router import router as auth_router
from app.core.config import settings
from app.middleware.browser_security import BrowserSecurityMiddleware
from app.middleware.request_size import RequestSizeLimitMiddleware
from app.services.rate_limit import TokenBucketRateLimiter

load_dotenv()  # Load environment variables from .env file


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME)
    app.state.rate_limiter = TokenBucketRateLimiter(max_buckets=settings.MAX_RATE_LIMIT_BUCKETS)
    app.add_middleware(RequestSizeLimitMiddleware, max_bytes=settings.MAX_REQUEST_BYTES)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type"],
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
    app.add_middleware(
        BrowserSecurityMiddleware,
        allowed_origins=settings.allowed_origins,
        enable_hsts=settings.ENV.lower() in {"production", "prod", "production_debug"},
    )
    app.include_router(health_router, prefix="/api")
    app.include_router(db_health_router, prefix="/api")
    app.include_router(datasets_router, prefix="/api")
    app.include_router(runs_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")

    static_dir = Path(__file__).resolve().parent.parent / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
        index_html = static_dir / "index.html"

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa_fallback(full_path: str) -> FileResponse | dict[str, str]:
            if full_path.startswith("/api"):
                return {"detail": "Not Found"}
            if index_html.exists():
                return FileResponse(index_html)
            return {"detail": "Frontend not built"}

    return app


app = create_app()
