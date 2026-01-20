import os

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from routers import users

from database.database import engine, Base
from fastapi.middleware.cors import CORSMiddleware

# # Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS configuration from environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=os.getenv("CORS_CREDENTIALS", "True").lower() == "true",
    allow_methods=os.getenv("CORS_METHODS", "*").split(","),
    allow_headers=os.getenv("CORS_HEADERS", "*").split(","),
)

app.include_router(users.router, prefix="/users", tags=["Users"])

@app.get("/")
def read_root():
    return {"message": "WWelcome to the FastAPI backend!"}