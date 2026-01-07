from fastapi import Request
from typing import Optional
import os
from jose import jwt

# Load secret key from environment (should match auth.py)
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_in_prod")
ALGORITHM = "HS256"

async def check_access(request: Request) -> bool:
    """
    Determine if user has FULL access to company data.
    
    Access Rules:
    1. Logged in users (Authorization header) -> FULL ACCESS
    2. Bots (User-Agent) -> LIMITED ACCESS (Teaser)
    3. Anonymous users -> METERED ACCESS (Max 2 views)
       - View count is tracked via 'X-View-Count' header set by Frontend Middleware
    """
    
    # 1. Check Login (Authorization Header)
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            # Simple signature verification verify
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return True # Valid token -> Full Access
        except Exception:
             pass # Invalid token, fall through to metered check

    # 2. Check Bot
    user_agent = request.headers.get('user-agent', '').lower()
    if 'googlebot' in user_agent or 'bingbot' in user_agent or 'slurp' in user_agent:
        return False # Bots get Teaser only (to avoid cloaking)

    # 3. Check Metered Access (Headless/Cookie based)
    # The frontend middleware is responsible for incrementing the cookie and sending the count here.
    try:
        view_count = int(request.headers.get('X-View-Count', '0'))
    except ValueError:
        view_count = 0
        
    ALLOWED_FREE_VIEWS = 6
    
    return view_count < ALLOWED_FREE_VIEWS
