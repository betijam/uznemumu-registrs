from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import text
from etl.loader import engine
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


def hash_person_code(person_code: str) -> str:
    """Generate SHA256 hash of person code for GDPR-safe URLs."""
    if not person_code:
        return ""
    return hashlib.sha256(person_code.encode()).hexdigest()[:16]


def mask_person_code(person_code: str) -> str:
    """Mask person code for GDPR compliance (e.g., 120585-*****)."""
    if not person_code or len(person_code) < 6:
        return "******-*****"
    return f"{person_code[:6]}-*****"


def generate_person_url_id(person_code: str, person_name: str) -> str:
    """
    Generate URL-safe person identifier using hash.
    Format: 8-character hex hash (e.g., "a3f2b9c1")
    """
    # Create hash input
    hash_input = f"{person_code}|{person_name}"
    
    # Simple hash function (matching frontend)
    hash_val = 0
    for char in hash_input:
        hash_val = ((hash_val << 5) - hash_val) + ord(char)
        hash_val = hash_val & 0xFFFFFFFF  # 32-bit integer
    
    # Convert to hex (8 characters)
    hash_hex = format(abs(hash_val) & 0xFFFFFFFF, '08x')[:8]
    return hash_hex


def resolve_person_identifier(conn, identifier: str) -> Optional[str]:
    """
    Resolve person identifier to actual person_code.
    
    Identifier can be:
    - Hash format: 8-character hex hash of person_code|person_name (e.g., "a3f2b9c1")
    - Direct masked person code: DDMMYY-***** (e.g., "290800-*****")
    
    Returns: person_code or None if not found
    """
    logger.info(f"[resolve_person_identifier] Received identifier: {identifier}")
    
    # Try direct person_code first (exact match with masked code)
    result = conn.execute(text("""
        SELECT DISTINCT person_code, person_name
        FROM persons 
        WHERE person_code = :id
        LIMIT 1
    """), {"id": identifier}).fetchone()
    
    if result:
        logger.info(f"[resolve_person_identifier] Found exact match: {result.person_code}")
        return result.person_code
    
    # Try hash format (8 hex characters)
    if len(identifier) == 8 and all(c in '0123456789abcdef' for c in identifier.lower()):
        logger.info(f"[resolve_person_identifier] Trying hash format: {identifier}")
        
        # Use indexed person_hash column for fast lookup
        result = conn.execute(text("""
            SELECT person_code, person_name
            FROM persons 
            WHERE person_hash = :hash
            LIMIT 1
        """), {"hash": identifier.lower()}).fetchone()
        
        if result:
            logger.info(f"[resolve_person_identifier] HASH MATCH! person_code={result.person_code}, name={result.person_name}")
            return result.person_code
        
        logger.warning(f"[resolve_person_identifier] No hash match found for: {identifier}")
    
    logger.warning(f"[resolve_person_identifier] No match found for identifier: {identifier}")
    return None


@router.get("/person/{identifier}")
def get_person_profile(identifier: str, response: Response):
    """
    Get comprehensive person profile with all business connections.
    
    Identifier can be:
    - Hashed person_code (SHA256, 16 chars)
    - Person code fragment + slug (DDMMYY-slug)
    """
    response.headers["Cache-Control"] = "public, max-age=1800"  # 30 min cache
    
    with engine.connect() as conn:
        # Resolve identifier to actual person_code
        person_code = resolve_person_identifier(conn, identifier)
        
        if not person_code:
            raise HTTPException(status_code=404, detail="Person not found")
        
        # Get basic person info from first available record
        person_info = conn.execute(text("""
            SELECT DISTINCT
                person_name,
                person_code,
                birth_date,
                nationality,
                residence
            FROM persons
            WHERE person_code = :pc
            LIMIT 1
        """), {"pc": person_code}).fetchone()
        
        if not person_info:
            raise HTTPException(status_code=404, detail="Person not found")
        
        # Calculate KPIs
        kpi_data = conn.execute(text("""
            SELECT 
                COUNT(DISTINCT CASE 
                    WHEN c.status = 'active' AND p.date_to IS NULL 
                    THEN c.regcode 
                END) as active_companies,
                COUNT(DISTINCT CASE 
                    WHEN c.status != 'active' OR p.date_to IS NOT NULL 
                    THEN c.regcode 
                END) as historical_companies,
                COALESCE(SUM(CASE 
                    WHEN p.role IN ('officer', 'member') 
                        AND p.date_to IS NULL 
                        AND c.status = 'active'
                    THEN f.turnover 
                END), 0) as total_turnover,
                COALESCE(SUM(CASE 
                    WHEN p.role IN ('officer', 'member') 
                        AND p.date_to IS NULL 
                        AND c.status = 'active'
                    THEN f.employees 
                END), 0) as total_employees,
                COALESCE(SUM(CASE 
                    WHEN p.role = 'member' AND p.date_to IS NULL 
                    THEN p.number_of_shares * p.share_nominal_value 
                END), 0) as capital_value
            FROM persons p
            JOIN companies c ON c.regcode = p.company_regcode
            LEFT JOIN LATERAL (
                SELECT turnover, employees
                FROM financial_reports
                WHERE company_regcode = c.regcode
                ORDER BY year DESC LIMIT 1
            ) f ON true
            WHERE p.person_code = :pc
        """), {"pc": person_code}).fetchone()
        
        # Get risk indicators
        risk_data = conn.execute(text("""
            SELECT 
                COUNT(DISTINCT CASE 
                    WHEN r.risk_type = 'sanction' THEN c.regcode 
                END) > 0 as has_sanctions,
                COUNT(DISTINCT CASE 
                    WHEN r.risk_type = 'liquidation' THEN c.regcode 
                END) > 0 as has_insolvency
            FROM persons p
            JOIN companies c ON c.regcode = p.company_regcode
            LEFT JOIN risks r ON r.company_regcode = c.regcode AND r.active = true
            WHERE p.person_code = :pc AND p.date_to IS NULL
        """), {"pc": person_code}).fetchone()
        
        # Get all related companies with details
        companies = conn.execute(text("""
            SELECT
                c.regcode,
                c.name,
                c.status,
                c.nace_text,
                c.nace_section_text,
                p.role,
                p.position,
                p.number_of_shares,
                p.share_nominal_value,
                p.share_currency,
                p.date_from,
                p.date_to,
                p.rights_of_representation,
                f.turnover,
                f.profit,
                f.employees,
                f.year as financial_year
            FROM persons p
            JOIN companies c ON c.regcode = p.company_regcode
            LEFT JOIN LATERAL (
                SELECT turnover, profit, employees, year
                FROM financial_reports
                WHERE company_regcode = c.regcode
                ORDER BY year DESC LIMIT 1
            ) f ON true
            WHERE p.person_code = :pc
            ORDER BY 
                CASE WHEN p.date_to IS NULL THEN 0 ELSE 1 END,
                p.date_from DESC NULLS LAST
        """), {"pc": person_code}).fetchall()
        
        # Calculate share percentages
        companies_list = []
        for comp in companies:
            # Calculate ownership percentage for members
            share_percent = None
            if comp.role == 'member' and comp.number_of_shares and comp.share_nominal_value:
                # Get total capital for this company
                total_capital_result = conn.execute(text("""
                    SELECT SUM(number_of_shares * share_nominal_value) as total
                    FROM persons
                    WHERE company_regcode = :rc AND role = 'member'
                """), {"rc": comp.regcode}).fetchone()
                
                if total_capital_result and total_capital_result.total and total_capital_result.total > 0:
                    my_value = float(comp.number_of_shares) * float(comp.share_nominal_value)
                    share_percent = round((my_value / float(total_capital_result.total)) * 100, 2)
            
            # Determine if active
            is_active = comp.status == 'active' and comp.date_to is None
            
            companies_list.append({
                "regcode": comp.regcode,
                "name": comp.name,
                "status": comp.status,
                "nace_text": comp.nace_text,
                "nace_section_text": comp.nace_section_text,
                "role": comp.role,
                "position": comp.position,
                "share_percent": share_percent,
                "share_currency": comp.share_currency or "EUR",
                "date_from": str(comp.date_from) if comp.date_from else None,
                "date_to": str(comp.date_to) if comp.date_to else None,
                "is_active": is_active,
                "rights_of_representation": comp.rights_of_representation,
                "finances": {
                    "turnover": safe_float(comp.turnover),
                    "profit": safe_float(comp.profit),
                    "employees": comp.employees,
                    "year": comp.financial_year
                }
            })
        
        # Get collaboration network (co-occurring persons)
        network = conn.execute(text("""
            SELECT 
                p2.person_name,
                p2.person_code,
                p2.birth_date,
                COUNT(DISTINCT p2.company_regcode) as companies_together
            FROM persons p1
            JOIN persons p2 ON p1.company_regcode = p2.company_regcode 
                AND p2.person_code != p1.person_code
                AND p2.person_code IS NOT NULL
            WHERE p1.person_code = :pc
            GROUP BY p2.person_name, p2.person_code, p2.birth_date
            HAVING COUNT(DISTINCT p2.company_regcode) >= 1
            ORDER BY companies_together DESC
            LIMIT 15
        """), {"pc": person_code}).fetchall()
        
        collaboration_network = []
        for net in network:
            collaboration_network.append({
                "name": net.person_name,
                "person_id": generate_person_url_id(net.person_code, net.person_name),
                "companies_together": net.companies_together
            })
        
        # Build response
        return {
            "person_code_masked": mask_person_code(person_code),
            "person_code_hash": hash_person_code(person_code),
            "full_name": person_info.person_name,
            "birth_date": str(person_info.birth_date) if person_info.birth_date else None,
            "nationality": person_info.nationality or "LV",
            "residence": person_info.residence,
            "risk_badges": {
                "tax_debt": False,  # Would require additional data source
                "insolvency": bool(risk_data.has_insolvency) if risk_data else False,
                "sanctions": bool(risk_data.has_sanctions) if risk_data else False
            },
            "kpi": {
                "active_companies_count": int(kpi_data.active_companies) if kpi_data else 0,
                "historical_companies_count": int(kpi_data.historical_companies) if kpi_data else 0,
                "total_turnover_managed": safe_float(kpi_data.total_turnover) if kpi_data else 0,
                "total_employees_managed": int(kpi_data.total_employees) if kpi_data else 0,
                "capital_share_value": safe_float(kpi_data.capital_value) if kpi_data else 0
            },
            "companies": companies_list,
            "collaboration_network": collaboration_network
        }


@router.get("/person/{identifier}/companies")
def get_person_companies(identifier: str, status: Optional[str] = None, response: Response = None):
    """
    Get companies associated with a person.
    
    Query params:
    - status: 'active' or 'historical' to filter
    """
    if response:
        response.headers["Cache-Control"] = "public, max-age=1800"
    
    with engine.connect() as conn:
        person_code = resolve_person_identifier(conn, identifier)
        
        if not person_code:
            raise HTTPException(status_code=404, detail="Person not found")
        
        # Build query based on status filter
        where_clause = "WHERE p.person_code = :pc"
        if status == 'active':
            where_clause += " AND c.status = 'active' AND p.date_to IS NULL"
        elif status == 'historical':
            where_clause += " AND (c.status != 'active' OR p.date_to IS NOT NULL)"
        
        companies = conn.execute(text(f"""
            SELECT DISTINCT
                c.regcode, c.name, c.status, c.nace_text,
                p.role, p.position, p.date_from, p.date_to,
                p.number_of_shares, p.share_nominal_value,
                f.turnover, f.profit, f.employees
            FROM persons p
            JOIN companies c ON c.regcode = p.company_regcode
            LEFT JOIN LATERAL (
                SELECT turnover, profit, employees
                FROM financial_reports
                WHERE company_regcode = c.regcode
                ORDER BY year DESC LIMIT 1
            ) f ON true
            {where_clause}
            ORDER BY p.date_from DESC NULLS LAST
        """), {"pc": person_code}).fetchall()
        
        return {"companies": [dict(c._mapping) for c in companies]}


@router.get("/person/{identifier}/network")
def get_person_network(identifier: str, response: Response):
    """Get collaboration network - persons who appear in same companies."""
    response.headers["Cache-Control"] = "public, max-age=1800"
    
    with engine.connect() as conn:
        person_code = resolve_person_identifier(conn, identifier)
        
        if not person_code:
            raise HTTPException(status_code=404, detail="Person not found")
        
        network = conn.execute(text("""
            SELECT 
                p2.person_name,
                p2.person_code,
                p2.birth_date,
                COUNT(DISTINCT p2.company_regcode) as companies_together,
                STRING_AGG(DISTINCT c.name, ', ' ORDER BY c.name) as company_names
            FROM persons p1
            JOIN persons p2 ON p1.company_regcode = p2.company_regcode 
                AND p2.person_code != p1.person_code
                AND p2.person_code IS NOT NULL
            JOIN companies c ON c.regcode = p2.company_regcode
            WHERE p1.person_code = :pc
            GROUP BY p2.person_name, p2.person_code, p2.birth_date
            ORDER BY companies_together DESC
            LIMIT 20
        """), {"pc": person_code}).fetchall()
        
        
        network_list = []
        for n in network:
            network_list.append({
                "name": n.person_name,
                "person_id": generate_person_url_id(n.person_code, n.person_name),
                "companies_together": n.companies_together,
                "company_names": n.company_names
            })
        
        return {"network": network_list}
