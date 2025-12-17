# app/main.py
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator, Optional

from dotenv import load_dotenv
import os
load_dotenv()




from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config.settings import settings 
from app.core.logging_config import configure_logging
from app.api.router import router as api_router

from app.config.settings import settings
# from app.listeners.technical_listener import start as tech_start
# from app.listeners.pricing_listener import start as pricing_start
# from app.listeners.proposal_listener import start as proposal_start
# from app.listeners.legal_listener import start as legal_start
# from app.listeners.human_listener import start as human_start
from app.listeners.main_listener import start as main_listener

# Optional DB module: we'll import with try/except so app still works without DB.
try:
    from app.db.mongo import mongo_client  # <- stub provided below
except Exception:
    mongo_client = None

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting app %s %s", settings.APP_NAME, settings.APP_VERSION)

    import google.generativeai as genai

    print("Configuring GenAI with API Key:", settings.GENAI_API_KEY is not None)
    print("GENAI_API_KEY value (first 5 chars):", settings.GENAI_API_KEY[:5] if settings.GENAI_API_KEY else "None")

    genai.configure(api_key=settings.GENAI_API_KEY)

    # DB Connect
    if mongo_client is not None:
        try:
            await mongo_client.connect()
            logger.info("MongoDB connected")
        except Exception:
            logger.exception("Failed to connect to MongoDB during startup")
            raise

    # 💡 START LISTENERS HERE — inside lifespan
    # print("🚀 Starting all event listeners...")
    # tech_start()
    # pricing_start()
    # proposal_start()
    # legal_start()
    # human_start()
    # print("✅ All listeners running in background.")
    print("🚀 Starting main listener...")
    main_listener()  # Start main listener

    yield   # App is running!

    # Shutdown
    if mongo_client is not None:
        try:
            await mongo_client.disconnect()
            logger.info("MongoDB disconnected")
        except Exception:
            logger.exception("Error while disconnecting MongoDB")


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
    )

    # Middleware
    trusted_hosts = getattr(settings, "TRUSTED_HOSTS", None)
    if trusted_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)


    app.add_middleware(GZipMiddleware, minimum_size=500)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=settings.CORS_METHODS or ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=settings.CORS_HEADERS or ["*"],
    )

    # Register routers (keep router implementations in app/api)
    app.include_router(api_router, prefix="/api")

    # Light-weight health & readiness endpoints
    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}

    @app.get("/ready", tags=["health"])
    async def ready():
        # If DB available, include its readiness
        db_ready = True
        if mongo_client is not None:
            try:
                db_ready = mongo_client.is_connected()
            except Exception:
                db_ready = False

        status_code = status.HTTP_200_OK if db_ready else status.HTTP_503_SERVICE_UNAVAILABLE
        return JSONResponse(content={"db": db_ready}, status_code=status_code)

    # Global exception handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning("HTTP error %s %s", exc.status_code, exc.detail)
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception: %s", exc)
        payload = {"detail": "Internal Server Error"} if not settings.DEBUG else {"detail": str(exc)}
        return JSONResponse(payload, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
