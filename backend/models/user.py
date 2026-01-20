from sqlalchemy import Column, Integer, String
from pydantic import BaseModel, EmailStr, ConfigDict
from database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    fullname = Column(String(100), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)


class UserRequest(BaseModel):
    username: str
    fullname: str | None = None
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    fullname: str | None
    email: EmailStr


class LoginRequest(BaseModel):
    username_or_email: str
    password: str