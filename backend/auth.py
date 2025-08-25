import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)
from jose import JWTError, jwt
from models import APIKey, User
from sql_database import get_database
from sqlalchemy.orm import Session
from utils import generate_api_key, hash_api_key, verify_password

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)
api_key_scheme = HTTPBearer(auto_error=False)

# Rate limiting storage (in production, use Redis)
_rate_limit_storage = {}


class AuthenticationError(HTTPException):
    """Custom authentication exception"""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """Custom authorization exception"""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user with username and password"""
    try:
        from crud import get_user_by_username

        user = get_user_by_username(db, username)
        if not user:
            return None
        if not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    except Exception as e:
        logger.error(f"User authentication error: {e}")
        return None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token creation failed",
        ) from e


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return {"username": username, "exp": payload.get("exp")}
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None


def check_rate_limit(identifier: str, limit: int = 100, window: int = 3600) -> bool:
    """Simple rate limiting (use Redis in production)"""
    now = datetime.utcnow().timestamp()
    window_start = now - window

    if identifier not in _rate_limit_storage:
        _rate_limit_storage[identifier] = []

    # Clean old entries
    _rate_limit_storage[identifier] = [
        timestamp
        for timestamp in _rate_limit_storage[identifier]
        if timestamp > window_start
    ]

    # Check limit
    if len(_rate_limit_storage[identifier]) >= limit:
        return False

    # Add current request
    _rate_limit_storage[identifier].append(now)
    return True


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_database)
) -> User:
    """Get current user from JWT token"""
    if not token:
        raise AuthenticationError("Access token required")

    token_data = verify_token(token)
    if not token_data:
        raise AuthenticationError("Invalid or expired token")

    from crud import get_user_by_username

    user = get_user_by_username(db, username=token_data["username"])
    if user is None:
        raise AuthenticationError("User not found")

    if not user.is_active:
        raise AuthenticationError("Inactive user")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise AuthenticationError("Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current admin user"""
    if not current_user.is_admin:
        raise AuthorizationError("Admin access required")
    return current_user


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(api_key_scheme),
    db: Session = Depends(get_database),
) -> Optional[APIKey]:
    """Verify API key"""
    if not credentials:
        return None

    try:
        api_key_hash = hash_api_key(credentials.credentials)
        from crud import get_api_key_by_hash, update_api_key_usage

        api_key_obj = get_api_key_by_hash(db, api_key_hash)

        if not api_key_obj or not api_key_obj.is_active:
            return None

        # Check expiration
        if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
            return None

        # Update usage
        update__api_key_usage(db, api_key_obj.id)

        return api_key_obj
    except Exception as e:
        logger.error(f"API key verification error: {e}")
        return None


async def get_current_user_or_api_key(
    request: Request,
    token: str = Depends(oauth2_scheme),
    api_key: Optional[APIKey] = Depends(verify_api_key),
    db: Session = Depends(get_database),
) -> dict:
    """Get current user either from JWT token or API key"""

    # Rate limiting by IP
    client_ip = request.client.host
    if not check_rate_limit(f"ip:{client_ip}", limit=1000):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded"
        )

    # Try API key first
    if api_key:
        if not check_rate_limit(f"api_key:{api_key.id}", limit=api_key.rate_limit):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="API key rate limit exceeded",
            )

        from crud import get_user

        user = get_user(db, api_key.owner_id)
        return {"user": user, "api_key": api_key, "auth_type": "api_key"}

    # Try JWT token
    if token:
        user = await get_current_user(token, db)
        return {"user": user, "api_key": None, "auth_type": "jwt"}

    raise AuthenticationError("Authentication required")


# Permission checkers
def require_upload_permission(auth_data: dict = Depends(get_current_user_or_api_key)):
    """Require upload permission"""
    if auth_data["auth_type"] == "api_key":
        if not auth_data["api_key"].can_upload:
            raise AuthorizationError("Upload permission required")
    # JWT users always have upload permission
    return auth_data


def require_query_permission(auth_data: dict = Depends(get_current_user_or_api_key)):
    """Require query permission"""
    if auth_data["auth_type"] == "api_key":
        if not auth_data["api_key"].can_query:
            raise AuthorizationError("Query permission required")
    # JWT users always have query permission
    return auth_data


def require_admin_permission(auth_data: dict = Depends(get_current_user_or_api_key)):
    """Require admin permission"""
    if auth_data["auth_type"] == "api_key":
        if not auth_data["api_key"].can_admin:
            raise AuthorizationError("Admin permission required")
    else:
        if not auth_data["user"].is_admin:
            raise AuthorizationError("Admin permission required")
    return auth_data
