from fastapi import APIRouter, HTTPException, Response, Request, Depends, Query
from sqlalchemy import text
from app.core.database import engine
import logging
import hashlib
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)

# Helper to check access level (Duplicated from companies to avoid circular imports)
from app.utils.access_control import check_access

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
    
    Normalizes name by:
    1. Lowercase
    2. Split into parts
    3. Sort parts alphabetically
    4. Join back
    
    Uses ONLY first 6 chars of person_code (DDMMYY) to match frontend logic
    and support masked data.
    """
    # Normalize name
    normalized_name = " ".join(sorted(person_name.lower().split()))
    
    # Use only first 6 chars of person_code (DDMMYY)
    code_fragment = person_code[:6] if person_code else ""
    
    # Create hash input
    hash_input = f"{code_fragment}|{normalized_name}"
    
    # Simple hash function (matching frontend)
    hash_val = 0
    for char in hash_input:
        hash_val = ((hash_val << 5) - hash_val) + ord(char)
        hash_val = hash_val & 0xFFFFFFFF  # 32-bit integer
    
    # Convert to hex (8 characters)
    hash_hex = format(abs(hash_val) & 0xFFFFFFFF, '08x')[:8]
    return hash_hex


def resolve_person_identifier(conn, identifier: str) -> Optional[tuple]:
    """
    Resolve person identifier to actual person_code and person_name.
    
    Identifier can be:
    - Hash format: 8-character hex hash of person_code|person_name (e.g., "a3f2b9c1")
    - Direct masked person code: DDMMYY-***** (e.g., "290800-*****")
    
    Returns: (person_code, person_name) tuple or None if not found
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
        logger.info(f"[resolve_person_identifier] Found exact match: {result.person_code}, {result.person_name}")
        return (result.person_code, result.person_name)
    
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
            return (result.person_code, result.person_name)
        
        logger.warning(f"[resolve_person_identifier] No hash match found for: {identifier}")
    
    logger.warning(f"[resolve_person_identifier] No match found for identifier: {identifier}")
    
    # Try legacy person_code-slug format (DDMMYY-name-slug)
    # This is useful if old links exist or if hash lookup fails
    if '-' in identifier:
        parts = identifier.split('-')
        if len(parts) >= 2:
            fragment = parts[0]
            # Check if it's DDMMYY format (digits)
            if len(fragment) == 6 and fragment.isdigit():
                name_slug = '-'.join(parts[1:])
                logger.info(f"[resolve_person_identifier] Trying legacy format check: fragment={fragment}, slug={name_slug}")
                
                # Find candidates with matching person_code prefix
                candidates = conn.execute(text("""
                    SELECT DISTINCT person_code, person_name
                    FROM persons 
                    WHERE person_code LIKE :pattern
                """), {"pattern": f"{fragment}%"}).fetchall()
                
                # Check for match with normalized names
                for cand in candidates:
                    # Normalize candidate name using same logic as hash generation
                    # Lowercase -> split -> sort -> join
                    normalized_cand_name = " ".join(sorted(cand.person_name.lower().split()))
                    
                    # Create slug from normalized name
                    import re
                    cand_slug = re.sub(r'[^a-z0-9]+', '-', normalized_cand_name).strip('-')
                    
                    # Normalize input slug too (just in case)
                    normalized_input_slug = re.sub(r'[^a-z0-9]+', '-', name_slug.lower()).strip('-')
                    
                    # Compare
                    # Also try comparing sorted parts of the slug
                    cand_slug_parts = sorted(cand_slug.split('-'))
                    input_slug_parts = sorted(normalized_input_slug.split('-'))
                    
                    if cand_slug == normalized_input_slug or cand_slug_parts == input_slug_parts:
                        logger.info(f"[resolve_person_identifier] Legacy/Name Match found! {cand.person_code}, {cand.person_name}")
                        return (cand.person_code, cand.person_name)

    return None


@router.get("/person/{identifier}")
async def get_person_profile(identifier: str, response: Response, request: Request):
    """
    Get comprehensive person profile with all business connections.
    
    Identifier can be:
    - Hashed person_code (SHA256, 16 chars)
    - Person code fragment + slug (DDMMYY-slug)
    """
    response.headers["Cache-Control"] = "no-store"
    
    # Check Access
    has_full_access = await check_access(request)
    
    with engine.connect() as conn:
        # Resolve identifier to actual person_code and person_name
        resolved = resolve_person_identifier(conn, identifier)
        
        if not resolved:
            raise HTTPException(status_code=404, detail="Person not found")
        
        person_code, person_name = resolved
        logger.info(f"[get_person_profile] Resolved {identifier} to person_code={person_code}, person_name={person_name}")
        
        # Get basic person info from first available record
        person_info = conn.execute(text("""
            SELECT DISTINCT
                person_name,
                person_code,
                birth_date,
                nationality,
                residence
            FROM persons
            WHERE person_code = :pc AND person_name = :pn
            LIMIT 1
        """), {"pc": person_code, "pn": person_name}).fetchone()
        
        if not person_info:
            raise HTTPException(status_code=404, detail="Person not found")

        # Get all related companies
        companies = conn.execute(text("""
            SELECT 
                p.company_regcode as regcode,
                c.name,
                c.status,
                p.role,
                p.position,
                p.date_from,
                p.date_to,
                p.number_of_shares,
                p.share_nominal_value,
                p.share_currency,
                p.rights_of_representation,
                fr.turnover,
                fr.profit,
                fr.employees,
                fr.equity as balance,
                fr.year as financial_year,
                c.type_text,
                c.nace_text,
                c.nace_section_text
            FROM persons p
            JOIN companies c ON p.company_regcode = c.regcode
            LEFT JOIN financial_reports fr ON c.regcode = fr.company_regcode 
                AND fr.year = (SELECT MAX(year) FROM financial_reports WHERE company_regcode = c.regcode)
            WHERE p.person_code = :pc AND p.person_name = :pn
            ORDER BY 
                CASE WHEN p.date_to IS NULL THEN 0 ELSE 1 END,
                fr.turnover DESC NULLS LAST
        """), {"pc": person_code, "pn": person_name}).fetchall()
        
        # Calculate KPIs in Python to avoid double counting multiple roles
        active_companies_count = 0
        historical_companies_count = 0
        total_turnover = 0.0
        total_employees = 0
        capital_value = 0.0
        
        # Track processed regcodes to avoid double counting financials
        processed_financial_regcodes = set()
        
        for comp in companies:
            # Status counts (Active/Historical)
            # A company is "active for person" if company is active AND person's role is active (date_to is None)
            is_active_relationship = comp.status == 'active' and comp.date_to is None
            
            if is_active_relationship:
                active_companies_count += 1
            elif comp.status != 'active' or comp.date_to is not None:
                # If relationship ended OR company is not active, it's historical
                # Note: This simple logic might count a company as both if they have multiple roles (one active, one historical)
                # But typically we want distinct companies. 
                # Let's refine: We'll count distinct companies later if strictly needed, 
                # but for "Active Companies" vs "Historical Companies" usually we mean current state of affiliation.
                # If I am active in Company A, it's an active company for me.
                # If I was distinct board member in Company A (ended) but am now Member (active), it is Active.
                pass

        # Re-iterate or use sets for distinct counts to be precise
        unique_active_regcodes = set()
        unique_historical_regcodes = set()
        
        for comp in companies:
            is_active_role = comp.date_to is None
            is_active_company = comp.status == 'active'
            
            if is_active_role and is_active_company:
                unique_active_regcodes.add(comp.regcode)
            else:
                # Only add to historical if NOT in active (e.g. if I have one active role and one old role, I am effectively Active)
                pass
                
        # Fill historical: any company where I have a record but NO active role/company status
        # This requires checking if regcode is in unique_active_regcodes
        current_companies_set = set(c.regcode for c in companies)
        for rc in current_companies_set:
            if rc not in unique_active_regcodes:
                unique_historical_regcodes.add(rc)
                
        active_companies_count = len(unique_active_regcodes)
        historical_companies_count = len(unique_historical_regcodes)

        # Financials (Turnover/Employees) - Only for Active Companies
        # Count ONCE per company (avoid double counting if person has multiple roles in same company)
        for comp in companies:
            if comp.regcode in unique_active_regcodes and comp.regcode not in processed_financial_regcodes:
                # Include turnover and employees for ALL active companies where person is involved
                if comp.turnover:
                    try:
                        val = float(comp.turnover)
                        if val != val: # Check for NaN (val != val is a common Python trick, or use math.isnan)
                             val = 0
                        total_turnover += val
                        logger.info(f"  + Company {comp.regcode}: {val}")
                    except (ValueError, TypeError):
                        pass
                if comp.employees:
                    total_employees += comp.employees
                
                processed_financial_regcodes.add(comp.regcode)
        
        logger.info(f"Person {person_code}: Total Turnover (accumulated): {total_turnover}")
        
        # Capital Value - Sum of (shares * nominal) for all ACTIVE member roles
        # Note: A person can be a member multiple times? Usually once per company.
        # But if they have multiple member entries (rare), we sum them.
        for comp in companies:
            is_active_role = comp.date_to is None
            if comp.role == 'member' and is_active_role:
                 if comp.number_of_shares and comp.share_nominal_value:
                     try:
                         val = float(comp.number_of_shares) * float(comp.share_nominal_value)
                         capital_value += val
                     except:
                         pass

        
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
            WHERE p.person_code = :pc AND p.person_name = :pn AND p.date_to IS NULL
        """), {"pc": person_code, "pn": person_name}).fetchone()
        
        
        # Calculate share percentages and format company list
        companies_list = []
        # Group companies by regcode
        companies_map = {}
        
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
                    raw_percent = (my_value / float(total_capital_result.total)) * 100
                    share_percent = safe_float(raw_percent)
                    if share_percent is not None:
                        share_percent = round(share_percent, 2)
            
            # Determine if this specific role is active
            role_is_active = comp.status == 'active' and comp.date_to is None

            # Create new company entry if not exists
            if comp.regcode not in companies_map:
                companies_map[comp.regcode] = {
                    "regcode": comp.regcode,
                    "name": comp.name,
                    "status": comp.status,
                    "nace_text": comp.nace_text,
                    "nace_section_text": comp.nace_section_text,
                    "roles": [],
                    "finances": {
                        "turnover": safe_float(comp.turnover),
                        "profit": safe_float(comp.profit),
                        "employees": comp.employees,
                        "year": comp.financial_year
                    },
                    "is_active": False # Will be set to true if ANY role is active
                }
            
            # Add role to the list
            companies_map[comp.regcode]["roles"].append({
                "type": comp.role,
                "position": comp.position,
                "share_percent": share_percent,
                "share_currency": comp.share_currency or "EUR",
                "date_from": str(comp.date_from) if comp.date_from else None,
                "date_to": str(comp.date_to) if comp.date_to else None,
                "is_active": role_is_active,
                "rights_of_representation": comp.rights_of_representation
            })

            # Update company overall active status
            if role_is_active:
                companies_map[comp.regcode]["is_active"] = True

        companies_list = list(companies_map.values())
        
        # Get collaboration network (co-occurring persons)
        # Added STRING_AGG for company names
        # Get collaboration network (co-occurring persons)
        # Fetch raw data and aggregate in Python to handle name normalization (e.g. "Janis Berzins" vs "Berzins Janis")
        network_raw = conn.execute(text("""
            SELECT DISTINCT
                p2.person_name,
                p2.person_code,
                c.name as company_name,
                c.regcode as company_regcode
            FROM persons p1
            JOIN persons p2 ON p1.company_regcode = p2.company_regcode 
                AND (p2.person_code != p1.person_code OR p2.person_name != p1.person_name)
                AND p2.person_code IS NOT NULL
            JOIN companies c ON c.regcode = p2.company_regcode
            WHERE p1.person_code = :pc AND p1.person_name = :pn
        """), {"pc": person_code, "pn": person_name}).fetchall()
        
        # Aggregate in Python with normalization
        network_map = {}
        
        # Normalize target person name to exclude self even if name is reversed
        target_name_parts = person_name.lower().split()
        target_name_parts.sort()
        target_norm_key = "-".join(target_name_parts)

        for row in network_raw:
            # Normalize name for grouping: lowercase, split, sort parts
            # This merges "Oļegs Smirnovs" and "Smirnovs Oļegs"
            name_parts = row.person_name.lower().split()
            name_parts.sort()
            
            norm_key = "-".join(name_parts)
            
            # EXCLUDE SELF: Check if this person matches the target person
            if norm_key == target_norm_key:
                continue

            if norm_key not in network_map:
                network_map[norm_key] = {
                    "name": row.person_name, # Keep one display name (first encountered)
                    "person_code": row.person_code,
                    "companies": set(),
                    "company_names": set()
                }
            
            network_map[norm_key]["companies"].add(row.company_regcode)
            network_map[norm_key]["company_names"].add(row.company_name)
            
        # Convert to list and sort
        collaboration_network = []
        for key, data in network_map.items():
            count = len(data["companies"])
            company_names_str = ", ".join(sorted(list(data["company_names"])))
            
            collaboration_network.append({
                "name": data["name"],
                "person_id": generate_person_url_id(data["person_code"], data["name"]),
                "companies_together": count,
                "company_names": company_names_str
            })
            
        # Sort by count desc
        collaboration_network.sort(key=lambda x: x["companies_together"], reverse=True)
        collaboration_network = collaboration_network[:15]
        
        # Build response
        return {
            "person_code_masked": mask_person_code(person_code),
            "person_code_hash": hash_person_code(person_code),
            "full_name": person_info.person_name,
            "birth_date": str(person_info.birth_date) if person_info.birth_date else None,
            "nationality": person_info.nationality or "LV",
            "residence": person_info.residence,
            "risk_badges": {
                "tax_debt": False,
                "insolvency": bool(risk_data.has_insolvency) if risk_data else False,
                "sanctions": bool(risk_data.has_sanctions) if risk_data else False
            },
            "kpi": {
                "active_companies_count": active_companies_count,
                "historical_companies_count": historical_companies_count,
                "total_turnover_managed": safe_float(total_turnover),
                "total_employees_managed": total_employees,
                "capital_share_value": safe_float(capital_value)
            },
            "companies": companies_list,
            "collaboration_network": collaboration_network,
            "has_full_access": has_full_access
        }


@router.get("/person/{identifier}/companies")
def get_person_companies(identifier: str, status: Optional[str] = None, response: Response = None):
    """
    Get companies associated with a person.
    
    Query params:
    - status: 'active' or 'historical' to filter
    """
    if response:
        response.headers["Cache-Control"] = "no-store"
    
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
        
@router.get("/search/persons")
def search_persons(q: str, limit: int = 20, offset: int = 0):
    """
    Search for persons by name with fuzzy matching.
    Returns distinct person_code + person_name combinations with company counts.
    """
    if not q or len(q) < 2:
        return {"persons": [], "total": 0}
    
    with engine.connect() as conn:
        # Search with fuzzy matching (ILIKE for case-insensitive partial match)
        search_pattern = f"%{q}%"
        
        # Get distinct persons with company counts
        # We group by person_code, person_name, person_hash to ensure unique persons
        results = conn.execute(text("""
            SELECT 
                p.person_code,
                p.person_name,
                p.person_hash,
                COUNT(DISTINCT p.company_regcode) as company_count,
                STRING_AGG(DISTINCT p.role, ', ' ORDER BY p.role) as roles,
                MAX(p.birth_date) as birth_date
            FROM persons p
            WHERE p.person_name ILIKE :pattern
                AND p.person_code IS NOT NULL
            GROUP BY p.person_code, p.person_name, p.person_hash
            ORDER BY company_count DESC, p.person_name
            LIMIT :limit OFFSET :offset
        """), {"pattern": search_pattern, "limit": limit, "offset": offset}).fetchall()
        
        # Get total count for pagination
        total_result = conn.execute(text("""
            SELECT COUNT(DISTINCT (p.person_code, p.person_name))
            FROM persons p
            WHERE p.person_name ILIKE :pattern
                AND p.person_code IS NOT NULL
        """), {"pattern": search_pattern}).fetchone()
        
        total = total_result[0] if total_result else 0
        
        # Format results
        persons = []
        for row in results:
            # Use hash for person_id
            person_id = row.person_hash
            
            # If hash is missing (should stick to migration), generate it
            # generate_person_url_id now includes name normalization
            if not person_id:
                person_id = generate_person_url_id(row.person_code, row.person_name)
            
            persons.append({
                "person_id": person_id,
                "name": row.person_name,
                "person_code": f"{row.person_code[:6]}-*****" if len(row.person_code) >= 6 else row.person_code,
                "company_count": row.company_count,
                "roles": row.roles.split(", ") if row.roles else [],
                "birth_date": str(row.birth_date) if row.birth_date else None
            })
        
        return {
            "persons": persons,
            "total": total,
            "limit": limit,
            "offset": offset
        }



@router.get("/person/{identifier}/network")
def get_person_network(identifier: str, response: Response):
    """Get collaboration network - persons who appear in same companies."""
    response.headers["Cache-Control"] = "public, max-age=1800"
    
    with engine.connect() as conn:
        resolved = resolve_person_identifier(conn, identifier)
        
        if not resolved:
            raise HTTPException(status_code=404, detail="Person not found")
        
        person_code, person_name = resolved
        
        network = conn.execute(text("""
            SELECT 
                p2.person_name,
                p2.person_code,
                p2.birth_date,
                COUNT(DISTINCT p2.company_regcode) as companies_together,
                STRING_AGG(DISTINCT c.name, ', ' ORDER BY c.name) as company_names
            FROM persons p1
            JOIN persons p2 ON p1.company_regcode = p2.company_regcode 
                AND (p2.person_code != p1.person_code OR p2.person_name != p1.person_name)
                AND p2.person_code IS NOT NULL
            JOIN companies c ON c.regcode = p2.company_regcode
            WHERE p1.person_code = :pc AND p1.person_name = :pn
            GROUP BY p2.person_name, p2.person_code, p2.birth_date
            ORDER BY companies_together DESC
            LIMIT 20
        """), {"pc": person_code, "pn": person_name}).fetchall()
        
        
        network_list = []
        for n in network:
            network_list.append({
                "name": n.person_name,
                "person_id": generate_person_url_id(n.person_code, n.person_name),
                "companies_together": n.companies_together,
                "company_names": n.company_names
            })
        
        return {"network": network_list}


@router.get("/person/{identifier}/career-timeline")
def get_career_timeline(identifier: str, limit: int = 10, offset: int = 0, response: Response = None):
    """
    Get chronological career timeline for a person.
    Returns events sorted by date (newest first).
    
    Event types:
    - new_role: Person joined company (date_from)
    - exit: Person left company (date_to)
    - active_role: Currently active role (date_to IS NULL)
    - liquidation: Company was liquidated during person's tenure
    """
    if response:
        response.headers["Cache-Control"] = "public, max-age=1800"
    
    with engine.connect() as conn:
        # Resolve identifier
        resolved = resolve_person_identifier(conn, identifier)
        
        if not resolved:
            raise HTTPException(status_code=404, detail="Person not found")
        
        person_code, person_name = resolved
        logger.info(f"[get_career_timeline] Generating timeline for {person_code}, {person_name}")
        
        # Get all career events
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
                
                # Add share percentage if member
                if row.role == 'member' and row.number_of_shares and row.share_nominal_value:
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
        
        # Sort by date descending
        timeline_events.sort(key=lambda x: x["date"] if x["date"] else "1900-01-01", reverse=True)
        
        # Pagination
        total = len(timeline_events)
        paginated_events = timeline_events[offset:offset + limit]
        
        return {
            "events": paginated_events,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total
        }


# ============================================================================
# SITEMAP ENDPOINTS
# ============================================================================

@router.get("/persons/sitemap-info")
def get_persons_sitemap_info():
    """
    Get total count of unique persons for sitemap pagination.
    """
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(DISTINCT person_code) FROM persons")).scalar()
        return {"total": count}

@router.get("/persons/sitemap-ids")
def get_persons_sitemap_ids(page: int = Query(1, ge=1), limit: int = Query(50000, le=50000)):
    """
    Get batch of person identifiers for sitemap generation.
    Returns generated URL identifiers (hash).
    """
    offset = (page - 1) * limit
    
    with engine.connect() as conn:
        query = text("""
            SELECT DISTINCT person_code, person_name
            FROM persons
            ORDER BY person_code
            LIMIT :limit OFFSET :offset
        """)
        
        rows = conn.execute(query, {"limit": limit, "offset": offset}).fetchall()
        
        results = []
        for r in rows:
            identifier = generate_person_url_id(r.person_code, r.person_name)
            results.append({
                "identifier": identifier,
                "updated_at": None 
            })
        
        return {
            "page": page,
            "limit": limit,
            "ids": results
        }
