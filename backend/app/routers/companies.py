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
            "sepa_identifier": res.sepa_identifier,
            "company_size_badge": res.company_size_badge,
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

