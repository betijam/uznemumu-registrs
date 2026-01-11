"""
Favorites router for user watchlist functionality
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/favorites", tags=["favorites"])


# Pydantic models
class FavoriteCreate(BaseModel):
    entity_id: str
    entity_type: str  # 'company' or 'person'
    entity_name: str


class FavoriteResponse(BaseModel):
    id: str
    entity_id: str
    entity_type: str
    entity_name: str
    created_at: datetime


@router.post("/", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    favorite: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add an entity to user's favorites"""
    try:
        # Check if already exists
        existing = db.execute(
            """
            SELECT id FROM favorites 
            WHERE user_id = :user_id 
            AND entity_id = :entity_id 
            AND entity_type = :entity_type
            """,
            {
                "user_id": str(current_user.id),
                "entity_id": favorite.entity_id,
                "entity_type": favorite.entity_type
            }
        ).fetchone()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Entity already in favorites"
            )
        
        # Insert new favorite
        result = db.execute(
            """
            INSERT INTO favorites (user_id, entity_id, entity_type, entity_name)
            VALUES (:user_id, :entity_id, :entity_type, :entity_name)
            RETURNING id, entity_id, entity_type, entity_name, created_at
            """,
            {
                "user_id": str(current_user.id),
                "entity_id": favorite.entity_id,
                "entity_type": favorite.entity_type,
                "entity_name": favorite.entity_name
            }
        )
        db.commit()
        
        row = result.fetchone()
        return FavoriteResponse(
            id=str(row[0]),
            entity_id=row[1],
            entity_type=row[2],
            entity_name=row[3],
            created_at=row[4]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding favorite: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add favorite"
        )


@router.delete("/{entity_id}")
async def remove_favorite(
    entity_id: str,
    entity_type: str = "company",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove an entity from user's favorites"""
    try:
        result = db.execute(
            """
            DELETE FROM favorites 
            WHERE user_id = :user_id 
            AND entity_id = :entity_id 
            AND entity_type = :entity_type
            RETURNING id
            """,
            {
                "user_id": str(current_user.id),
                "entity_id": entity_id,
                "entity_type": entity_type
            }
        )
        db.commit()
        
        if result.fetchone() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Favorite not found"
            )
        
        return {"message": "Favorite removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing favorite: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove favorite"
        )


@router.get("/", response_model=List[FavoriteResponse])
async def get_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user's favorites"""
    try:
        result = db.execute(
            """
            SELECT id, entity_id, entity_type, entity_name, created_at
            FROM favorites
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            """,
            {"user_id": str(current_user.id)}
        )
        
        favorites = []
        for row in result:
            favorites.append(FavoriteResponse(
                id=str(row[0]),
                entity_id=row[1],
                entity_type=row[2],
                entity_name=row[3],
                created_at=row[4]
            ))
        
        return favorites
        
    except Exception as e:
        logger.error(f"Error fetching favorites: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch favorites"
        )


@router.get("/check/{entity_id}")
async def check_favorite(
    entity_id: str,
    entity_type: str = "company",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if an entity is in user's favorites"""
    try:
        result = db.execute(
            """
            SELECT id FROM favorites 
            WHERE user_id = :user_id 
            AND entity_id = :entity_id 
            AND entity_type = :entity_type
            """,
            {
                "user_id": str(current_user.id),
                "entity_id": entity_id,
                "entity_type": entity_type
            }
        )
        
        is_favorite = result.fetchone() is not None
        return {"is_favorite": is_favorite}
        
    except Exception as e:
        logger.error(f"Error checking favorite: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check favorite status"
        )
