"""
Favorites router for user watchlist functionality
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, text
from typing import List, Any
from datetime import datetime
import logging

from app.core.database import engine
from app.routers.auth import get_current_user
# from app.models.user import User  # This module does not exist
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
    current_user: Any = Depends(get_current_user)
):
    """Add an entity to user's favorites"""
    try:
        with engine.connect() as conn:
            # Check if already exists
            existing = conn.execute(
                text("""
                SELECT id FROM favorites 
                WHERE user_id = :user_id 
                AND entity_id = :entity_id 
                AND entity_type = :entity_type
                """),
                {
                    "user_id": current_user.id,
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
            result = conn.execute(
                text("""
                INSERT INTO favorites (user_id, entity_id, entity_type, entity_name)
                VALUES (:user_id, :entity_id, :entity_type, :entity_name)
                RETURNING id, entity_id, entity_type, entity_name, created_at
                """),
                {
                    "user_id": current_user.id,
                    "entity_id": favorite.entity_id,
                    "entity_type": favorite.entity_type,
                    "entity_name": favorite.entity_name
                }
            )
            conn.commit()
            
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add favorite"
        )


@router.delete("/{entity_id}")
async def remove_favorite(
    entity_id: str,
    entity_type: str = "company",
    current_user: Any = Depends(get_current_user)
):
    """Remove an entity from user's favorites"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                DELETE FROM favorites 
                WHERE user_id = :user_id 
                AND entity_id = :entity_id 
                AND entity_type = :entity_type
                RETURNING id
                """),
                {
                    "user_id": current_user.id,
                    "entity_id": entity_id,
                    "entity_type": entity_type
                }
            )
            conn.commit()
            
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove favorite"
        )


@router.get("/", response_model=List[FavoriteResponse])
async def get_favorites(
    current_user: Any = Depends(get_current_user)
):
    """Get all user's favorites"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                SELECT id, entity_id, entity_type, entity_name, created_at
                FROM favorites
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                """),
                {"user_id": current_user.id}
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
    current_user: Any = Depends(get_current_user)
):
    """Check if an entity is in user's favorites"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                SELECT id FROM favorites 
                WHERE user_id = :user_id 
                AND entity_id = :entity_id 
                AND entity_type = :entity_type
                """),
                {
                    "user_id": current_user.id,
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
