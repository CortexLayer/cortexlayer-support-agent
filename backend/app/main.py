"""FastAPI entrypoint."""

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from backend.app.core.config import settings
from backend.app.middleware.logging import log_requests
from backend.app.routes import admin, auth, query
from backend.app.routes.webhook import router as webhook_router
from backend.app.utils.logger import logger
from backend.app.utils.redis_client import test_redis_connection

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
    allow_origins=[
        "https://support-agent.dashboard.cortexlayertech.com",
        "http://localhost:3000",
    ],
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


@app.get("/health")
async def health_check():
    """Health check endpoint confirming API is running."""
    return {"status": "healthy", "service": "cortexlayer-support-agent"}


@app.on_event("startup")
async def startup():
    """Executed when application is starting."""
    logger.info("CortexLayer Support Agent starting up...")
    test_redis_connection()


@app.on_event("shutdown")
async def shutdown():
    """Executed when application is shutting down."""
    logger.info("CortexLayer Support Agent shutting down...")
