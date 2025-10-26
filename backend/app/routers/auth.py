from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import LoginRequest, Token
from app.config import settings
from app.auth import create_access_token, verify_password
from datetime import timedelta

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint for admin authentication"""
    # Simple hardcoded admin user for dev
    if (login_data.username == settings.admin_username and 
        login_data.password == settings.admin_password):
        
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": login_data.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
