from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import text
from app.core.database import engine
import logging
import hashlib
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)


def safe_float(val):
    """Convert value to JSON-safe float. Returns None for inf/NaN."""
    if val is None:
        return None
    try:
        import math
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


# ... [keeping all existing helper functions: hash_person_code, mask_person_code, generate_person_url_id, resolve_person_identifier]
# ... [keeping all existing endpoints: get_person_profile, get_person_companies, search_persons, get_person_network]


@router.get("/person/{identifier}/career-timeline")
def get_career_timeline(identifier: str, limit: int = 10, offset: int = 0, response: Response = None):
    """
    Get chronological career timeline for a person.
    Returns events sorted by date (newest first).
    
    Event types:
    - new_role: Person joined company (date_from)
    - exit: Person left company (date_to)
    - active_role: Current active role (date_to IS NULL)
    - liquidation: Company was liquidated during person's tenure
    """
    if response:
        response.headers["Cache-Control"] = "public, max-age=1800"
    
    with engine.connect() as conn:
        # Resolve identifier to actual person_code and person_name
        resolved = resolve_person_identifier(conn, identifier)
        
        if not resolved:
            raise HTTPException(status_code=404, detail="Person not found")
        
        person_code, person_name = resolved
        logger.info(f"[get_career_timeline] Resolved {identifier} to {person_code}, {person_name}")
        
        # Get all career events from persons table
        # We create events for: date_from (new_role), date_to (exit), and active roles
        events_data = conn.execute(text("""
            SELECT 
                p.company_regcode as regcode,
                c.name as company_name,
                c.status as company_status,
                p.role,
                p.position,
                p.date_from,
                p.date_to,
                p.number_of_shares,
                p.share_nominal_value
            FROM persons p
            JOIN companies c ON p.company_regcode = c.regcode
            WHERE p.person_code = :pc AND p.person_name = :pn
            ORDER BY 
                COALESCE(p.date_to, p.date_from, '9999-12-31') DESC,
                p.date_from DESC NULLS LAST
        """), {"pc": person_code, "pn": person_name}).fetchall()
        
        # Build timeline events
        timeline_events = []
        
        for row in events_data:
            # Determine role description
            role_desc = row.position or row.role.title()
            
            # Event 1: New role (date_from)
            if row.date_from:
                event_type = "active_role" if row.date_to is None and row.company_status == 'active' else "new_role"
                is_current = row.date_to is None and row.company_status == 'active'
                
                # Build description
                if row.role == 'member' and row.number_of_shares and row.share_nominal_value:
                    # Calculate share percentage for description
                    total_capital_result = conn.execute(text("""
                        SELECT SUM(number_of_shares * share_nominal_value) as total
                        FROM persons
                        WHERE company_regcode = :rc AND role = 'member'
                    """), {"rc": row.regcode}).fetchone()
                    
                    if total_capital_result and total_capital_result.total and total_capital_result.total > 0:
                        my_value = float(row.number_of_shares) * float(row.share_nominal_value)
                        share_percent = safe_float((my_value / float(total_capital_result.total)) * 100)
                        if share_percent:
                            role_desc = f"{role_desc} ({round(share_percent, 1)}%)"
                
                timeline_events.append({
                    "date": str(row.date_from),
                    "year": row.date_from.year if row.date_from else None,
                    "type": event_type,
                    "company_name": row.company_name,
                    "regcode": row.regcode,
                    "description": role_desc,
                    "is_current": is_current
                })
            
            # Event 2: Exit (date_to)
            if row.date_to:
                # Check if company was liquidated
                event_type = "liquidation" if row.company_status == 'liquidated' else "exit"
                
                timeline_events.append({
                    "date": str(row.date_to),
                    "year": row.date_to.year if row.date_to else None,
                    "type": event_type,
                    "company_name": row.company_name,
                    "regcode": row.regcode,
                    "description": role_desc,
                    "is_current": False
                })
        
        # Sort by date descending (newest first)
        timeline_events.sort(key=lambda x: x["date"] if x["date"] else "1900-01-01", reverse=True)
        
        # Apply pagination
        total = len(timeline_events)
        paginated_events = timeline_events[offset:offset + limit]
        
        return {
            "events": paginated_events,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total
        }
