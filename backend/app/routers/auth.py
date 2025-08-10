from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import authenticate_user, create_access_token, create_user, ACCESS_TOKEN_EXPIRE_MINUTES
from app.schemas import UserCreate, UserLogin, Token, UserResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user account
    
    - **email**: Valid email address (will be validated)
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit required)
    """
    try:
        # Create user account
        user = create_user(db, user_data.email, user_data.password)
        
        logger.info(f"New user registered: {user.email}")
        
        return UserResponse(
            id=user.id,
            email=user.email,
            created_at=user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error for {user_data.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to server error"
        )

@router.post("/login", response_model=Token)
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT access token
    
    - **email**: User email address
    - **password**: User password
    
    Returns JWT token for accessing protected endpoints
    """
    try:
        # Authenticate user
        user = authenticate_user(db, login_data.email, login_data.password)
        if not user:
            logger.warning(f"Failed login attempt for {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        )
        
        logger.info(f"Successful login for user: {user.email}")
        
        return Token(
            access_token=access_token,
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {login_data.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to server error"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: str = Depends(lambda: None)  # Placeholder for refresh token logic
):
    """
    Refresh JWT access token
    
    Note: This is a placeholder for refresh token functionality
    In production, implement proper refresh token rotation
    """
    # REFINEMENT_HOOK: implement_refresh_token_logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token functionality not implemented"
    )

@router.post("/logout")
async def logout_user():
    """
    Logout user (client-side token removal)
    
    Since JWT tokens are stateless, logout is handled client-side
    by removing the token from storage
    """
    return {"message": "Logout successful. Please remove token from client storage."}

@router.post("/forgot-password")
async def forgot_password(email: str):
    """
    Request password reset
    
    - **email**: Email address for password reset
    
    Note: This is a placeholder for password reset functionality
    """
    # REFINEMENT_HOOK: implement_password_reset_logic
    logger.info(f"Password reset requested for: {email}")
    return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/reset-password")
async def reset_password(
    token: str,
    new_password: str
):
    """
    Reset password using reset token
    
    - **token**: Password reset token
    - **new_password**: New password
    
    Note: This is a placeholder for password reset functionality
    """
    # REFINEMENT_HOOK: implement_password_reset_logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset functionality not implemented"
    )