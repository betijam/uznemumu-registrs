from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import text
from app.core.database import engine
import logging
import hashlib
from typing import Optional
from app.routers.person import resolve_person_identifier

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
        # OPTIMIZATION: Calculate total capital only for companies where this person has a role
        # Using a correlated subquery instead of aggregating the entire persons table
        
        # Build WHERE clause to handle NULL person_code (foreign persons)
        if person_code:
            person_filter = "p.person_code = :pc AND p.person_name = :pn"
            person_params = {"pc": person_code, "pn": person_name}
        else:
            person_filter = "(p.person_code IS NULL OR p.person_code = '') AND p.person_name = :pn"
            person_params = {"pn": person_name}
        
        # STEP 1: Get base career events (without capital calculation)
        events_data = conn.execute(text(f"""
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
            WHERE {person_filter}
            ORDER BY 
                COALESCE(p.date_to, p.date_from, '9999-12-31') DESC,
                p.date_from DESC NULLS LAST
        """), person_params).fetchall()
        
        # STEP 2: Pre-fetch total capital for member companies in one query
        # This eliminates N+1 problem (correlated subquery per row)
        member_regcodes = list(set(row.regcode for row in events_data if row.role == 'member'))
        
        capital_map = {}
        if member_regcodes:
            capital_results = conn.execute(text("""
                SELECT 
                    company_regcode,
                    SUM(number_of_shares * share_nominal_value) as total_capital
                FROM persons
                WHERE company_regcode = ANY(:regcodes) AND role = 'member'
                GROUP BY company_regcode
            """), {"regcodes": member_regcodes}).fetchall()
            
            for row in capital_results:
                capital_map[row.company_regcode] = float(row.total_capital) if row.total_capital else 0
        
        # Build timeline events
        timeline_events = []
        
        for row in events_data:
            # Determine role description
            role_desc = row.position or row.role.title()
            
            # Event 1: New role (date_from)
            if row.date_from:
                event_type = "active_role" if row.date_to is None and row.company_status == 'active' else "new_role"
                is_current = row.date_to is None and row.company_status == 'active'
                
                # Build description with share percentage for members
                total_capital = capital_map.get(row.regcode, 0) if row.role == 'member' else 0
                if row.role == 'member' and row.number_of_shares and row.share_nominal_value and total_capital > 0:
                    # Calculate share percentage for description
                    try:
                         my_value = float(row.number_of_shares) * float(row.share_nominal_value)
                         if total_capital > 0:
                             share_percent = safe_float((my_value / total_capital) * 100)
                             if share_percent:
                                 role_desc = f"{role_desc} ({round(share_percent, 1)}%)"
                    except (ValueError, TypeError):
                        pass
                
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
