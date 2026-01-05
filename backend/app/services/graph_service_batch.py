
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

    # 2. Bulk Fetch Owners (Upstream)
    owners_rows = conn.execute(text("""
        SELECT 
            p.company_regcode,
            p.person_name,
            p.number_of_shares,
            p.share_nominal_value,
            p.legal_entity_regcode,
            p.person_code
        FROM persons p
        WHERE p.company_regcode = ANY(:r) AND p.role = 'member'
    """), {"r": list(companies_map.keys())}).fetchall()
    
    # Organize owners by company
    owners_by_company = {r: [] for r in regcodes}
    all_related_regcodes = set()
    
    for row in owners_rows:
        owners_by_company[row.company_regcode].append(row)
        if row.legal_entity_regcode:
            all_related_regcodes.add(row.legal_entity_regcode)
            
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
            # Avoid duplicates if found by regcode already?
            # It's okay, we'll dedupe logic in loop usually, or just append.
            # Simplified: just append, will filter distinct subs later if needed.
            subsidiaries_by_company[parent_reg].append(row)
            all_related_regcodes.add(row.sub_regcode)
            
    # 4. Bulk Fetch Financials for ALL related entities
    fin_cache = bulk_fetch_financials(conn, list(all_related_regcodes), year)
    
    # 5. Process Each Company
    for regcode in companies_map:
        company_result = results[regcode]
        
        # --- Process Owners ---
        owners = owners_by_company.get(regcode, [])
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
                if classification == "partner":
                    company_result["partners"].append(entry)
                else:
                    company_result["linked"].append(entry)
                    
        # --- Process Subsidiaries ---
        subs = subsidiaries_by_company.get(regcode, [])
        # Deduplicate subs by regcode
        processed_subs = set()
        
        for sub in subs:
            if sub.sub_regcode in processed_subs or sub.sub_regcode == regcode:
                continue
            processed_subs.add(sub.sub_regcode)
            
            # We need Total Capital of the SUB to calculate % we own
            # This is an N+1 query if we don't calculate it. 
            # Optimization: approximates or fetches. 
            # For exact correctness, we need the sub's total capital.
            # FETCHING SUB TOTAL CAPITAL IN BULK:
            # We can do this with one query before this loop.
            pass 
        
    # Extra Step: Bulk Fetch Sub Capitals
    # We need total capital for all subs found
    all_sub_regcodes = list(all_related_regcodes)
    sub_capitals = {}
    if all_sub_regcodes:
        cap_rows = conn.execute(text("""
            SELECT company_regcode, SUM(COALESCE(number_of_shares, 0) * COALESCE(share_nominal_value, 0)) as total
            FROM persons
            WHERE company_regcode = ANY(:r) AND role = 'member'
            GROUP BY company_regcode
        """), {"r": all_sub_regcodes}).fetchall()
        sub_capitals = {row.company_regcode: row.total for row in cap_rows}

    # Resume Processing Subsidiaries
    for regcode in companies_map:
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
                    results[regcode]["partners"].append(entry)
                else:
                    results[regcode]["linked"].append(entry)
                    
        # Determine overall status
        if results[regcode]["linked"]:
            results[regcode]["status"] = "LINKED"
        elif results[regcode]["partners"]:
            results[regcode]["status"] = "PARTNER"
            
    return results
