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
    
    TEMPORARILY: Always return True to restore functionality.
    NOTE: Proper metered access will be implemented later with a different architecture
    that doesn't conflict with Next.js caching.
    """
    return True
