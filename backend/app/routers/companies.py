from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import text
from etl.loader import engine
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

def calculate_company_size(employees: int, turnover: float, assets: float) -> str:
    """
    Calculate company size according to EU standards (SME definition)
    
    Categories:
    - Mikro: <10 employees AND (≤2M€ turnover OR ≤2M€ balance sheet)
    - Mazs: <50 employees AND (≤10M€ turnover OR ≤10M€ balance sheet)
    - Vidējs: <250 employees AND (≤50M€ turnover OR ≤43M€ balance sheet)
    - Liels: ≥250 employees OR (>50M€ turnover OR >43M€ balance sheet)
    """
    # Handle None/missing values
    employees = employees or 0
    turnover = turnover or 0
    assets = assets or 0
    
    # Check if we have sufficient data
    if employees == 0 and turnover == 0 and assets == 0:
        return None  # No data available
    
    # EU SME Classification
    if employees < 10 and (turnover <= 2_000_000 or assets <= 2_000_000):
        return "Mikro"
    elif employees < 50 and (turnover <= 10_000_000 or assets <= 10_000_000):
        return "Mazs"
    elif employees < 250 and (turnover <= 50_000_000 or assets <= 43_000_000):
        return "Vidējs"
    else:
        return "Liels"


@router.get("/companies/{regcode}")
def get_company_details(regcode: int, response: Response):
    # Cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    
    with engine.connect() as conn:
        # 1. Main Info
        res = conn.execute(text("SELECT * FROM companies WHERE regcode = :r"), {"r": regcode}).fetchone()
        if not res:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company = {
            "regcode": res.regcode,
            "name": res.name,
            "address": res.address,
            "registration_date": str(res.registration_date),
            "status": res.status,
            "sepa_identifier": res.sepa_identifier,  # Deprecated, use pvn_number
            # PVN (VAT) Taxpayer Info
            "pvn_number": res.pvn_number if hasattr(res, 'pvn_number') else None,
            "is_pvn_payer": res.is_pvn_payer if hasattr(res, 'is_pvn_payer') else False,
            # Company Size
            "company_size_badge": res.company_size_badge,
            "latest_size_year": res.latest_size_year if hasattr(res, 'latest_size_year') else None,
            "size_changed_recently": res.size_changed_recently if hasattr(res, 'size_changed_recently') else False,
            # NACE Industry Classification
            "nace_code": res.nace_code,
            "nace_text": res.nace_text,
            "nace_section": res.nace_section,
            "nace_section_text": res.nace_section_text,
            "employee_count": res.employee_count,
            "tax_data_year": res.tax_data_year
        }
        
        # 2. Financial History (All years with growth calculation + ratios)
        fin_rows = conn.execute(text("""
            SELECT year, turnover, profit, employees, cash_balance,
                   current_ratio, quick_ratio, cash_ratio,
                   net_profit_margin, roe, roa, debt_to_equity, equity_ratio, ebitda
            FROM financial_reports 
            WHERE company_regcode = :r 
            ORDER BY year DESC
        """), {"r": regcode}).fetchall()
        
        financial_history = []
        prev_turnover = None
        prev_profit = None
        
        # Process in reverse to calculate growth correctly
        fin_list = list(fin_rows)
        fin_list.reverse()  # Oldest first for growth calc
        
        for f in fin_list:
            row = {
                "year": f.year,
                "turnover": float(f.turnover) if f.turnover else None,
                "profit": float(f.profit) if f.profit else None,
                "employees": f.employees,
                "cash_balance": float(f.cash_balance) if f.cash_balance else None,
                "turnover_growth": None,
                "profit_growth": None,
                # Financial Ratios
                "current_ratio": float(f.current_ratio) if f.current_ratio else None,
                "quick_ratio": float(f.quick_ratio) if f.quick_ratio else None,
                "cash_ratio": float(f.cash_ratio) if f.cash_ratio else None,
                "net_profit_margin": float(f.net_profit_margin) if f.net_profit_margin else None,
                "roe": float(f.roe) if f.roe else None,
                "roa": float(f.roa) if f.roa else None,
                "debt_to_equity": float(f.debt_to_equity) if f.debt_to_equity else None,
                "equity_ratio": float(f.equity_ratio) if f.equity_ratio else None,
                "ebitda": float(f.ebitda) if f.ebitda else None
            }
            
            # Calculate growth %
            if prev_turnover and f.turnover and prev_turnover != 0:
                row["turnover_growth"] = round(((float(f.turnover) - prev_turnover) / abs(prev_turnover)) * 100, 1)
            if prev_profit and f.profit and prev_profit != 0:
                row["profit_growth"] = round(((float(f.profit) - prev_profit) / abs(prev_profit)) * 100, 1)
            
            prev_turnover = float(f.turnover) if f.turnover else None
            prev_profit = float(f.profit) if f.profit else None
            financial_history.append(row)
        
        # Reverse back to newest first for display
        financial_history.reverse()
        company["financial_history"] = financial_history
        
        # Latest finances for summary cards
        if financial_history:
            latest = financial_history[0]
            company["finances"] = {
                "turnover": latest["turnover"],
                "profit": latest["profit"],
                "employees": latest["employees"],
                "year": latest["year"],
                "turnover_growth": latest["turnover_growth"],
                "profit_growth": latest["profit_growth"]
            }
        else:
            company["finances"] = {"turnover": None, "profit": None, "employees": None, "year": None}
        
        # 3. Tax History (VID data with salary calculations)
        tax_rows = conn.execute(text("""
            SELECT year, total_tax_paid, labor_tax_iin, social_tax_vsaoi, avg_employees, nace_code
            FROM tax_payments 
            WHERE company_regcode = :r 
            ORDER BY year DESC
        """), {"r": regcode}).fetchall()
        
        tax_history = []
        VSAOI_RATE = 0.3409  # 34.09% darba devēja VSAOI likme
        
        for t in tax_rows:
            row = {
                "year": t.year,
                "total_tax_paid": float(t.total_tax_paid) if t.total_tax_paid else None,
                "labor_tax_iin": float(t.labor_tax_iin) if t.labor_tax_iin else None,
                "social_tax_vsaoi": float(t.social_tax_vsaoi) if t.social_tax_vsaoi else None,
                "avg_employees": float(t.avg_employees) if t.avg_employees else None,
                "nace_code": t.nace_code,
                "avg_gross_salary": None,
                "avg_net_salary": None
            }
            
            # Calculate average gross salary: (VSAOI / VSAOI_RATE) / employees / 12
            if t.social_tax_vsaoi and t.avg_employees and float(t.avg_employees) > 0:
                vsaoi = float(t.social_tax_vsaoi)
                employees = float(t.avg_employees)
                gross_yearly = vsaoi / VSAOI_RATE
                gross_monthly = gross_yearly / employees / 12
                row["avg_gross_salary"] = round(gross_monthly, 2)
                
                # Approximate net salary calculation:
                # 1. VSAOI employee part (10.5%): gross * 0.105
                # 2. IIN (20% after VSAOI deduction): (gross - VSAOI_employee) * 0.20
                # Net = Gross - VSAOI_employee - IIN
                vsaoi_employee = gross_monthly * 0.105
                iin = (gross_monthly - vsaoi_employee) * 0.20
                net_monthly = gross_monthly - vsaoi_employee - iin
                row["avg_net_salary"] = round(net_monthly, 2)
            
            tax_history.append(row)
        
        company["tax_history"] = tax_history
        
        # 4. VID Rating
        rating_res = conn.execute(text("""
            SELECT rating_grade, rating_explanation, last_evaluated_on
            FROM company_ratings 
            WHERE company_regcode = :r
        """), {"r": regcode}).fetchone()
        
        if rating_res:
            company["rating"] = {
                "grade": rating_res.rating_grade,
                "explanation": rating_res.rating_explanation,
                "date": str(rating_res.last_evaluated_on) if rating_res.last_evaluated_on else None
            }
        else:
            company["rating"] = None
        
        # 5. Risks (Active) - Enhanced with detailed categorization
        risks = conn.execute(text("""
            SELECT risk_type, description, start_date, risk_score,
                   sanction_program, sanction_list_text, legal_base_url,
                   suspension_code, suspension_grounds,
                   measure_type, institution_name, case_number,
                   liquidation_type, liquidation_grounds
            FROM risks 
            WHERE company_regcode = :r AND active = TRUE
            ORDER BY risk_score DESC, start_date DESC
        """), {"r": regcode}).fetchall()
        
        # Calculate total risk score
        total_risk_score = sum(r.risk_score or 0 for r in risks)
        
        # Categorize risks
        risks_by_type = {
            'sanctions': [],
            'liquidations': [],
            'suspensions': [],
            'securing_measures': []
        }
        
        for r in risks:
            risk_obj = {
                "type": r.risk_type,
                "description": r.description,
                "date": str(r.start_date) if r.start_date else None,
                "score": r.risk_score
            }
            
            # Add type-specific fields
            if r.risk_type == 'sanction':
                risk_obj.update({
                    "program": r.sanction_program,
                    "list_text": r.sanction_list_text,
                    "legal_base_url": r.legal_base_url
                })
                risks_by_type['sanctions'].append(risk_obj)
            elif r.risk_type == 'liquidation':
                risk_obj.update({
                    "liquidation_type": r.liquidation_type,
                    "grounds": r.liquidation_grounds
                })
                risks_by_type['liquidations'].append(risk_obj)
            elif r.risk_type == 'suspension':
                risk_obj.update({
                    "suspension_code": r.suspension_code,
                    "grounds": r.suspension_grounds
                })
                risks_by_type['suspensions'].append(risk_obj)
            elif r.risk_type == 'securing_measure':
                risk_obj.update({
                    "measure_type": r.measure_type,
                    "institution": r.institution_name,
                    "case_number": r.case_number
                })
                risks_by_type['securing_measures'].append(risk_obj)
        
        company["risks"] = risks_by_type
        company["total_risk_score"] = total_risk_score
        company["risk_level"] = (
            "CRITICAL" if total_risk_score >= 100 else
            "HIGH" if total_risk_score >= 50 else
            "MEDIUM" if total_risk_score >= 30 else
            "LOW" if total_risk_score > 0 else
            "NONE"
        )
        
        # 6. Persons (Structured: UBOs, Members, Officers)
        persons = conn.execute(text("""
            SELECT person_name, role, share_percent, date_from, 
                   position, rights_of_representation, representation_with_at_least,
                   number_of_shares, share_nominal_value, share_currency, legal_entity_regcode,
                   nationality, residence
            FROM persons
            WHERE company_regcode = :r
        """), {"r": regcode}).fetchall()
        
        # Calculate total share capital for member % calculation
        total_capital = sum(
            (float(p.number_of_shares or 0) * float(p.share_nominal_value or 0))
            for p in persons if p.role == 'member'
        )
        
        # Structure into 3 sections
        ubos = []
        members = []
        officers = []
        
        for p in persons:
            if p.role == 'ubo':
                ubos.append({
                    "name": p.person_name,
                    "nationality": p.nationality,
                    "residence": p.residence,
                    "registered_on": str(p.date_from) if p.date_from else None
                })
            elif p.role == 'member':
                share_value = float(p.number_of_shares or 0) * float(p.share_nominal_value or 0)
                percent = (share_value / total_capital * 100) if total_capital > 0 else 0
                members.append({
                    "name": p.person_name,
                    "legal_entity_regcode": int(p.legal_entity_regcode) if p.legal_entity_regcode else None,
                    "number_of_shares": int(p.number_of_shares) if p.number_of_shares else None,
                    "share_value": share_value,
                    "share_currency": p.share_currency or "EUR",
                    "percent": round(percent, 2),
                    "date_from": str(p.date_from) if p.date_from else None
                })
            elif p.role == 'officer':
                officers.append({
                    "name": p.person_name,
                    "position": p.position,
                    "rights_of_representation": p.rights_of_representation,
                    "representation_with_at_least": int(p.representation_with_at_least) if p.representation_with_at_least else None,
                    "registered_on": str(p.date_from) if p.date_from else None
                })
        
        company["ubos"] = ubos
        company["members"] = members
        company["officers"] = officers
        company["total_capital"] = total_capital

        # 7. Procurements
        procurements = conn.execute(text("""
            SELECT authority_name, subject, amount, contract_date
            FROM procurements
            WHERE winner_regcode = :r
            ORDER BY contract_date DESC LIMIT 10
        """), {"r": regcode}).fetchall()
        
        company["procurements"] = [
            {
                "authority": p.authority_name,
                "subject": p.subject,
                "amount": float(p.amount) if p.amount else None,
                "date": str(p.contract_date)
            }
            for p in procurements
        ]
        
        # 8. Company Size (read from cached DB column for performance)
        # Note: Updated periodically via update_company_sizes.py script
        company["company_size"] = res.company_size_badge
        
        return company


# ================================================================================
# COMPREHENSIVE LINKED ENTITY DETECTION (EU SME Rules)
# ================================================================================

def get_ownership_percent(conn, owner_regcode_or_person_code: str, target_regcode: int, is_legal_entity: bool = True) -> float:
    """Calculate ownership percentage of one entity in another"""
    if is_legal_entity:
        result = conn.execute(text("""
            SELECT 
                SUM(p.number_of_shares * p.share_nominal_value) as owner_value,
                (SELECT SUM(number_of_shares * share_nominal_value) 
                 FROM persons WHERE company_regcode = :target AND role = 'member') as total_capital
            FROM persons p
            WHERE p.company_regcode = :target 
              AND p.role = 'member'
              AND p.legal_entity_regcode = :owner
        """), {"target": target_regcode, "owner": owner_regcode_or_person_code}).fetchone()
    else:
        result = conn.execute(text("""
            SELECT 
                SUM(p.number_of_shares * p.share_nominal_value) as owner_value,
                (SELECT SUM(number_of_shares * share_nominal_value) 
                 FROM persons WHERE company_regcode = :target AND role = 'member') as total_capital
            FROM persons p
            WHERE p.company_regcode = :target 
              AND p.role = 'member'
              AND p.person_code = :owner
        """), {"target": target_regcode, "owner": owner_regcode_or_person_code}).fetchone()
    
    if result and result.owner_value and result.total_capital and float(result.total_capital) > 0:
        return (float(result.owner_value) / float(result.total_capital)) * 100
    return 0.0


def find_direct_owners(conn, regcode: int) -> list:
    """Find all direct owners (legal entities) with >50% control"""
    result = conn.execute(text("""
        WITH company_capital AS (
            SELECT SUM(number_of_shares * share_nominal_value) as total
            FROM persons WHERE company_regcode = :r AND role = 'member'
        )
        SELECT 
            p.legal_entity_regcode as owner_regcode,
            p.person_name as owner_name,
            SUM(p.number_of_shares * p.share_nominal_value) as owner_value,
            cc.total as total_capital,
            CASE WHEN cc.total > 0 
                THEN (SUM(p.number_of_shares * p.share_nominal_value) / cc.total) * 100 
                ELSE 0 
            END as ownership_percent
        FROM persons p, company_capital cc
        WHERE p.company_regcode = :r 
          AND p.role = 'member'
          AND p.legal_entity_regcode IS NOT NULL
        GROUP BY p.legal_entity_regcode, p.person_name, cc.total
        HAVING (SUM(p.number_of_shares * p.share_nominal_value) / NULLIF(cc.total, 0)) > 0.5
    """), {"r": regcode}).fetchall()
    
    return [{"regcode": r.owner_regcode, "name": r.owner_name, "percent": float(r.ownership_percent)} for r in result]


def find_direct_subsidiaries(conn, regcode: int, company_name: str) -> list:
    """Find all direct subsidiaries (>50% owned by this company)"""
    # By regcode
    by_regcode = conn.execute(text("""
        SELECT DISTINCT c.regcode, c.name
        FROM persons p
        JOIN companies c ON c.regcode = p.company_regcode
        WHERE p.legal_entity_regcode = :r AND p.role = 'member'
    """), {"r": regcode}).fetchall()
    
    # By name (fallback)
    by_name = conn.execute(text("""
        SELECT DISTINCT c.regcode, c.name
        FROM persons p
        JOIN companies c ON c.regcode = p.company_regcode
        WHERE p.person_name = :n AND p.role = 'member' 
          AND p.legal_entity_regcode IS NULL
          AND c.regcode != :r
    """), {"n": company_name, "r": regcode}).fetchall()
    
    # Combine and check ownership >50%
    seen = set()
    result = []
    for sub in list(by_regcode) + list(by_name):
        if sub.regcode in seen or sub.regcode == regcode:
            continue
        seen.add(sub.regcode)
        
        # Calculate our ownership in this subsidiary
        percent = get_ownership_percent(conn, regcode, sub.regcode, is_legal_entity=True)
        if percent > 50:
            result.append({"regcode": sub.regcode, "name": sub.name, "percent": round(percent, 2)})
    
    return result


def get_ownership_chain(conn, start_regcode: int, visited: set = None, depth: int = 0, max_depth: int = 5) -> list:
    """
    Recursively find all linked entities through ownership chain (transitive closure).
    
    E kritērijs: Ja A→B un B→C (>50%), tad A↔C ir saistīti.
    """
    if visited is None:
        visited = set()
    
    if start_regcode in visited or depth > max_depth:
        return []
    
    visited.add(start_regcode)
    all_linked = []
    
    # Get company name for subsidiary search
    company_row = conn.execute(text("SELECT name FROM companies WHERE regcode = :r"), {"r": start_regcode}).fetchone()
    company_name = company_row.name if company_row else ""
    
    # Find direct owners (upstream)
    owners = find_direct_owners(conn, start_regcode)
    for owner in owners:
        entry = {
            "regcode": owner["regcode"],
            "name": owner["name"],
            "relation": "owner",
            "ownership_percent": owner["percent"],
            "chain_depth": depth + 1,
            "chain_type": "upstream"
        }
        all_linked.append(entry)
        
        # Recurse to find chain
        chain = get_ownership_chain(conn, owner["regcode"], visited, depth + 1, max_depth)
        all_linked.extend(chain)
    
    # Find direct subsidiaries (downstream)
    subsidiaries = find_direct_subsidiaries(conn, start_regcode, company_name)
    for sub in subsidiaries:
        entry = {
            "regcode": sub["regcode"],
            "name": sub["name"],
            "relation": "subsidiary",
            "ownership_percent": sub["percent"],
            "chain_depth": depth + 1,
            "chain_type": "downstream"
        }
        all_linked.append(entry)
        
        # Recurse to find chain
        chain = get_ownership_chain(conn, sub["regcode"], visited, depth + 1, max_depth)
        all_linked.extend(chain)
    
    return all_linked


def find_significant_physical_persons(conn, regcode: int) -> list:
    """
    Find ALL physical persons with ≥25% ownership in this company.
    
    Returns person_name + person_code for identification since
    person_code is partially masked (format: 140777-*****).
    """
    result = conn.execute(text("""
        WITH company_capital AS (
            SELECT SUM(number_of_shares * share_nominal_value) as total
            FROM persons WHERE company_regcode = :r AND role = 'member'
        )
        SELECT 
            p.person_code,
            p.person_name,
            SUM(p.number_of_shares * p.share_nominal_value) as person_value,
            cc.total as total_capital,
            CASE WHEN cc.total > 0 
                THEN (SUM(p.number_of_shares * p.share_nominal_value) / cc.total) * 100 
                ELSE 0 
            END as ownership_percent
        FROM persons p, company_capital cc
        WHERE p.company_regcode = :r 
          AND p.role = 'member'
          AND p.legal_entity_regcode IS NULL
          AND p.person_name IS NOT NULL
          AND TRIM(p.person_name) != ''
        GROUP BY p.person_code, p.person_name, cc.total
        HAVING (SUM(p.number_of_shares * p.share_nominal_value) / NULLIF(cc.total, 0)) >= 0.25
    """), {"r": regcode}).fetchall()
    
    return [{
        "person_code": r.person_code,
        "name": r.person_name,
        "percent": float(r.ownership_percent) if r.ownership_percent else 0
    } for r in result]


def find_companies_controlled_by_person(conn, person_name: str, person_code: str, exclude_regcode: int) -> list:
    """
    F1 kritērijs: Atrast VISUS citus uzņēmumus, kuros šī persona ir dalībnieks.
    
    Identifikācija notiek pēc:
    - person_name (vārds uzvārds) - OBLIGĀTI jāsakrīt
    - person_code (ja ir) - jāsakrīt, bet ņem vērā, ka otrā daļa ir maskēta
    
    Atgriež uzņēmumus ar klasifikāciju:
    - >50% = LINKED (saistīts)
    - 25-50% = PARTNER (partneris)
    """
    if not person_name or person_name.strip() == '':
        return []
    
    # Match by person_name, and additionally by person_code if available
    # Since person_code is masked (140777-*****), we match the visible prefix
    if person_code and len(person_code) > 6:
        # Extract visible prefix (first 6 digits before dash)
        code_prefix = person_code.split('-')[0] if '-' in person_code else person_code[:6]
        query = """
            WITH person_companies AS (
                SELECT 
                    c.regcode,
                    c.name,
                    c.nace_code,
                    c.nace_section,
                    SUM(p.number_of_shares * p.share_nominal_value) as person_value,
                    (SELECT SUM(number_of_shares * share_nominal_value) 
                     FROM persons WHERE company_regcode = c.regcode AND role = 'member') as total_capital
                FROM persons p
                JOIN companies c ON c.regcode = p.company_regcode
                WHERE LOWER(TRIM(p.person_name)) = LOWER(TRIM(:person_name))
                  AND p.person_code LIKE :code_prefix || '%'
                  AND p.role = 'member'
                  AND p.legal_entity_regcode IS NULL
                  AND c.regcode != :exclude
                GROUP BY c.regcode, c.name, c.nace_code, c.nace_section
            )
            SELECT regcode, name, nace_code, nace_section,
                   COALESCE((person_value / NULLIF(total_capital, 0)) * 100, 0) as ownership_percent,
                   CASE 
                       WHEN (person_value / NULLIF(total_capital, 0)) > 0.5 THEN 'linked'
                       WHEN (person_value / NULLIF(total_capital, 0)) >= 0.25 THEN 'partner'
                       ELSE 'minor'
                   END as classification
            FROM person_companies
            WHERE (person_value / NULLIF(total_capital, 0)) >= 0.25
        """
        result = conn.execute(text(query), {
            "person_name": person_name,
            "code_prefix": code_prefix,
            "exclude": exclude_regcode
        }).fetchall()
    else:
        # Fallback: match by name only (less precise)
        query = """
            WITH person_companies AS (
                SELECT 
                    c.regcode,
                    c.name,
                    c.nace_code,
                    c.nace_section,
                    SUM(p.number_of_shares * p.share_nominal_value) as person_value,
                    (SELECT SUM(number_of_shares * share_nominal_value) 
                     FROM persons WHERE company_regcode = c.regcode AND role = 'member') as total_capital
                FROM persons p
                JOIN companies c ON c.regcode = p.company_regcode
                WHERE LOWER(TRIM(p.person_name)) = LOWER(TRIM(:person_name))
                  AND p.role = 'member'
                  AND p.legal_entity_regcode IS NULL
                  AND c.regcode != :exclude
                GROUP BY c.regcode, c.name, c.nace_code, c.nace_section
            )
            SELECT regcode, name, nace_code, nace_section,
                   COALESCE((person_value / NULLIF(total_capital, 0)) * 100, 0) as ownership_percent,
                   CASE 
                       WHEN (person_value / NULLIF(total_capital, 0)) > 0.5 THEN 'linked'
                       WHEN (person_value / NULLIF(total_capital, 0)) >= 0.25 THEN 'partner'
                       ELSE 'minor'
                   END as classification
            FROM person_companies
            WHERE (person_value / NULLIF(total_capital, 0)) >= 0.25
        """
        result = conn.execute(text(query), {
            "person_name": person_name,
            "exclude": exclude_regcode
        }).fetchall()
    
    companies = []
    for r in result:
        companies.append({
            "regcode": r.regcode,
            "name": r.name,
            "nace_code": r.nace_code,
            "ownership_percent": float(r.ownership_percent) if r.ownership_percent else 0,
            "classification": r.classification
        })
    
    logger.info(f"[PERSON] Found {len(companies)} companies for '{person_name}'")
    return companies


def find_all_linked_entities(conn, regcode: int, year: int = 2024) -> dict:
    """
    Galvenā funkcija: Atrod VISUS saistītos uzņēmumus pēc ES MVU noteikumiem.
    
    Ietver:
    - A1/A2: Tiešā kapitāla/balsstiesību kontrole (>50%)
    - E: Ķēdes efekts (A→B→C = A↔C saistīti)
    - F1: Fiziskās personas kontrole (viena persona kontrolē vairākus uzņēmumus)
    """
    
    # Get company info
    company = conn.execute(text("SELECT name, nace_section FROM companies WHERE regcode = :r"), {"r": regcode}).fetchone()
    if not company:
        return {"linked": [], "partners": [], "via_person": []}
    
    company_name = company.name
    nace_section = company.nace_section
    
    all_linked = []
    all_partners = []
    via_person = []
    seen_regcodes = set([regcode])  # Don't include self
    
    # 1. Chain effect (transitive closure) - finds all >50% linked through chains
    logger.info(f"[LINKED] Finding ownership chain for {regcode}")
    chain_entities = get_ownership_chain(conn, regcode, set(), 0, 5)
    
    for entity in chain_entities:
        if entity["regcode"] not in seen_regcodes:
            seen_regcodes.add(entity["regcode"])
            all_linked.append({
                **entity,
                "link_reason": f"Ķēdes efekts ({entity.get('chain_type', 'direct')})"
            })
    
    logger.info(f"[LINKED] Found {len(all_linked)} linked via ownership chain")
    
    # 2. Physical person control (F1 criterion)
    # Find ALL significant persons (≥25%) and their other companies
    logger.info(f"[LINKED] Finding significant physical persons for {regcode}")
    significant_persons = find_significant_physical_persons(conn, regcode)
    logger.info(f"[LINKED] Found {len(significant_persons)} significant persons")
    
    for person in significant_persons:
        if not person["name"]:
            continue
            
        # Find ALL other companies where this person has ≥25% ownership
        # Uses person_name + person_code prefix for matching
        other_companies = find_companies_controlled_by_person(
            conn, person["name"], person.get("person_code"), regcode
        )
        
        for other in other_companies:
            if other["regcode"] not in seen_regcodes:
                seen_regcodes.add(other["regcode"])
                
                entry = {
                    "regcode": other["regcode"],
                    "name": other["name"],
                    "ownership_percent": other["ownership_percent"],
                    "controlling_person": person["name"],
                    "person_percent": person["percent"],
                    "relation": "via_person",
                    "classification": other["classification"],
                    "link_reason": f"Kontrolē {person['name']} ({person['percent']:.1f}%)"
                }
                
                # Classify based on person's ownership in the other company
                if other["classification"] == "linked":
                    # >50% in other company = LINKED
                    all_linked.append(entry)
                else:
                    # 25-50% in other company = via_person (show separately)
                    via_person.append(entry)
    
    logger.info(f"[LINKED] Found {len(via_person)} companies via physical person control")
    
    # 3. Also get partners (25-50%) - direct only
    partners_result = conn.execute(text("""
        WITH company_capital AS (
            SELECT SUM(number_of_shares * share_nominal_value) as total
            FROM persons WHERE company_regcode = :r AND role = 'member'
        )
        SELECT 
            p.legal_entity_regcode as partner_regcode,
            p.person_name as partner_name,
            p.person_code,
            SUM(p.number_of_shares * p.share_nominal_value) as value,
            cc.total as total_capital,
            CASE WHEN cc.total > 0 
                THEN (SUM(p.number_of_shares * p.share_nominal_value) / cc.total) * 100 
                ELSE 0 
            END as ownership_percent
        FROM persons p, company_capital cc
        WHERE p.company_regcode = :r 
          AND p.role = 'member'
        GROUP BY p.legal_entity_regcode, p.person_name, p.person_code, cc.total
        HAVING (SUM(p.number_of_shares * p.share_nominal_value) / NULLIF(cc.total, 0)) BETWEEN 0.25 AND 0.50
    """), {"r": regcode}).fetchall()
    
    for p in partners_result:
        if p.partner_regcode and p.partner_regcode not in seen_regcodes:
            seen_regcodes.add(p.partner_regcode)
            all_partners.append({
                "regcode": p.partner_regcode,
                "name": p.partner_name,
                "ownership_percent": float(p.ownership_percent),
                "relation": "owner",
                "entity_type": "legal_entity"
            })
        elif not p.partner_regcode and p.person_code:
            # Physical person partner
            all_partners.append({
                "regcode": None,
                "name": p.partner_name,
                "ownership_percent": float(p.ownership_percent),
                "relation": "owner",
                "entity_type": "physical_person"
            })
    
    return {
        "linked": all_linked,
        "partners": all_partners,
        "via_person": via_person,
        "total_linked_count": len(all_linked) + len(via_person)
    }

@router.get("/companies/{regcode}/graph")
def get_related_companies(regcode: int, year: int = 2024):
    """
    ES MVU Saistīto Uzņēmumu un Personu Klasifikācija:
    - Partner: 25-50% ownership
    - Linked: >50% ownership  
    - Autonomous: <25% or no relations
    
    Includes both legal entities AND physical persons with >=25% ownership.
    """
    
    def classify_ownership(percent: float) -> str:
        if percent is None:
            return "unknown"
        if percent > 50:
            return "linked"
        elif percent >= 25:
            return "partner"
        else:
            return "minor"  # <25%, ignored
    
    def get_financial_data(conn, related_regcode: int, year: int):
        """Get financial data for a related company"""
        if not related_regcode:
            return {"employees": None, "turnover": None, "balance": None}
        
        fin = conn.execute(text("""
            SELECT turnover, profit, employees, total_assets
            FROM financial_reports
            WHERE company_regcode = :r AND year = :y
            ORDER BY year DESC LIMIT 1
        """), {"r": related_regcode, "y": year}).fetchone()
        
        if fin:
            return {
                "employees": fin.employees,
                "turnover": float(fin.turnover) if fin.turnover else None,
                "balance": float(fin.total_assets) if fin.total_assets else None
            }
        return {"employees": None, "turnover": None, "balance": None}
    
    partners = []  # 25-50%
    linked = []    # >50%
    total_capital = 0
    
    with engine.connect() as conn:
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
        
        logger.info(f"[DEBUG] Company {regcode} ({company_name}): Found {len(owners)} owners")
        for o in owners:
            logger.info(f"[DEBUG]   Owner: {o.person_name}, shares={o.number_of_shares}, nominal={o.share_nominal_value}, legal_entity_regcode={o.legal_entity_regcode}")
        
        # Calculate total capital
        for owner in owners:
            shares = float(owner.number_of_shares or 0)
            nominal = float(owner.share_nominal_value or 0)
            total_capital += shares * nominal
        
        logger.info(f"[DEBUG] Company {regcode}: Total capital = {total_capital}")
        
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
        
        logger.info(f"[DEBUG] Company {regcode}: Found {len(subsidiaries_by_regcode)} subsidiaries by regcode, {len(subsidiaries_by_name)} by name")
        for s in subsidiaries_by_regcode:
            logger.info(f"[DEBUG]   Subsidiary (by regcode): {s.name} ({s.regcode})")
        for s in subsidiaries_by_name:
            logger.info(f"[DEBUG]   Subsidiary (by name): {s.name} ({s.regcode})")
        
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
            logger.info(f"[DEBUG]   Subsidiary {sub.name}: percent={percent}, classification={classification}")
            
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
    logger.info(f"[DEBUG] Company {regcode}: Final result - {len(linked)} linked, {len(partners)} partners")
    if linked:
        status = "LINKED"
    elif partners:
        status = "PARTNER"
    else:
        status = "AUTONOMOUS"
    
    return {
        "status": status,
        "year": year,
        "total_capital": total_capital,
        "partners": partners,
        "linked": linked
    }

# Alias route for compatibility (frontend may call without /companies/ prefix)
@router.get("/mvk-declaration/{regcode}")
@router.get("/companies/{regcode}/mvk-declaration")
def get_mvk_declaration(regcode: int, year: int = 2024):
    """
    MVK (MVU) Deklarācijas Pielikumu Datu Struktūra
    
    Atgriež pilnu datu kopu priekš:
    - Scenārija noteikšanas (Autonoms / Partner / Saistīts)
    - A sadaļas (Partneruzņēmumi 25-50%)
    - B sadaļas (Saistītie >50%, ar/bez konsolidācijas)
    - Kopsavilkuma tabulas 2.1-2.3 aprēķiniem
    """
    
    def classify_ownership(percent: float) -> str:
        if percent is None:
            return "unknown"
        if percent > 50:
            return "linked"
        elif percent >= 25:
            return "partner"
        else:
            return "minor"
    
    def get_financial_data(conn, related_regcode: int, year: int):
        """Get financial data for a related company"""
        if not related_regcode:
            return {"employees": None, "turnover": None, "balance": None}
        
        fin = conn.execute(text("""
            SELECT turnover, profit, employees, total_assets
            FROM financial_reports
            WHERE company_regcode = :r AND year = :y
            ORDER BY year DESC LIMIT 1
        """), {"r": related_regcode, "y": year}).fetchone()
        
        if fin:
            return {
                "employees": fin.employees,
                "turnover": float(fin.turnover) if fin.turnover else None,
                "balance": float(fin.total_assets) if fin.total_assets else None
            }
        return {"employees": None, "turnover": None, "balance": None}
    
    with engine.connect() as conn:
        # 1. Get Company Info
        company_row = conn.execute(text("""
            SELECT name, regcode, address
            FROM companies WHERE regcode = :r
        """), {"r": regcode}).fetchone()
        
        if not company_row:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # 2. Get Authorized Person (first officer with representation rights)
        auth_person = conn.execute(text("""
            SELECT person_name, position
            FROM persons
            WHERE company_regcode = :r AND role = 'officer'
            ORDER BY date_from DESC
            LIMIT 1
        """), {"r": regcode}).fetchone()
        
        # 3. Get Own Financial Data
        own_fin = conn.execute(text("""
            SELECT turnover, employees, total_assets
            FROM financial_reports
            WHERE company_regcode = :r AND year = :y
        """), {"r": regcode, "y": year}).fetchone()
        
        own_financials = {
            "employees": own_fin.employees if own_fin else None,
            "turnover": float(own_fin.turnover) if own_fin and own_fin.turnover else None,
            "balance": float(own_fin.total_assets) if own_fin and own_fin.total_assets else None
        }
        
        # 4. Calculate Capital and Get Owners
        owners = conn.execute(text("""
            SELECT 
                p.person_name, p.number_of_shares, p.share_nominal_value,
                p.legal_entity_regcode, c.name as legal_entity_name
            FROM persons p
            LEFT JOIN companies c ON c.regcode = p.legal_entity_regcode
            WHERE p.company_regcode = :r AND p.role = 'member'
        """), {"r": regcode}).fetchall()
        
        total_capital = sum(
            float(o.number_of_shares or 0) * float(o.share_nominal_value or 0)
            for o in owners
        )
        
        partners = []  # 25-50%
        linked = []    # >50%
        
        # Classify Owners (upstream)
        for owner in owners:
            shares = float(owner.number_of_shares or 0)
            nominal = float(owner.share_nominal_value or 0)
            owner_value = shares * nominal
            percent = (owner_value / total_capital * 100) if total_capital > 0 else None
            classification = classify_ownership(percent)
            
            if classification in ["partner", "linked"]:
                is_legal_entity = owner.legal_entity_regcode is not None
                financials = get_financial_data(conn, owner.legal_entity_regcode, year) if is_legal_entity else {"employees": None, "turnover": None, "balance": None}
                
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
        
        # Get Subsidiaries (downstream)
        subsidiaries = conn.execute(text("""
            SELECT c.regcode, c.name, p.number_of_shares, p.share_nominal_value
            FROM persons p
            JOIN companies c ON c.regcode = p.company_regcode
            WHERE p.legal_entity_regcode = :r AND p.role = 'member'
        """), {"r": regcode}).fetchall()
        
        for sub in subsidiaries:
            if sub.regcode == regcode:
                continue
            
            sub_capital = conn.execute(text("""
                SELECT SUM(COALESCE(number_of_shares, 0) * COALESCE(share_nominal_value, 0)) as total
                FROM persons WHERE company_regcode = :r AND role = 'member'
            """), {"r": sub.regcode}).scalar() or 0
            
            our_value = float(sub.number_of_shares or 0) * float(sub.share_nominal_value or 0)
            percent = (our_value / float(sub_capital) * 100) if sub_capital > 0 else None
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
        
        # ========================================
        # COMPREHENSIVE ENTITY DETECTION (EU SME)
        # ========================================
        # Use new algorithm to find ALL linked entities including:
        # - Chain effect (A→B→C = A↔C linked)
        # - Physical person control (same person controlling multiple companies)
        
        logger.info(f"[MVK] Running comprehensive entity detection for {regcode}")
        comprehensive_result = find_all_linked_entities(conn, regcode, year)
        
        # Merge chain-effect linked entities
        seen_regcodes = set(e.get("regcode") for e in linked if e.get("regcode"))
        for chain_entity in comprehensive_result.get("linked", []):
            if chain_entity.get("regcode") and chain_entity["regcode"] not in seen_regcodes:
                seen_regcodes.add(chain_entity["regcode"])
                financials = get_financial_data(conn, chain_entity["regcode"], year)
                linked.append({
                    "name": chain_entity["name"],
                    "regcode": chain_entity["regcode"],
                    "relation": chain_entity.get("relation", "chain"),
                    "entity_type": "legal_entity",
                    "ownership_percent": chain_entity.get("ownership_percent"),
                    "chain_depth": chain_entity.get("chain_depth", 1),
                    "link_reason": chain_entity.get("link_reason", "Ķēdes efekts"),
                    **financials
                })
        
        # Add entities linked via physical person control
        for person_entity in comprehensive_result.get("via_person", []):
            if person_entity.get("regcode") and person_entity["regcode"] not in seen_regcodes:
                seen_regcodes.add(person_entity["regcode"])
                financials = get_financial_data(conn, person_entity["regcode"], year)
                linked.append({
                    "name": person_entity["name"],
                    "regcode": person_entity["regcode"],
                    "relation": "via_person",
                    "entity_type": "legal_entity",
                    "ownership_percent": person_entity.get("ownership_percent"),
                    "controlling_person": person_entity.get("controlling_person"),
                    "link_reason": person_entity.get("link_reason", "Fiziskās personas kontrole"),
                    **financials
                })
        
        logger.info(f"[MVK] Total linked after comprehensive detection: {len(linked)}")
        
        # 5. Determine Scenario
        has_partners = len(partners) > 0
        has_linked = len(linked) > 0
        
        # Consolidation: assumed if any linked entity has >50% ownership
        has_consolidation = any(e.get("ownership_percent", 0) > 50 for e in linked)
        
        if has_linked:
            company_type = "LINKED"
            required_sections = ["B1"] if has_consolidation else ["B2"]
            if has_partners:
                required_sections.insert(0, "A")
        elif has_partners:
            company_type = "PARTNER"
            required_sections = ["A"]
        else:
            company_type = "AUTONOMOUS"
            required_sections = []
        
        # 6. Calculate A Section Totals (proportional)
        section_a_totals = {"employees": 0, "turnover": 0, "balance": 0}
        for p in partners:
            pct = (p.get("ownership_percent") or 0) / 100
            section_a_totals["employees"] += int((p.get("employees") or 0) * pct)
            section_a_totals["turnover"] += (p.get("turnover") or 0) * pct
            section_a_totals["balance"] += (p.get("balance") or 0) * pct
        
        # 7. Calculate B Section Totals (100% for linked)
        section_b_totals = {"employees": 0, "turnover": 0, "balance": 0}
        for l in linked:
            section_b_totals["employees"] += l.get("employees") or 0
            section_b_totals["turnover"] += l.get("turnover") or 0
            section_b_totals["balance"] += l.get("balance") or 0
        
        # 8. Summary Table 2.1-2.3
        row_2_1 = own_financials.copy()
        row_2_2 = section_a_totals.copy()
        row_2_3 = section_b_totals.copy()
        
        total_row = {
            "employees": (row_2_1.get("employees") or 0) + row_2_2["employees"] + row_2_3["employees"],
            "turnover": (row_2_1.get("turnover") or 0) + row_2_2["turnover"] + row_2_3["turnover"],
            "balance": (row_2_1.get("balance") or 0) + row_2_2["balance"] + row_2_3["balance"]
        }
        
        return {
            "scenario": {
                "company_type": company_type,
                "has_partners": has_partners,
                "has_linked": has_linked,
                "has_consolidation": has_consolidation,
                "required_sections": required_sections
            },
            "identification": {
                "name": company_row.name,
                "address": company_row.address,
                "regcode": str(company_row.regcode),
                "authorized_person": auth_person.person_name if auth_person else None,
                "authorized_position": auth_person.position if auth_person else None
            },
            "own_financials": own_financials,
            "section_a": {
                "partners": partners,
                "totals": section_a_totals
            },
            "section_b": {
                "type": "B1" if has_consolidation else "B2",
                "consolidated": section_b_totals if has_consolidation else None,
                "entities": linked
            },
            "summary_table": {
                "row_2_1": row_2_1,
                "row_2_2": row_2_2,
                "row_2_3": row_2_3,
                "total": total_row
            },
            "year": year,
            "total_capital": total_capital,
            # Calculate company size based on total (combined) data
            "company_size": calculate_company_size(
                total_row["employees"],
                total_row["turnover"],
                total_row["balance"]
            )
        }

