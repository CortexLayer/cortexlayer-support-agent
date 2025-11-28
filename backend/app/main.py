"""FastAPI entrypoint."""

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.utils.logger import logger

# Initialize Sentry
if settings.SENTRY_DSN:
    sentry_sdk.init(dsn=settings.SENTRY_DSN)

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint confirming API is running."""
    return {"status": "healthy", "service": "cortexlayer-support-agent"}


@app.on_event("startup")
async def startup():
    """Executed when application is starting."""
    logger.info("🚀 CortexLayer Support Agent starting up...")


@app.on_event("shutdown")
async def shutdown():
    """Executed when application is shutting down."""
    logger.info("🛑 CortexLayer Support Agent shutting down...")
