
import logging
from sqlalchemy import text
import math

logger = logging.getLogger(__name__)

def safe_float(val):
    """Convert value to JSON-safe float. Returns None for inf/NaN."""
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None

def bulk_fetch_financials(conn, regcodes: list, year: int) -> dict:
    """
    Fetch financial data for multiple companies in a single query.
    Returns dict: {regcode: {employees, turnover, balance}}
    """
    if not regcodes:
        return {}
    
    # Remove None values and duplicates
    valid_codes = list(set(r for r in regcodes if r is not None))
    if not valid_codes:
        return {}
    
    result = conn.execute(text("""
        SELECT company_regcode, turnover, profit, employees, total_assets
        FROM financial_reports
        WHERE company_regcode = ANY(:codes) AND year = :y
    """), {"codes": valid_codes, "y": year}).fetchall()
    
    # Convert to dict for O(1) lookup
    fin_map = {}
    for row in result:
        fin_map[row.company_regcode] = {
            "employees": row.employees,
            "turnover": safe_float(row.turnover),
            "balance": safe_float(row.total_assets)
        }
    
    return fin_map

def classify_ownership(percent: float) -> str:
    if percent is None:
        return "unknown"
    if percent > 50:
        return "linked"
    elif percent >= 25:
        return "partner"
    else:
        return "minor"  # <25%, ignored

def calculate_company_graph(conn, regcode: int, year: int = 2024):
    """
    Calculates the relationship graph for a company (Linked/Partner status).
    Returns the full result dictionary.
    """
    
    # Financial cache - will be populated by bulk fetch for performance
    _fin_cache = {}
    
    def get_financial_data(conn, related_regcode: int, year: int):
        """Get financial data from cache or single query as fallback"""
        if not related_regcode:
            return {"employees": None, "turnover": None, "balance": None}
        
        # Check cache first (populated by bulk prefetch)
        if related_regcode in _fin_cache:
            return _fin_cache[related_regcode]
        
        # Fallback to single query if not in cache
        fin = conn.execute(text("""
            SELECT turnover, profit, employees, total_assets
            FROM financial_reports
            WHERE company_regcode = :r AND year = :y
            ORDER BY year DESC LIMIT 1
        """), {"r": related_regcode, "y": year}).fetchone()
        
        result = {"employees": None, "turnover": None, "balance": None}
        if fin:
            result = {
                "employees": fin.employees,
                "turnover": safe_float(fin.turnover),
                "balance": safe_float(fin.total_assets)
            }
        _fin_cache[related_regcode] = result
        return result
    
    partners = []  # 25-50%
    linked = []    # >50%
    total_capital = 0
    
    # Get Company Info
    company_row = conn.execute(text("SELECT name, regcode FROM companies WHERE regcode=:r"), {"r": regcode}).fetchone()
    if not company_row:
        return {"status": "NOT_FOUND", "partners": [], "linked": [], "total_capital": 0, "year": year}
    
    company_name = company_row.name
    company_regcode = company_row.regcode
    
    # ===== 1. UPSTREAM: Who owns THIS company (Parents/Owners) =====
    owners = conn.execute(text("""
        SELECT 
            p.person_name,
            p.number_of_shares,
            p.share_nominal_value,
            p.legal_entity_regcode,
            p.person_code,
            c.name as legal_entity_name
        FROM persons p
        LEFT JOIN companies c ON c.regcode = p.legal_entity_regcode
        WHERE p.company_regcode = :r AND p.role = 'member'
    """), {"r": regcode}).fetchall()
    
    # PERFORMANCE: Bulk prefetch financials for all owner legal entities (N+1 fix)
    owner_regcodes = [o.legal_entity_regcode for o in owners if o.legal_entity_regcode]
    if owner_regcodes:
        _fin_cache.update(bulk_fetch_financials(conn, owner_regcodes, year))
    
    # Calculate total capital
    for owner in owners:
        shares = float(owner.number_of_shares or 0)
        nominal = float(owner.share_nominal_value or 0)
        total_capital += shares * nominal
    
    # Classify owners (both legal entities and physical persons)
    for owner in owners:
        shares = float(owner.number_of_shares or 0)
        nominal = float(owner.share_nominal_value or 0)
        owner_value = shares * nominal
        
        if total_capital > 0:
            percent = (owner_value / total_capital) * 100
        else:
            percent = None
        
        classification = classify_ownership(percent)
        
        if classification in ["partner", "linked"]:
            # Determine entity type
            is_legal_entity = owner.legal_entity_regcode is not None
            
            # Get financial data only for legal entities
            if is_legal_entity:
                financials = get_financial_data(conn, owner.legal_entity_regcode, year)
            else:
                financials = {"employees": None, "turnover": None, "balance": None}
            
            entry = {
                "name": owner.person_name,
                "regcode": owner.legal_entity_regcode,
                "relation": "owner",
                "entity_type": "legal_entity" if is_legal_entity else "physical_person",
                "ownership_percent": round(percent, 2) if percent else None,
                "share_value": owner_value,
                **financials
            }
            
            if classification == "partner":
                partners.append(entry)
            else:
                linked.append(entry)
    
    # ===== 2. DOWNSTREAM: Companies owned BY this company (Children/Subsidiaries) =====
    # Method 1: Find where this company's regcode is listed as legal_entity_regcode
    subsidiaries_by_regcode = conn.execute(text("""
        SELECT 
            c.regcode,
            c.name,
            p.number_of_shares,
            p.share_nominal_value
        FROM persons p
        JOIN companies c ON c.regcode = p.company_regcode
        WHERE p.legal_entity_regcode = :r AND p.role = 'member'
    """), {"r": company_regcode}).fetchall()
    
    # Method 2: Also check by company name (fallback for older data)
    subsidiaries_by_name = conn.execute(text("""
        SELECT 
            c.regcode,
            c.name,
            p.number_of_shares,
            p.share_nominal_value
        FROM persons p
        JOIN companies c ON c.regcode = p.company_regcode
        WHERE p.person_name = :n AND p.role = 'member' 
            AND p.legal_entity_regcode IS NULL
    """), {"n": company_name}).fetchall()
    
    # Combine and deduplicate subsidiaries
    seen_regcodes = set()
    all_subsidiaries = []
    
    for sub in subsidiaries_by_regcode:
        if sub.regcode not in seen_regcodes:
            seen_regcodes.add(sub.regcode)
            all_subsidiaries.append(sub)
    
    for sub in subsidiaries_by_name:
        if sub.regcode not in seen_regcodes:
            seen_regcodes.add(sub.regcode)
            all_subsidiaries.append(sub)
    
    # PERFORMANCE: Bulk prefetch financials for all subsidiaries (N+1 fix)
    sub_regcodes = [s.regcode for s in all_subsidiaries if s.regcode and s.regcode != regcode]
    if sub_regcodes:
        _fin_cache.update(bulk_fetch_financials(conn, sub_regcodes, year))
    
    for sub in all_subsidiaries:
        # Skip if this is the same company
        if sub.regcode == regcode:
            continue
            
        # Calculate ownership % in subsidiary
        sub_capital = conn.execute(text("""
            SELECT SUM(COALESCE(number_of_shares, 0) * COALESCE(share_nominal_value, 0)) as total
            FROM persons
            WHERE company_regcode = :r AND role = 'member'
        """), {"r": sub.regcode}).scalar() or 0
        
        our_shares = float(sub.number_of_shares or 0)
        our_nominal = float(sub.share_nominal_value or 0)
        our_value = our_shares * our_nominal
        
        if sub_capital > 0:
            percent = (our_value / float(sub_capital)) * 100
        else:
            percent = None
        
        classification = classify_ownership(percent)
        
        if classification in ["partner", "linked"]:
            financials = get_financial_data(conn, sub.regcode, year)
            
            entry = {
                "name": sub.name,
                "regcode": sub.regcode,
                "relation": "subsidiary",
                "entity_type": "legal_entity",
                "ownership_percent": round(percent, 2) if percent else None,
                "share_value": our_value,
                **financials
            }
            
            if classification == "partner":
                partners.append(entry)
            else:
                linked.append(entry)
    
    # Determine overall status
    if linked:
        status = "LINKED"
    elif partners:
        status = "PARTNER"
    else:
        status = "AUTONOMOUS"
    
    result = {
        "status": status,
        "year": year,
        "total_capital": total_capital,
        "partners": partners,
        "linked": linked
    }

    return result
