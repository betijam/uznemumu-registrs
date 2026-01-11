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

class FeedbackRequest(BaseModel):
    feedback_text: str
    email: EmailStr | None = None
    source: str = "feedback_button"

@router.post("/", status_code=201)
def join_waitlist(request: WaitlistRequest):
    """
    Add an email to the newsletter waitlist
    """
    logger.info(f"Adding {request.email} to waitlist from {request.source}")
    
    try:
        with engine.connect() as conn:
            # Use ON CONFLICT to handle duplicates gracefully
            result = conn.execute(text("""
                INSERT INTO waitlist_emails (email, source)
                VALUES (:email, :source)
                ON CONFLICT (email, source) DO UPDATE 
                SET created_at = NOW()
                RETURNING id
            """), {"email": request.email, "source": request.source})
            conn.commit()
            row = result.fetchone()
            return {"id": row[0], "message": "Email added to waitlist"}
            
    except Exception as e:
        logger.error(f"Failed to add to waitlist: {e}")
        raise HTTPException(status_code=500, detail="Failed to join waitlist")

@router.post("/feedback", status_code=201)
def submit_feedback(request: FeedbackRequest):
    """
    Submit feedback or feature request
    """
    logger.info(f"Feedback submitted from {request.email or 'anonymous'}: {request.feedback_text[:50]}...")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                INSERT INTO feedback_submissions (feedback_text, email, source)
                VALUES (:feedback, :email, :source)
                RETURNING id
            """), {
                "feedback": request.feedback_text,
                "email": request.email,
                "source": request.source
            })
            conn.commit()
            row = result.fetchone()
            return {"id": row[0], "message": "Feedback submitted successfully"}
            
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")
