from fastapi import APIRouter, HTTPException
from models.user import User, UserRequest, UserResponse
from fastapi import Depends
from sqlalchemy.orm import Session
from database.database import get_db
from utils import hash_password 


router = APIRouter()

@router.post("/register", response_model=UserResponse)
def create_user(user_req: UserRequest, db: Session = Depends(get_db)):
    print("Register endpoint called")
    
    # Check if username exists
    existing_user = db.query(User).filter(User.username == user_req.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    print(f"Great! {user_req.username} is not taken")
    
    # Create and save user
    new_user = User(
        username=user_req.username,
        fullname=user_req.fullname,
        email=user_req.email,
        hashed_password=hash_password(user_req.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    print(f"New user created: {new_user}")
    
    response = UserResponse(username=new_user.username, email=new_user.email)
    return response