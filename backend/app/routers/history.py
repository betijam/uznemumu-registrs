"""
History router for tracking user's recently viewed entities
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from datetime import datetime
import logging

from app.core.database import engine
from app.core.auth import get_current_user
from app.models.user import User
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["history"])


# Pydantic models
class RecentView(BaseModel):
    entity_id: str
    entity_type: str
    entity_name: str
    viewed_at: datetime


def log_view_history(
    user_id: str,
    entity_id: str,
    entity_type: str,
    entity_name: str,
    db: Session
):
    """
    Background task to log entity view.
    Uses UPSERT to prevent duplicates - updates timestamp if already exists.
    """
    try:
        with engine.connect() as conn:
            # PostgreSQL UPSERT using ON CONFLICT
            conn.execute(
                text("""
                INSERT INTO recent_views (user_id, entity_id, entity_type, entity_name, viewed_at)
                VALUES (:user_id, :entity_id, :entity_type, :entity_name, NOW())
                ON CONFLICT (user_id, entity_id, entity_type)
                DO UPDATE SET 
                    viewed_at = NOW(),
                    entity_name = EXCLUDED.entity_name
                """),
                {
                    "user_id": user_id,
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "entity_name": entity_name
                }
            )
            conn.commit()
            logger.info(f"Logged view: user={user_id}, entity={entity_id}")
        
    except Exception as e:
        logger.error(f"Error logging view history: {e}")


@router.get("/recent", response_model=List[RecentView])
async def get_recent_views(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get user's recently viewed entities"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                SELECT entity_id, entity_type, entity_name, viewed_at
                FROM recent_views
                WHERE user_id = :user_id
                ORDER BY viewed_at DESC
                LIMIT :limit
                """),
                {
                    "user_id": current_user.id,
                    "limit": limit
                }
            )
            
            views = []
            for row in result:
                views.append(RecentView(
                    entity_id=row[0],
                    entity_type=row[1],
                    entity_name=row[2],
                    viewed_at=row[3]
                ))
            
            return views
        
    except Exception as e:
        logger.error(f"Error fetching recent views: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch recent views"
        )
