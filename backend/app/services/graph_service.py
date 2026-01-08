
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
        SELECT p.person_name, p.person_code, p.legal_entity_regcode, p.number_of_shares, p.share_nominal_value, p.share_currency, c.name as legal_entity_name 
    FROM persons p
        LEFT JOIN companies c ON c.regcode = p.legal_entity_regcode
        WHERE p.company_regcode = :r AND p.role = 'member'
    """), {"r": regcode}).fetchall()

    # Get Officers and UBOs for cache
    officers_rows = conn.execute(text("""
        SELECT person_name, person_code, position, rights_of_representation, 
               representation_with_at_least, date_from, birth_date
        FROM persons 
        WHERE company_regcode = :r AND role = 'officer'
    """), {"r": regcode}).fetchall()

    ubos_rows = conn.execute(text("""
        SELECT person_name, person_code, nationality, residence, date_from, birth_date
        FROM persons 
        WHERE company_regcode = :r AND role = 'ubo'
    """), {"r": regcode}).fetchall()

    # Format for cache
    cached_officers = []
    for o in officers_rows:
        cached_officers.append({
            "name": o.person_name, "person_code": o.person_code, "position": o.position,
            "rights_of_representation": o.rights_of_representation,
            "representation_with_at_least": int(o.representation_with_at_least) if o.representation_with_at_least else None,
            "registered_on": str(o.date_from) if o.date_from else None,
            "birth_date": str(o.birth_date) if o.birth_date else None
        })

    cached_ubos = []
    for u in ubos_rows:
        cached_ubos.append({
            "name": u.person_name, "person_code": u.person_code, "nationality": u.nationality,
            "residence": u.residence, "registered_on": str(u.date_from) if u.date_from else None,
            "birth_date": str(u.birth_date) if u.birth_date else None
        })

    cached_members = []

    
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
        
        # Add to all members list
        cached_members.append({
            "name": owner.person_name, 
            "person_code": owner.person_code,
            "legal_entity_regcode": int(owner.legal_entity_regcode) if owner.legal_entity_regcode else None,
            "number_of_shares": int(shares) if shares else None,
            "share_value": owner_value,
            "share_currency": "EUR", # Default
            "percent": round(percent, 2) if percent is not None else 0,
            "date_from": None, # Not selected in original query, acceptable for cache
            "birth_date": None # Not selected in original query
        })

        
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
        "linked": linked,
        "officers": cached_officers,
        "members": cached_members,
        "ubos": cached_ubos
    }

    return result

def calculate_company_graphs_batch(conn, regcodes: list, year: int = 2024) -> dict:
    """
    Calculates relationship graphs for multiple companies in bulk.
    Significantly reduces N+1 queries by pre-fetching data.
    """
    if not regcodes:
        return {}
        
    results = {}
    
    # 1. Fetch Company Info (Name, Regcode)
    companies_rows = conn.execute(text("SELECT name, regcode FROM companies WHERE regcode = ANY(:r)"), {"r": regcodes}).fetchall()
    companies_map = {row.regcode: row.name for row in companies_rows}
    
    # Initialize results with defaults
    for r in regcodes:
        if r not in companies_map:
            results[r] = {"status": "NOT_FOUND", "partners": [], "linked": [], "total_capital": 0, "year": year}
        else:
            results[r] = {
                "status": "AUTONOMOUS", 
                "partners": [], 
                "linked": [], 
                "total_capital": 0, 
                "year": year
            }

    if not companies_map:
        return results

    # 2. Bulk Fetch All Persons (Owners, Officers, UBOs)
    persons_rows = conn.execute(text("""
        SELECT 
            p.company_regcode,
            p.person_name,
            p.number_of_shares,
            p.share_nominal_value,
            p.legal_entity_regcode,
            p.person_code,
            p.role,
            p.position,
            p.rights_of_representation,
            p.representation_with_at_least,
            p.date_from,
            p.birth_date,
            p.nationality,
            p.residence,
            p.share_currency
        FROM persons p
        WHERE p.company_regcode = ANY(:r)
    """), {"r": list(companies_map.keys())}).fetchall()
    
    # Organize by company
    persons_by_company = {r: [] for r in regcodes}
    all_related_regcodes = set()
    
    for row in persons_rows:
        if row.company_regcode in persons_by_company:
            persons_by_company[row.company_regcode].append(row)
        if row.role == 'member' and row.legal_entity_regcode:
            all_related_regcodes.add(row.legal_entity_regcode)
            
    # Keep owners_rows variable for compatibility with downstream logic if needed, 
    # but we will iterate persons_by_company for main logic
    owners_rows = [p for p in persons_rows if p.role == 'member']
            
    # 3. Bulk Fetch Subsidiaries (Downstream)
    # 3a. By Legal Entity Regcode
    subs_by_regcode_rows = conn.execute(text("""
        SELECT 
            p.legal_entity_regcode as parent_regcode,
            c.regcode as sub_regcode,
            c.name as sub_name,
            p.number_of_shares,
            p.share_nominal_value
        FROM persons p
        JOIN companies c ON c.regcode = p.company_regcode
        WHERE p.legal_entity_regcode = ANY(:r) AND p.role = 'member'
    """), {"r": list(companies_map.keys())}).fetchall()

    # 3b. By Company Name (fallback)
    company_names = list(companies_map.values())
    subs_by_name_rows = []
    if company_names:
        subs_by_name_rows = conn.execute(text("""
            SELECT 
                p.person_name as parent_name,
                c.regcode as sub_regcode,
                c.name as sub_name,
                p.number_of_shares,
                p.share_nominal_value
            FROM persons p
            JOIN companies c ON c.regcode = p.company_regcode
            WHERE p.person_name = ANY(:n) AND p.role = 'member' 
                AND p.legal_entity_regcode IS NULL
        """), {"n": company_names}).fetchall()
    
    # Map name back to regcode for 3b
    name_to_regcode = {v: k for k, v in companies_map.items()}
    
    subsidiaries_by_company = {r: [] for r in regcodes}
    
    for row in subs_by_regcode_rows:
        if row.parent_regcode in subsidiaries_by_company:
             subsidiaries_by_company[row.parent_regcode].append(row)
             all_related_regcodes.add(row.sub_regcode)

    for row in subs_by_name_rows:
        if row.parent_name in name_to_regcode:
            parent_reg = name_to_regcode[row.parent_name]
            subsidiaries_by_company[parent_reg].append(row)
            all_related_regcodes.add(row.sub_regcode)
            
    # 4. Bulk Fetch Financials for ALL related entities
    fin_cache = bulk_fetch_financials(conn, list(all_related_regcodes), year)
    
    # 5. Process Each Company (Part 1: Owners)
    # We need to collect all sub regcodes to bulk fetch their total capitals
    subs_to_check_capital = set()
    for regcode in companies_map:
        subs = subsidiaries_by_company.get(regcode, [])
        for sub in subs:
            if sub.sub_regcode != regcode:
                 subs_to_check_capital.add(sub.sub_regcode)
                 
    # Bulk fetch sub capitals
    sub_capitals = {}
    if subs_to_check_capital:
        cap_rows = conn.execute(text("""
            SELECT company_regcode, SUM(COALESCE(number_of_shares, 0) * COALESCE(share_nominal_value, 0)) as total
            FROM persons
            WHERE company_regcode = ANY(:r) AND role = 'member'
            GROUP BY company_regcode
        """), {"r": list(subs_to_check_capital)}).fetchall()
        sub_capitals = {row.company_regcode: row.total for row in cap_rows}
    
    # 6. Final Logic
    for regcode in companies_map:
        company_result = results[regcode]
        
        # --- Process Owners ---
        # --- Process Persons (Owners, Officers, UBOs) ---
        all_persons = persons_by_company.get(regcode, [])
        owners = [p for p in all_persons if p.role == 'member']
        officers = [p for p in all_persons if p.role == 'officer']
        ubos = [p for p in all_persons if p.role == 'ubo']

        # Format Officers
        cached_officers = []
        for o in officers:
            cached_officers.append({
                "name": o.person_name, "person_code": o.person_code, "position": o.position,
                "rights_of_representation": o.rights_of_representation,
                "representation_with_at_least": int(o.representation_with_at_least) if o.representation_with_at_least else None,
                "registered_on": str(o.date_from) if o.date_from else None,
                "birth_date": str(o.birth_date) if o.birth_date else None
            })
        company_result['officers'] = cached_officers

        # Format UBOs
        cached_ubos = []
        for u in ubos:
            cached_ubos.append({
                "name": u.person_name, "person_code": u.person_code, "nationality": u.nationality,
                "residence": u.residence, "registered_on": str(u.date_from) if u.date_from else None,
                "birth_date": str(u.birth_date) if u.birth_date else None
            })
        company_result['ubos'] = cached_ubos

        # Process Members (Owners)
        cached_members = []

        total_capital = 0
        for o in owners:
            s = float(o.number_of_shares or 0)
            n = float(o.share_nominal_value or 0)
            total_capital += s * n
        
        company_result['total_capital'] = total_capital
        
        for owner in owners:
            s = float(owner.number_of_shares or 0)
            n = float(owner.share_nominal_value or 0)
            val = s * n
            percent = (val / total_capital * 100) if total_capital > 0 else None
            classification = classify_ownership(percent)
            
            if classification in ["partner", "linked"]:
                is_legal = owner.legal_entity_regcode is not None
                fin = fin_cache.get(owner.legal_entity_regcode, {"employees": None, "turnover": None, "balance": None}) if is_legal else {"employees": None, "turnover": None, "balance": None}
                
                entry = {
                    "name": owner.person_name,
                    "regcode": owner.legal_entity_regcode,
                    "relation": "owner",
                    "entity_type": "legal_entity" if is_legal else "physical_person",
                    "ownership_percent": round(percent, 2) if percent else None,
                    "share_value": val,
                    **fin
                }
                
                # Add to full members list
                cached_members.append({
                    "name": owner.person_name, 
                    "person_code": owner.person_code,
                    "legal_entity_regcode": int(owner.legal_entity_regcode) if owner.legal_entity_regcode else None,
                    "number_of_shares": int(s) if s else None,
                    "share_value": val,
                    "share_currency": owner.share_currency or "EUR",
                    "percent": round(percent, 2) if percent is not None else 0,
                    "date_from": str(owner.date_from) if owner.date_from else None,
                    "birth_date": str(owner.birth_date) if owner.birth_date else None
                })

                if classification == "partner":
                    company_result["partners"].append(entry)
                else:
                    company_result["linked"].append(entry)
                    
        company_result['members'] = cached_members
                    
        # --- Process Subsidiaries ---
        subs = subsidiaries_by_company.get(regcode, [])
        processed_subs = set()
        
        for sub in subs:
            if sub.sub_regcode in processed_subs or sub.sub_regcode == regcode:
                continue
            processed_subs.add(sub.sub_regcode)
            
            sub_total_cap = float(sub_capitals.get(sub.sub_regcode, 0))
            
            my_shares = float(sub.number_of_shares or 0)
            my_nominal = float(sub.share_nominal_value or 0)
            my_val = my_shares * my_nominal
            
            percent = (my_val / sub_total_cap * 100) if sub_total_cap > 0 else None
            classification = classify_ownership(percent)
            
            if classification in ["partner", "linked"]:
                fin = fin_cache.get(sub.sub_regcode, {"employees": None, "turnover": None, "balance": None})
                
                entry = {
                    "name": sub.sub_name,
                    "regcode": sub.sub_regcode,
                    "relation": "subsidiary",
                    "entity_type": "legal_entity",
                    "ownership_percent": round(percent, 2) if percent else None,
                    "share_value": my_val,
                    **fin
                }
                
                if classification == "partner":
                    company_result["partners"].append(entry)
                else:
                    company_result["linked"].append(entry)
                    
        # Determine overall status
        if company_result["linked"]:
            company_result["status"] = "LINKED"
        elif company_result["partners"]:
            company_result["status"] = "PARTNER"
            
    return results
