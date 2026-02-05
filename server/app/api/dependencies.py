from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import jwt
from app.core.config import settings
from app.core.database import get_db
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from app.core.uow import AsyncUnitOfWork
    from app.repositories.conversation_repo import ConversationRepository
    from app.repositories.roadmap_repo import RoadmapRepository
    from app.services.discovery_service import DiscoveryStreamService
    from app.services.roadmap_service import RoadmapStreamService

logger = logging.getLogger(__name__)

# Optional security - allows unauthenticated requests if no token
security = HTTPBearer(auto_error=False)

# Initialize JWKS client for Supabase (ES256 tokens)
_jwks_client = None


def get_jwks_client():
    global _jwks_client
    if _jwks_client is None and settings.SUPABASE_URL:
        jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client


class CurrentUser:
    """Represents the authenticated user from JWT."""

    def __init__(self, user_id: str, email: str | None = None):
        self.user_id = user_id
        self.email = email


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> CurrentUser:
    """
    Validates the Supabase JWT and returns the current user.

    Raises:
        HTTPException: If token is missing or invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        # Get the algorithm from the token header
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get("alg", "HS256")

        if alg == "ES256":
            # Use JWKS for ES256 tokens
            jwks_client = get_jwks_client()
            if not jwks_client:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="JWKS client not configured",
                )
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256"],
                audience="authenticated",
            )
        else:
            # Use HS256 with JWT secret (older Supabase projects)
            if not settings.SUPABASE_JWT_SECRET:
                logger.warning(
                    "SUPABASE_JWT_SECRET not configured, skipping validation"
                )
                return CurrentUser(user_id="dev-user", email="dev@example.com")

            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
            )

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )

        return CurrentUser(user_id=user_id, email=email)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"JWT validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> CurrentUser | None:
    """
    Returns the current user if authenticated, else None.
    Does not raise exceptions for missing or invalid tokens.
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


# --- Unit of Work Provider ---


def get_uow() -> "AsyncUnitOfWork":
    from app.core.uow import AsyncUnitOfWork

    return AsyncUnitOfWork()


# --- Repository Providers ---


async def get_conversation_repo(
    session: AsyncSession = Depends(get_db),
) -> "ConversationRepository":
    from app.repositories.conversation_repo import ConversationRepository

    return ConversationRepository(session)


async def get_roadmap_repo(
    session: AsyncSession = Depends(get_db),
) -> "RoadmapRepository":
    from app.repositories.roadmap_repo import RoadmapRepository

    return RoadmapRepository(session)


# --- Service Providers ---


def get_discovery_service(
    uow: "AsyncUnitOfWork" = Depends(get_uow),
) -> "DiscoveryStreamService":
    from app.services.discovery_service import DiscoveryStreamService, discovery_manager

    return DiscoveryStreamService(uow, discovery_manager)


def get_roadmap_service(
    uow: "AsyncUnitOfWork" = Depends(get_uow),
) -> "RoadmapStreamService":
    from app.services.roadmap_service import RoadmapStreamService, roadmap_manager

    return RoadmapStreamService(uow, roadmap_manager)
