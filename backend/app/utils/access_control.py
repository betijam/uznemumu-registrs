from fastapi import Request
from typing import Optional
import os
import logging
from jose import jwt

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_in_prod")
ALGORITHM = "HS256"

# Configuration
ALLOWED_FREE_VIEWS = 5  

async def check_access(request: Request) -> bool:
    """
    Determine if user has FULL access to company data.
    
    Priority:
    1. Valid JWT -> Full access (logged in users)
    2. Search engine bot -> Teaser only (for SEO safety)
    3. Anonymous user -> Check view count (first N views free)
    """
    # 1. Check Login (logged in users always get full access)
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            logger.info("[ACCESS] Granted via JWT")
            return True
        except Exception as e:
            logger.debug(f"[ACCESS] JWT decode failed: {e}")
            pass

    # 2. Check Bot (only block known search engine bots)
    user_agent = request.headers.get('user-agent', '').lower()
    SEARCH_BOTS = ['googlebot', 'bingbot', 'slurp', 'duckduckbot', 'baiduspider', 'yandexbot']
    if any(bot in user_agent for bot in SEARCH_BOTS):
        logger.info(f"[ACCESS] Teaser for search bot: {user_agent[:50]}")
        return False

    # 3. Check Metered Access (view count from frontend)
    view_count_header = request.headers.get('X-View-Count')
    
    if view_count_header is None or view_count_header == '':
        # No header = grant access (enables SSR without cookies)
        logger.info("[ACCESS] Granted (no view count header)")
        return True
    
    try:
        view_count = int(view_count_header)
    except ValueError:
        view_count = 0
    
    has_access = view_count < ALLOWED_FREE_VIEWS
    logger.info(f"[ACCESS] View count: {view_count}, Limit: {ALLOWED_FREE_VIEWS}, Access: {has_access}")
    return has_access
