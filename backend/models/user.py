from sqlalchemy import Column, Integer, String
from pydantic import BaseModel
from database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    fullname = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
class UserRequest(BaseModel):
    username: str
    fullname: str
    email: str
    password: str

class UserResponse(BaseModel):
    username: str
    email: str 