from fastapi import Request
from typing import Optional
import os
import logging
from jose import jwt

logger = logging.getLogger(__name__)

# Load secret key from environment (should match auth.py)
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_in_prod")
ALGORITHM = "HS256"

async def check_access(request: Request) -> bool:
    """
    Determine if user has FULL access to company data.
    
    TEMPORARY: Always returning True to debug data visibility issue.
    Re-enable metered access after verifying data shows correctly.
    """
    # TEMPORARY: Force full access to debug data issue
    logger.info("[ACCESS] TEMPORARY: Granting full access for debugging")
    return True
    
    # --- ORIGINAL LOGIC BELOW (disabled for debugging) ---
    # 1. Check Login (Authorization Header)
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            logger.info("[ACCESS] Granted via valid JWT")
            return True
        except Exception as e:
            logger.warning(f"[ACCESS] Invalid JWT: {e}")
            pass

    # 2. Check Bot
    user_agent = request.headers.get('user-agent', '').lower()
    if 'googlebot' in user_agent or 'bingbot' in user_agent or 'slurp' in user_agent:
        logger.info("[ACCESS] Denied for bot (Teaser only)")
        return False

    # 3. Check Metered Access
    view_count_header = request.headers.get('X-View-Count')
    logger.info(f"[ACCESS] X-View-Count header value: '{view_count_header}'")
    
    if view_count_header is None:
        logger.info("[ACCESS] Granted (no X-View-Count header)")
        return True
    
    try:
        view_count = int(view_count_header)
    except ValueError:
        view_count = 0
        
    ALLOWED_FREE_VIEWS = 5
    result = view_count < ALLOWED_FREE_VIEWS
    logger.info(f"[ACCESS] View count: {view_count}, Limit: {ALLOWED_FREE_VIEWS}, Access: {result}")
    return result
