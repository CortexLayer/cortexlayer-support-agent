"""Routes for authentication (register + login)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.auth import (
    create_access_token,
    hash_password,
    verify_password,
)
from backend.app.core.database import get_db
from backend.app.models.client import BillingStatus, Client
from backend.app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from backend.app.services.stripe_service import create_customer
from backend.app.utils.logger import logger

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse)
async def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Register a new client and initialize billing state safely."""
    existing = db.query(Client).filter(Client.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # 1. Create Stripe customer (no payment yet)
    try:
        stripe_customer_id = create_customer(
            email=request.email,
            name=request.company_name,
        )
    except Exception as exc:
        logger.error("Stripe customer creation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Billing setup failed. Please try again later.",
        ) from exc

    # 2. Create client in GRACE_PERIOD (not ACTIVE)
    client = Client(
        email=request.email,
        hashed_password=hash_password(request.password),
        company_name=request.company_name,
        stripe_customer_id=stripe_customer_id,
        billing_status=BillingStatus.GRACE_PERIOD,
        is_disabled=False,
    )

    try:
        db.add(client)
        db.commit()
        db.refresh(client)
    except Exception as exc:
        db.rollback()
        logger.critical(
            "Client creation failed after Stripe \
customer creation "
            "(customer_id=%s): %s",
            stripe_customer_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account creation failed. Please contact support.",
        ) from exc

    token = create_access_token({"sub": str(client.id)})
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login_user(
    request: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Login existing client and return access token."""
    client = db.query(Client).filter(Client.email == request.email).first()

    if not client or not verify_password(
        request.password,
        client.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if client.is_disabled or client.billing_status == BillingStatus.DISABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled due to billing or policy issues.",
        )

    token = create_access_token({"sub": str(client.id)})
    return TokenResponse(access_token=token)
