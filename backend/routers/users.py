from typing import List

import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database.database import get_db
from models.user import User, UserRequest, UserResponse, LoginRequest, TokenResponse
from utils import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        username = decode_access_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def find_or_create_user(
    db: Session,
    username: str,
    email: str,
    fullname: str
) -> str:
    """Find existing user or create new one. Returns the username."""
    existing = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing:
        return existing.username
    
    # Create new user with random password (OAuth users don't use password)
    random_pw = secrets.token_urlsafe(32)
    new_user = User(
        username=username,
        fullname=fullname,
        email=email,
        hashed_password=hash_password(random_pw),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user.username


@router.get("/", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(User).all()

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": "User deleted"}


@router.post("/register", response_model=UserResponse)
def create_user(user_req: UserRequest, db: Session = Depends(get_db)):
    # Check if username exists
    if db.query(User).filter(User.username == user_req.username).first():
        raise HTTPException(status_code=409, detail="Username already exists")

    # Check if email exists
    if db.query(User).filter(User.email == user_req.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Create and save user
    new_user = User(
        username=user_req.username,
        fullname=user_req.fullname,
        email=user_req.email,
        hashed_password=hash_password(user_req.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse.model_validate(new_user)

@router.post("/login", response_model=TokenResponse)
def login_user(login_req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        or_(
            User.username == login_req.username_or_email,
            User.email == login_req.username_or_email,
        )
    ).first()
    
    if not user or not verify_password(login_req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(subject=user.username)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )