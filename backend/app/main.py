"""FastAPI entrypoint."""

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings, validate_settings
from backend.app.core.database import SessionLocal
from backend.app.middleware.logging import log_requests
from backend.app.routes import admin, auth, query, upload, whatsapp
from backend.app.routes.webhook import router as webhook_router
from backend.app.utils.logger import logger
from backend.app.utils.redis_client import test_redis_connection
from backend.app.utils.s3 import list_bucket_safe

# Force eager config validation (FAIL FAST)
validate_settings()

# Initialize Sentry early
if settings.SENTRY_DSN:
    sentry_sdk.init(dsn=settings.SENTRY_DSN)

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

# Security & Transport Middleware (EARLY)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "testserver",
        "*.cortexlayertech.com",
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Observability & Performance
app.middleware("http")(log_requests)

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,
)

# Routes
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(webhook_router)
app.include_router(query.router)
app.include_router(upload.router)
app.include_router(whatsapp.router)


@app.get("/health")
async def health_check():
    """Health check - DB, Redis, S3 probes."""
    status = {"status": "healthy", "checks": {}}

    # Redis
    redis_ok = test_redis_connection()
    status["checks"]["redis"] = "ok" if redis_ok else "fail"

    # Database
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        status["checks"]["db"] = "ok"
    except Exception as exc:
        status["checks"]["db"] = f"fail: {exc}"

    # S3 (best effort)
    try:
        list_bucket_safe()
        status["checks"]["s3"] = "ok"
    except Exception as exc:
        status["checks"]["s3"] = f"fail: {exc}"

    if any(str(v).startswith("fail") for v in status["checks"].values()):
        return JSONResponse(status_code=503, content=status)

    return status


@app.on_event("startup")
async def startup():
    """Fail-fast startup validation."""
    logger.info("CortexLayer Support Agent starting up...")

    if not test_redis_connection():
        raise RuntimeError("Redis unavailable at startup")

    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except Exception as exc:
        raise RuntimeError(f"Database unavailable at startup: {exc}") from exc

    try:
        list_bucket_safe()
    except Exception as exc:
        raise RuntimeError(f"S3 unavailable at startup: {exc}") from exc

    logger.info("Startup checks passed")


@app.on_event("shutdown")
async def shutdown():
    """Executed when application is shutting down."""
    logger.info("CortexLayer Support Agent shutting down...")
