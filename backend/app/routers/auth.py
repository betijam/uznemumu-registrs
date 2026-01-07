from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import text
from etl.loader import engine
from app.schemas.auth import UserCreate, UserLogin, Token, UserResponse, TokenData
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import os
import logging

# Config
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_in_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30  # 30 days

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    with engine.connect() as conn:
        user = conn.execute(text("SELECT * FROM users WHERE email = :email"), {"email": token_data.email}).fetchone()
        if user is None:
            raise credentials_exception
        return user

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate):
    with engine.connect() as conn:
        # Check existing
        existing = conn.execute(text("SELECT id FROM users WHERE email = :email"), {"email": user.email}).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_pw = get_password_hash(user.password)
        
        # Insert
        result = conn.execute(text("""
            INSERT INTO users (email, hashed_password, full_name, auth_provider)
            VALUES (:email, :pw, :name, 'email')
            RETURNING id, email, full_name, created_at, auth_provider
        """), {
            "email": user.email, 
            "pw": hashed_pw, 
            "name": user.full_name
        })
        conn.commit()
        new_user = result.fetchone()
        
        return new_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with engine.connect() as conn:
        # Check user
        user = conn.execute(text("SELECT * FROM users WHERE email = :email"), {"email": form_data.username}).fetchone()
        
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Update last login
        conn.execute(text("UPDATE users SET last_login = NOW() WHERE id = :id"), {"id": user.id})
        conn.commit()
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user = Depends(get_current_user)):
    return current_user
