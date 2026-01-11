from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from app.core.database import engine
import logging

router = APIRouter(prefix="/waitlist", tags=["Waitlist"])
logger = logging.getLogger(__name__)

class WaitlistRequest(BaseModel):
    email: EmailStr
    source: str = "pricing_page"

@router.post("/", status_code=201)
def join_waitlist(request: WaitlistRequest):
    """
    Add an email to the waitlist
    """
    logger.info(f"Adding {request.email} to waitlist from {request.source}")
    
    query = """
    INSERT INTO waitlist_emails (email, source)
    VALUES (:email, :source)
    RETURNING id
    """
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), {"email": request.email, "source": request.source})
            conn.commit()
            row = result.fetchone()
            return {"id": row.id, "message": "Email added to waitlist"}
            
    except Exception as e:
        logger.error(f"Failed to add to waitlist: {e}")
        raise HTTPException(status_code=500, detail="Failed to join waitlist")
