from fastapi import Request
from typing import Optional
import os
import logging
from jose import jwt

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_in_prod")
ALGORITHM = "HS256"

async def check_access(request: Request) -> bool:
    """
    Determine if user has FULL access to company data.
    
    NOTE: Metered access temporarily disabled. 
    The issues are:
    1. Cookie-based counting accumulates incorrectly (values 47, 23 even in incognito)
    2. Multiple request types (SSR vs browser) getting different access levels
    
    TODO: Implement proper session-based or IP-based counting instead of cookies
    """
    # Check Login (logged in users always get full access)
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            logger.info("[ACCESS] Granted via JWT")
            return True
        except Exception:
            pass

    # Check Bot
    user_agent = request.headers.get('user-agent', '').lower()
    SEARCH_BOTS = ['googlebot', 'bingbot', 'slurp', 'duckduckbot', 'baiduspider', 'yandexbot']
    if any(bot in user_agent for bot in SEARCH_BOTS):
        logger.info("[ACCESS] Teaser for search bot")
        return False  # Search bots get teaser for SEO

    # TEMPORARY: Grant access to all non-bot users
    # Cookie-based metered access has issues with SSR architecture
    logger.info("[ACCESS] Granted (metered access disabled)")
    return True
