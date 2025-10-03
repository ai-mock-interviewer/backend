from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from .models import User
from .schemas import (
    UserRegister, UserLogin, UserResponse, TokenResponse, 
    UserProfile, PasswordChange
)
from .services import (
    authenticate_user, register_user, create_access_token,
    get_user_by_username_or_email, update_user_password
)
from .dependencies import get_current_active_user, require_auth
from config.database import get_db

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    try:
        user = register_user(db, user_data)
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            is_active=user.is_active
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user and return access token"""
    user = authenticate_user(
        db, 
        user_credentials.username_or_email, 
        user_credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Create access token (3 hours)
    access_token_expires = timedelta(hours=3)
    access_token = create_access_token(
        data={
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email
        },
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        user= user,
        access_token=access_token,
        token_type="bearer",
        expires_in=3 * 60 * 60  # 3 hours in seconds
    )


@router.post("/login-form", response_model=TokenResponse)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login using OAuth2 form (for FastAPI docs)"""
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Create access token (3 hours)
    access_token_expires = timedelta(hours=3)
    access_token = create_access_token(
        data={
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email
        },
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=3 * 60 * 60  # 3 hours in seconds
    )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user profile"""
    return UserProfile(
        user_id=current_user.user_id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at
    )


@router.put("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    # Verify current password
    from .services import verify_password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    success = update_user_password(db, current_user.user_id, password_data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )
    
    return {"message": "Password updated successfully"}


@router.get("/verify-token", status_code=status.HTTP_200_OK)
async def verify_token_endpoint(
    current_user: User = Depends(get_current_active_user)
):
    """Verify if the current token is valid"""
    return {
        "valid": True,
        "user_id": current_user.user_id,
        "username": current_user.username
    }
