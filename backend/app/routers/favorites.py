"""
Favorites router for user watchlist functionality
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, text
from typing import List, Any, Optional
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


@router.post("", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
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


@router.get("", response_model=List[FavoriteResponse])
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

class DashboardFavoriteResponse(BaseModel):
    id: str
    entity_id: str
    entity_type: str
    entity_name: str
    created_at: datetime
    # Extra fields
    regcode: Optional[int] = None
    status: Optional[str] = None
    turnover: Optional[float] = None
    profit: Optional[float] = None
    employees: Optional[int] = None
    company_count: Optional[int] = None # For persons


@router.get("/dashboard-list", response_model=List[DashboardFavoriteResponse])
async def get_dashboard_favorites(
    current_user: Any = Depends(get_current_user)
):
    """Get rich list of user's favorites for dashboard"""
    try:
        with engine.connect() as conn:
            # Fetch favorites
            favs = conn.execute(
                text("""
                SELECT id, entity_id, entity_type, entity_name, created_at
                FROM favorites
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                """),
                {"user_id": current_user.id}
            ).fetchall()
            
            if not favs:
                return []

            # Separate IDs by type
            company_ids = [int(f.entity_id) for f in favs if f.entity_type == 'company' and f.entity_id.isdigit()]
            person_hashes = [f.entity_id for f in favs if f.entity_type == 'person']

            # Fetch Company Data
            company_map = {}
            if company_ids:
                query = text("""
                    SELECT 
                        c.regcode, 
                        c.status,
                        fr.turnover,
                        fr.profit,
                        fr.employees
                    FROM companies c
                    LEFT JOIN LATERAL (
                        SELECT turnover, profit, employees
                        FROM financial_reports
                        WHERE company_regcode = c.regcode
                          AND year = (
                              SELECT MAX(year) 
                              FROM financial_reports 
                              WHERE company_regcode = c.regcode
                          )
                        LIMIT 1
                    ) fr ON true
                    WHERE c.regcode = ANY(:ids)
                """)
                rows = conn.execute(query, {"ids": company_ids}).fetchall()
                for r in rows:
                    company_map[str(r.regcode)] = {
                        "regcode": r.regcode,
                        "status": r.status,
                        "turnover": r.turnover,
                        "profit": r.profit,
                        "employees": r.employees
                    }

            results = []
            for f in favs:
                entry = {
                    "id": str(f.id),
                    "entity_id": f.entity_id,
                    "entity_type": f.entity_type,
                    "entity_name": f.entity_name,
                    "created_at": f.created_at
                }
                
                if f.entity_type == 'company' and f.entity_id in company_map:
                    data = company_map[f.entity_id]
                    entry.update({
                        "regcode": data["regcode"],
                        "status": data["status"],
                        "turnover": data["turnover"],
                        "profit": data["profit"],
                        "employees": data["employees"]
                    })
                
                results.append(DashboardFavoriteResponse(**entry))
            
            return results
        
    except Exception as e:
        logger.error(f"Error fetching dashboard favorites: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch favorites"
        )
