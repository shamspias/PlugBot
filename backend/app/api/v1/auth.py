from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from ...api.deps import get_db, get_current_user
from ...models.user import User
from ...schemas.auth import (
    UserRegister, UserLogin, TokenResponse, UserResponse,
    PasswordResetRequest, PasswordReset, RefreshTokenRequest
)
from ...services.auth_service import auth_service
from ...utils.logger import get_logger
from ...core.config import settings
import httpx

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
        user_data: UserRegister,
        db: Session = Depends(get_db)
):
    """Register a new user."""
    try:
        # Check if registration is allowed
        user_count = db.query(User).count()
        if user_count > 0 and not settings.ALLOW_REGISTRATION:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Registration is disabled"
            )

        user = auth_service.create_user(user_data, db)
        return UserResponse.from_orm(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(
        response: Response,
        credentials: UserLogin,
        db: Session = Depends(get_db)
):
    """Login user and return tokens."""
    user = auth_service.authenticate_user(
        credentials.email,
        credentials.password,
        db
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.email_verified and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email first"
        )

    tokens = auth_service.create_tokens(user, db)

    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60  # 7 days
    )

    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
        response: Response,
        request: Request,
        db: Session = Depends(get_db)
):
    """Refresh access token."""
    # Get refresh token from cookie or body
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        body = await request.json()
        refresh_token = body.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided"
        )

    tokens = auth_service.refresh_access_token(refresh_token, db)

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # Update refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )

    return tokens


@router.post("/logout")
async def logout(
        response: Response,
        request: Request,
        db: Session = Depends(get_db)
):
    """Logout user."""
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        auth_service.revoke_refresh_token(refresh_token, db)

    # Clear cookie
    response.delete_cookie("refresh_token")

    return {"message": "Successfully logged out"}


@router.post("/forgot-password")
async def forgot_password(
        data: PasswordResetRequest,
        db: Session = Depends(get_db)
):
    """Request password reset."""
    success = auth_service.request_password_reset(data.email, db)

    # Always return success to prevent email enumeration
    return {
        "message": "If an account exists with this email, you will receive a password reset link"
    }


@router.post("/reset-password")
async def reset_password(
        data: PasswordReset,
        db: Session = Depends(get_db)
):
    """Reset password with token."""
    success = auth_service.reset_password(data.token, data.new_password, db)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    return {"message": "Password successfully reset"}


@router.get("/me", response_model=UserResponse)
async def get_me(
        current_user: User = Depends(get_current_user)
):
    """Get current user info."""
    return UserResponse.from_orm(current_user)


@router.get("/verify")
async def verify_token(
        current_user: User = Depends(get_current_user)
):
    """Verify if token is valid."""
    return {"valid": True, "user_id": current_user.id}
