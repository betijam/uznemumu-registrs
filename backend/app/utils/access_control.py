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
    
    Priority:
    1. Valid JWT -> Full access
    2. Search engine bot -> Teaser only (for SEO safety)
    3. Anonymous user -> Check view count (5 free views)
    """
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

    # 2. Check Bot (only well-known search engine bots)
    user_agent = request.headers.get('user-agent', '').lower()
    logger.info(f"[ACCESS] User-Agent: {user_agent[:80]}...")
    
    # Only block known search engine bots, NOT generic user agents
    SEARCH_BOTS = ['googlebot', 'bingbot', 'slurp', 'duckduckbot', 'baiduspider', 'yandexbot']
    if any(bot in user_agent for bot in SEARCH_BOTS):
        logger.info("[ACCESS] Denied for search bot (Teaser only)")
        return False

    # 3. Check Metered Access
    view_count_header = request.headers.get('X-View-Count')
    logger.info(f"[ACCESS] X-View-Count header: '{view_count_header}'")
    
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
