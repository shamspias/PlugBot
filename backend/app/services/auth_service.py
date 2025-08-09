import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from ..core.config import settings
from ..core.security import security_manager
from ..models.user import User, PasswordResetToken, RefreshToken
from ..schemas.auth import UserRegister, TokenResponse
from ..utils.logger import get_logger
from ..utils.mailer import send_email

logger = get_logger(__name__)


class AuthService:
    """Authentication service."""

    def __init__(self):
        self.access_token_expire = timedelta(minutes=30)
        self.refresh_token_expire = timedelta(days=7)
        self.reset_token_expire = timedelta(hours=1)

    def create_user(self, user_data: UserRegister, db: Session) -> User:
        """Create a new user."""
        # Check if user exists
        existing_user = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()

        if existing_user:
            if existing_user.email == user_data.email:
                raise ValueError("Email already registered")
            else:
                raise ValueError("Username already taken")

        # Create user
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=security_manager.hash_password(user_data.password),
            full_name=user_data.full_name
        )

        # First user becomes superuser
        user_count = db.query(User).count()
        if user_count == 0:
            user.is_superuser = True
            user.email_verified = True

        db.add(user)
        db.commit()
        db.refresh(user)

        # Send verification email if not superuser
        if not user.is_superuser:
            self._send_verification_email(user, db)

        return user

    def authenticate_user(self, email: str, password: str, db: Session) -> Optional[User]:
        """Authenticate a user."""
        user = db.query(User).filter(User.email == email).first()

        if not user:
            return None

        if not security_manager.verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.commit()

        return user

    def create_tokens(self, user: User, db: Session) -> TokenResponse:
        """Create access and refresh tokens."""
        # Create access token
        access_token_data = {
            "sub": user.id,
            "email": user.email,
            "username": user.username,
            "is_superuser": user.is_superuser
        }
        access_token = security_manager.create_access_token(
            access_token_data,
            self.access_token_expire
        )

        # Create refresh token
        refresh_token_str = self._generate_token(64)
        refresh_token = RefreshToken(
            user_id=user.id,
            token=refresh_token_str,
            expires_at=datetime.now(timezone.utc) + self.refresh_token_expire
        )

        # Revoke old refresh tokens
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked == False
        ).update({"revoked": True})

        db.add(refresh_token)
        db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            expires_in=int(self.access_token_expire.total_seconds())
        )

    def refresh_access_token(self, refresh_token: str, db: Session) -> Optional[TokenResponse]:
        """Refresh access token using refresh token."""
        token = db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.now(timezone.utc)
        ).first()

        if not token:
            return None

        user = db.query(User).filter(User.id == token.user_id).first()
        if not user or not user.is_active:
            return None

        # Revoke old token
        token.revoked = True
        db.commit()

        # Create new tokens
        return self.create_tokens(user, db)

    def request_password_reset(self, email: str, db: Session) -> bool:
        """Request password reset."""
        user = db.query(User).filter(User.email == email).first()

        if not user:
            # Don't reveal if user exists
            return True

        # Generate reset token
        reset_token = self._generate_token(32)

        # Save token
        token_record = PasswordResetToken(
            user_id=user.id,
            token=reset_token,
            expires_at=datetime.now(timezone.utc) + self.reset_token_expire
        )

        # Invalidate old tokens
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False
        ).update({"used": True})

        db.add(token_record)
        db.commit()

        # Send email with HTML template
        reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={reset_token}"

        try:
            # HTML email template
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .button {{ display: inline-block; padding: 12px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Password Reset Request</h1>
                    </div>
                    <div class="content">
                        <p>Hello {user.full_name or user.username},</p>

                        <p>We received a request to reset your password for your PlugBot account.</p>

                        <p>Click the button below to reset your password:</p>

                        <div style="text-align: center;">
                            <a href="{reset_url}" class="button">Reset Password</a>
                        </div>

                        <p>Or copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; background: #fff; padding: 10px; border-radius: 5px;">
                            {reset_url}
                        </p>

                        <p><strong>This link will expire in 1 hour for security reasons.</strong></p>

                        <p>If you didn't request this password reset, please ignore this email. Your password won't be changed.</p>

                        <div class="footer">
                            <p>Best regards,<br>The PlugBot Team</p>
                            <p>This is an automated message, please do not reply to this email.</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """

            # Plain text fallback
            text_body = f"""
    Hello {user.full_name or user.username},

    We received a request to reset your password for your PlugBot account.

    Click the link below to reset your password:
    {reset_url}

    This link will expire in 1 hour for security reasons.

    If you didn't request this password reset, please ignore this email. Your password won't be changed.

    Best regards,
    The PlugBot Team
            """

            send_email(
                to_email=user.email,
                subject="Password Reset Request - PlugBot",
                body=text_body,
                html_body=html_body  # You'll need to update the send_email function to support HTML
            )
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
            return False

        return True

    def reset_password(self, token: str, new_password: str, db: Session) -> bool:
        """Reset user password."""
        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > datetime.now(timezone.utc)
        ).first()

        if not reset_token:
            return False

        user = db.query(User).filter(User.id == reset_token.user_id).first()
        if not user:
            return False

        # Update password
        user.hashed_password = security_manager.hash_password(new_password)

        # Mark token as used
        reset_token.used = True

        # Revoke all refresh tokens
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user.id
        ).update({"revoked": True})

        db.commit()

        return True

    def revoke_refresh_token(self, refresh_token: str, db: Session) -> bool:
        """Revoke a refresh token (logout)."""
        token = db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token
        ).first()

        if token:
            token.revoked = True
            db.commit()
            return True

        return False

    def _generate_token(self, length: int = 32) -> str:
        """Generate a random token."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def _send_verification_email(self, user: User, db: Session):
        """Send email verification."""
        # Generate verification token
        verification_token = self._generate_token(32)

        # You can store this in a new table or reuse password_reset_tokens table
        # For simplicity, let's reuse the password reset token table with a flag

        verification_url = f"{settings.FRONTEND_URL}/auth/verify-email?token={verification_token}"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; padding: 12px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to PlugBot!</h1>
                </div>
                <div class="content">
                    <p>Hello {user.full_name or user.username},</p>

                    <p>Thank you for registering with PlugBot. Please verify your email address to complete your registration.</p>

                    <div style="text-align: center;">
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </div>

                    <p>Or copy and paste this link:</p>
                    <p style="word-break: break-all; background: #fff; padding: 10px; border-radius: 5px;">
                        {verification_url}
                    </p>

                    <p>Best regards,<br>The PlugBot Team</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
    Welcome to PlugBot!

    Hello {user.full_name or user.username},

    Thank you for registering with PlugBot. Please verify your email address by clicking the link below:

    {verification_url}

    Best regards,
    The PlugBot Team
        """

        try:
            send_email(
                to_email=user.email,
                subject="Verify Your Email - PlugBot",
                body=text_body,
                html_body=html_body
            )
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")


auth_service = AuthService()
