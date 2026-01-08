from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
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
import httpx
import secrets
import string

# Config
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_in_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30  # 30 days

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

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


# --- Google Auth ---

@router.get("/google")
async def login_google():
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google Client ID not configured")
    
    redirect_uri = f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/api/auth/google/callback"
    scope = "openid email profile"
    return RedirectResponse(
        f"https://accounts.google.com/o/oauth2/v2/auth?client_id={GOOGLE_CLIENT_ID}&redirect_uri={redirect_uri}&response_type=code&scope={scope}&access_type=offline&prompt=consent"
    )

@router.get("/google/callback")
async def google_callback(code: str, request: Request):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google config missing")

    redirect_uri = f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/api/auth/google/callback"
    
    async with httpx.AsyncClient() as client:
        # 1. Exchange code for token
        data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        resp = await client.post("https://oauth2.googleapis.com/token", data=data)
        if resp.status_code != 200:
            logger.error(f"Google Token Error: {resp.text}")
            raise HTTPException(status_code=400, detail="Failed to retrieve token from Google")
        
        token_data = resp.json()
        access_token = token_data.get("access_token")
        
        # 2. Get user info
        user_resp = await client.get("https://www.googleapis.com/oauth2/v2/userinfo", headers={"Authorization": f"Bearer {access_token}"})
        if user_resp.status_code != 200:
             raise HTTPException(status_code=400, detail="Failed to retrieve user info from Google")
        
        user_info = user_resp.json()
        email = user_info.get("email")
        full_name = user_info.get("name")
        
        return handle_social_login(email, full_name, "google")


# --- LinkedIn Auth ---

@router.get("/linkedin")
async def login_linkedin():
    if not LINKEDIN_CLIENT_ID:
        raise HTTPException(status_code=500, detail="LinkedIn Client ID not configured")
    
    redirect_uri = f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/api/auth/linkedin/callback"
    state = secrets.token_urlsafe(16)
    scope = "openid profile email"
    
    return RedirectResponse(
        f"https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id={LINKEDIN_CLIENT_ID}&redirect_uri={redirect_uri}&state={state}&scope={scope}"
    )

@router.get("/linkedin/callback")
async def linkedin_callback(code: str):
    if not LINKEDIN_CLIENT_ID or not LINKEDIN_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="LinkedIn config missing")

    redirect_uri = f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/api/auth/linkedin/callback"
    
    async with httpx.AsyncClient() as client:
        # 1. Exchange code for token
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": LINKEDIN_CLIENT_ID,
            "client_secret": LINKEDIN_CLIENT_SECRET
        }
        resp = await client.post("https://www.linkedin.com/oauth/v2/accessToken", data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        if resp.status_code != 200:
            logger.error(f"LinkedIn Token Error: {resp.text}")
            raise HTTPException(status_code=400, detail="Failed to retrieve token from LinkedIn")
            
        token_data = resp.json()
        access_token = token_data.get("access_token")
        
        # 2. Get user info (OpenID Connect)
        user_resp = await client.get("https://api.linkedin.com/v2/userinfo", headers={"Authorization": f"Bearer {access_token}"})
        if user_resp.status_code != 200:
             logger.error(f"LinkedIn UserInfo Error: {user_resp.text}")
             raise HTTPException(status_code=400, detail="Failed to retrieve user info from LinkedIn")
             
        user_info = user_resp.json()
        email = user_info.get("email")
        full_name = user_info.get("name") or f"{user_info.get('given_name', '')} {user_info.get('family_name', '')}".strip()
        
        return handle_social_login(email, full_name, "linkedin")

# --- Helper ---

def handle_social_login(email: str, full_name: str, provider: str):
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by identity provider")

    with engine.connect() as conn:
        # Check if exists
        user = conn.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email}).fetchone()
        
        if not user:
            # Register new user
            # Generate random password since they use OAuth
            alphabet = string.ascii_letters + string.digits
            rand_password = ''.join(secrets.choice(alphabet) for i in range(20))
            hashed = get_password_hash(rand_password)
            
            result = conn.execute(text("""
                INSERT INTO users (email, hashed_password, full_name, auth_provider)
                VALUES (:email, :pw, :name, :prov)
                RETURNING id, email, full_name, auth_provider
            """), {
                "email": email,
                "pw": hashed,
                "name": full_name or email.split("@")[0],
                "prov": provider
            })
            conn.commit()
            user = result.fetchone()
        
        # Issue Token
        conn.execute(text("UPDATE users SET last_login = NOW() WHERE email = :email"), {"email": email})
        conn.commit()
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(email)}, expires_delta=access_token_expires
        )
        
        # Redirect to Frontend with Token
        return RedirectResponse(f"{FRONTEND_URL}/auth/callback?token={access_token}")
