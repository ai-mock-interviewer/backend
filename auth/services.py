from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import or_
import os

from .models import User
from .schemas import UserRegister, UserLogin

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "180"))  # 3 hours


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    # Truncate password to 72 bytes if it's longer (bcrypt limit)
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    # Truncate password to 72 bytes if it's longer (bcrypt limit)
    if len(plain_password.encode('utf-8')) > 72:
        plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def authenticate_user(db: Session, username_or_email: str, password: str) -> Optional[User]:
    """Authenticate a user with username/email and password"""
    user = get_user_by_username_or_email(db, username_or_email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def get_user_by_username_or_email(db: Session, username_or_email: str) -> Optional[User]:
    """Get user by username or email"""
    return db.query(User).filter(
        or_(User.username == username_or_email, User.email == username_or_email)
    ).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.user_id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def register_user(db: Session, user_data: UserRegister) -> User:
    """Register a new user"""
    # Check if username already exists
    if get_user_by_username(db, user_data.username):
        raise ValueError("Username already exists")
    
    # Check if email already exists
    if get_user_by_email(db, user_data.email):
        raise ValueError("Email already exists")
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_password(db: Session, user_id: int, new_password: str) -> bool:
    """Update user password"""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    
    user.password_hash = hash_password(new_password)
    db.commit()
    return True


def deactivate_user(db: Session, user_id: int) -> bool:
    """Deactivate a user account"""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    
    user.is_active = False
    db.commit()
    return True


def activate_user(db: Session, user_id: int) -> bool:
    """Activate a user account"""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    
    user.is_active = True
    db.commit()
    return True
