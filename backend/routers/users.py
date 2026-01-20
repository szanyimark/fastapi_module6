from typing import List

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database.database import get_db
from models.user import User, UserRequest, UserResponse, LoginRequest
from utils import hash_password, verify_password


router = APIRouter()


@router.get("/", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


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

@router.post("/login")
def login_user(login_req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        or_(
            User.username == login_req.username_or_email,
            User.email == login_req.username_or_email,
        )
    ).first()
    
    if not user or not verify_password(login_req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful"}