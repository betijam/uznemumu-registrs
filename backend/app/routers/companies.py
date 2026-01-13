from fastapi import APIRouter, HTTPException, Response, Request, Depends, Query, BackgroundTasks
from sqlalchemy import text
from app.core.database import engine
import logging
import math
from concurrent.futures import ThreadPoolExecutor
import hashlib
from app.routers.auth import get_current_user
from typing import Optional
import json
import time
from app.routers.benchmarking import get_company_benchmark, get_top_competitors

def time_execution(name, func, *args, **kwargs):
    start = time.time()
    result = func(*args, **kwargs)
    logger.info(f"[{name}] took {time.time() - start:.4f}s")
    return result


def get_person_hash(person_code: str):
    if not person_code:
        return None
    return "P-" + hashlib.md5(person_code.encode()).hexdigest()

router = APIRouter()
logger = logging.getLogger(__name__)

# Helper to check access level
from app.utils.access_control import check_access

# Global thread pool for parallel database queries
# Using 8 workers as we have many I/O bound tasks
_executor = ThreadPoolExecutor(max_workers=8)

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
    
    This is a performance optimization to avoid N+1 queries.
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


# ==========================
# REUSABLE SERVICE LOGIC
# ==========================

def get_financial_history(regcode: int):
    with engine.connect() as conn:
        fin_rows = conn.execute(text("""
            SELECT year, turnover, profit, employees, cash_balance,
                   current_ratio, quick_ratio, cash_ratio,
                   net_profit_margin, roe, roa, debt_to_equity, equity_ratio, ebitda,
                   interest_expenses, depreciation_expenses, provision_for_income_taxes, by_nature_labour_expenses,
                   accounts_receivable, inventories, current_liabilities, non_current_liabilities, equity, total_assets, total_current_assets,
                   cfo_im_net_operating_cash_flow, cff_net_financing_cash_flow, cfi_acquisition_of_fixed_assets_intangible_assets,
                   cfo_im_income_taxes_paid
            FROM financial_reports 
            WHERE company_regcode = :r 
            ORDER BY year DESC
        """), {"r": regcode}).fetchall()
        
        history = []
        prev_turnover = None
        prev_profit = None
        
        fin_list = list(fin_rows)
        fin_list.reverse()
        
        for f in fin_list:
            row = {
                "year": f.year,
                "turnover": safe_float(f.turnover),
                "profit": safe_float(f.profit),
                "employees": f.employees,
                "cash_balance": safe_float(f.cash_balance),
                "turnover_growth": None,
                "profit_growth": None,
                "current_ratio": safe_float(f.current_ratio),
                "quick_ratio": safe_float(f.quick_ratio),
                "cash_ratio": safe_float(f.cash_ratio),
                "net_profit_margin": safe_float(f.net_profit_margin),
                "roe": safe_float(f.roe),
                "roa": safe_float(f.roa),
                "debt_to_equity": safe_float(f.debt_to_equity),
                "equity_ratio": safe_float(f.equity_ratio),
                "ebitda": safe_float(f.ebitda),
                # Extended fields
                "interest_payment": safe_float(f.interest_expenses),
                "depreciation": safe_float(f.depreciation_expenses),
                "corporate_income_tax": safe_float(f.provision_for_income_taxes),
                "labour_costs": safe_float(f.by_nature_labour_expenses),
                "accounts_receivable": safe_float(f.accounts_receivable),
                "inventories": safe_float(f.inventories),
                "current_liabilities": safe_float(f.current_liabilities),
                "non_current_liabilities": safe_float(f.non_current_liabilities),
                "equity": safe_float(f.equity),
                "total_assets": safe_float(f.total_assets),
                "total_current_assets": safe_float(f.total_current_assets),
                "cfo": safe_float(f.cfo_im_net_operating_cash_flow),
                "cff": safe_float(f.cff_net_financing_cash_flow),
                "cfi": safe_float(f.cfi_acquisition_of_fixed_assets_intangible_assets),
                "taxes_paid_cf": safe_float(f.cfo_im_income_taxes_paid)
            }
            
            turnover_val = safe_float(f.turnover)
            profit_val = safe_float(f.profit)
            if prev_turnover and turnover_val and prev_turnover != 0:
                row["turnover_growth"] = round(((turnover_val - prev_turnover) / abs(prev_turnover)) * 100, 1)
            if prev_profit and profit_val and prev_profit != 0:
                row["profit_growth"] = round(((profit_val - prev_profit) / abs(prev_profit)) * 100, 1)
            
            prev_turnover = turnover_val
            prev_profit = profit_val
            history.append(row)
        
        history.reverse()
        return history

def get_tax_history(regcode: int):
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT tp.year, tp.total_tax_paid, tp.labor_tax_iin, tp.social_tax_vsaoi, 
                   tp.avg_employees, tp.nace_code, cm.avg_gross_salary, cm.avg_net_salary
            FROM tax_payments tp
            LEFT JOIN company_computed_metrics cm ON tp.company_regcode = cm.company_regcode AND tp.year = cm.year
            WHERE tp.company_regcode = :r ORDER BY tp.year DESC
        """), {"r": regcode}).fetchall()
        
        VSAOI_RATE = 0.3409
        history = []
        for t in rows:
            avg_gross = safe_float(t.avg_gross_salary)
            avg_net = safe_float(t.avg_net_salary)
            if avg_gross is None and t.social_tax_vsaoi and t.avg_employees and float(t.avg_employees) > 0:
                vsaoi = float(t.social_tax_vsaoi)
                employees = float(t.avg_employees)
                avg_gross = round((vsaoi / VSAOI_RATE) / employees / 12, 2)
                vsaoi_emp = avg_gross * 0.105
                iin = (avg_gross - vsaoi_emp) * 0.20
                avg_net = round(avg_gross - vsaoi_emp - iin, 2)
            
            history.append({
                "year": t.year,
                "total_tax_paid": safe_float(t.total_tax_paid),
                "labor_tax_iin": safe_float(t.labor_tax_iin),
                "social_tax_vsaoi": safe_float(t.social_tax_vsaoi),
                "avg_employees": safe_float(t.avg_employees),
                "nace_code": t.nace_code,
                "avg_gross_salary": avg_gross,
                "avg_net_salary": avg_net
            })
        return history

def get_rating(regcode: int):
    with engine.connect() as conn:
        res = conn.execute(text("SELECT rating_grade, rating_explanation, last_evaluated_on FROM company_ratings WHERE company_regcode = :r"), {"r": regcode}).fetchone()
        if res:
            return {"grade": res.rating_grade, "explanation": res.rating_explanation, "date": str(res.last_evaluated_on) if res.last_evaluated_on else None}
        return None

def get_risks(regcode: int):
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT risk_type, description, start_date, risk_score, active,
                   sanction_program, sanction_list_text, legal_base_url,
                   suspension_code, suspension_grounds,
                   measure_type, institution_name, case_number,
                   liquidation_type, liquidation_grounds
            FROM risks WHERE company_regcode = :r
            ORDER BY COALESCE(active, TRUE) DESC, risk_score DESC, start_date DESC
        """), {"r": regcode}).fetchall()
        
        # Default scores if missing in DB
        DEFAULT_SCORES = {
            'sanction': 100,
            'liquidation': 50,
            'suspension': 30,
            'securing_measure': 10
        }
        
        total_score = 0
        by_type = {'sanctions': [], 'liquidations': [], 'suspensions': [], 'securing_measures': []}
        for r in rows:
            is_active = r.active if r.active is not None else True
            
            # Use DB score if provided and >0, else fallback to default
            current_score = r.risk_score if (r.risk_score and r.risk_score > 0) else DEFAULT_SCORES.get(r.risk_type, 0)
            
            if is_active:
                total_score += current_score
                
            risk = {
                "type": r.risk_type,
                "description": r.description,
                "date": str(r.start_date) if r.start_date else None,
                "score": current_score,
                "active": is_active
            }
            if r.risk_type == 'sanction':
                risk.update({"program": r.sanction_program, "list_text": r.sanction_list_text, "legal_base_url": r.legal_base_url})
                by_type['sanctions'].append(risk)
            elif r.risk_type == 'liquidation':
                risk.update({"liquidation_type": r.liquidation_type, "grounds": r.liquidation_grounds})
                by_type['liquidations'].append(risk)
            elif r.risk_type == 'suspension':
                risk.update({"suspension_code": r.suspension_code, "grounds": r.suspension_grounds})
                by_type['suspensions'].append(risk)
            elif r.risk_type == 'securing_measure':
                risk.update({"measure_type": r.measure_type, "institution": r.institution_name, "case_number": r.case_number})
                by_type['securing_measures'].append(risk)
        return by_type, total_score

def get_persons(regcode: int):
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT person_name, role, share_percent, date_from, person_code, birth_date,
                   position, rights_of_representation, representation_with_at_least,
                   number_of_shares, share_nominal_value, share_currency, legal_entity_regcode,
                   nationality, residence, entity_type
            FROM persons WHERE company_regcode = :r
        """), {"r": regcode}).fetchall()
        
        # Try to get total capital from company first if possible
        company_reg = conn.execute(text("SELECT total_capital FROM companies WHERE regcode = :r"), {"r": regcode}).fetchone()
        db_total_capital = float(company_reg.total_capital) if company_reg and company_reg.total_capital else 0
        
        calc_total_capital = sum((float(p.number_of_shares or 0) * float(p.share_nominal_value or 0)) for p in rows if p.role == 'member')
        total_capital = max(calc_total_capital, db_total_capital)
        
        ubos, members, officers = [], [], []
        for p in rows:
            birth_date = str(p.birth_date) if hasattr(p, 'birth_date') and p.birth_date else None
            entity_type = p.entity_type if hasattr(p, 'entity_type') else None
            
            if p.role == 'ubo':
                ubos.append({
                    "name": p.person_name, "person_code": p.person_code, "nationality": p.nationality, "residence": p.residence,
                    "registered_on": str(p.date_from) if p.date_from else None, "birth_date": birth_date
                })
            elif p.role == 'member':
                share_value = float(p.number_of_shares or 0) * float(p.share_nominal_value or 0)
                percent = (share_value / total_capital * 100) if total_capital > 0 else 0
                
                # Fallback to stored percent
                if (percent == 0 or percent is None) and hasattr(p, 'share_percent') and p.share_percent:
                    percent = float(p.share_percent)
                
                # If we have percent but share_value is 0, back-calculate from total_capital
                if share_value == 0 and percent > 0 and total_capital > 0:
                    share_value = total_capital * (percent / 100)
                
                # Determine if entity has a profile page
                # FOREIGN_ENTITY = no profile, others = has profile (redeploy trigger)
                legal_regcode = int(p.legal_entity_regcode) if p.legal_entity_regcode else None
                has_profile = entity_type != 'FOREIGN_ENTITY'  # FOREIGN_ENTITY never has profile
                
                members.append({
                    "name": p.person_name, "person_code": p.person_code,
                    "legal_entity_regcode": legal_regcode,
                    "has_profile": has_profile,  # Based on entity_type from DB
                    "entity_type": entity_type,  # Pass through for debugging/future use
                    "number_of_shares": int(p.number_of_shares) if p.number_of_shares else None,
                    "share_value": round(share_value, 2), "share_currency": p.share_currency or "EUR",
                    "percent": round(percent, 2), "date_from": str(p.date_from) if p.date_from else None, "birth_date": birth_date
                })
            elif p.role == 'officer':
                officers.append({
                    "name": p.person_name, "person_code": p.person_code, "position": p.position,
                    "rights_of_representation": p.rights_of_representation,
                    "representation_with_at_least": int(p.representation_with_at_least) if p.representation_with_at_least else None,
                    "registered_on": str(p.date_from) if p.date_from else None, "birth_date": birth_date
                })
        return ubos, members, officers, total_capital

def get_procurements(regcode: int):
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT authority_name, subject, amount, contract_date FROM procurements WHERE winner_regcode = :r ORDER BY contract_date DESC LIMIT 10"), {"r": regcode}).fetchall()
        return [{"authority": p.authority_name, "subject": p.subject, "amount": safe_float(p.amount), "date": str(p.contract_date)} for p in rows]

def build_full_profile(regcode: int, base_company_info: dict):
    start_time = time.time()

    # 1. Try to load persons from Cache FIRST to avoid unnecessary DB call
    cached_graph = None
    ubos, members, officers, total_capital = [], [], [], 0
    persons_loaded = False
    
    try:
        with engine.connect() as conn:
             row = conn.execute(text("SELECT graph_data FROM company_graph_cache WHERE company_regcode = :r"), {"r": regcode}).fetchone()
             if row and row.graph_data:
                 cached_graph = row.graph_data
                 # Check if graph has new structure (officers/members/ubos)
                 if 'officers' in cached_graph:
                     ubos = cached_graph.get('ubos', [])
                     members = cached_graph.get('members', [])
                     officers = cached_graph.get('officers', [])
                     total_capital = cached_graph.get('total_capital', 0)
                     persons_loaded = True
                     # Inject graph into result to avoid another query later if needed
                     base_company_info['graph'] = cached_graph
                     logger.info(f"[{regcode}] Cache HIT for persons graph")
    except Exception as e:
        logger.error(f"Failed to load generic cache: {e}")
    
    # 2. Concurrent fetching of heavy data
    with ThreadPoolExecutor(max_workers=6) as executor:
        f_fin = executor.submit(lambda: time_execution("get_financial_history", get_financial_history, regcode))
        f_risk = executor.submit(lambda: time_execution("get_risks", get_risks, regcode))
        
        # Only fetch persons if not in cache
        if not persons_loaded:
            f_pers = executor.submit(lambda: time_execution("get_persons", get_persons, regcode))
        else:
            f_pers = None
            
        f_proc = executor.submit(lambda: time_execution("get_procurements", get_procurements, regcode))
        f_rate = executor.submit(lambda: time_execution("get_rating", get_rating, regcode))
        f_tax = executor.submit(lambda: time_execution("get_tax_history", get_tax_history, regcode))

    logger.info(f"[{regcode}] Concurrent execution setup took {time.time() - start_time:.4f}s")
    
    financial_history = f_fin.result()
    tax_history = f_tax.result()
    rating = f_rate.result()
    risks_by_type, total_risk_score = f_risk.result()
    procurements = f_proc.result()
    
    if not persons_loaded and f_pers:
        ubos, members, officers, total_capital = f_pers.result()

    full_data = base_company_info.copy()
    full_data["financial_history"] = financial_history
    full_data["finances"] = financial_history[0] if financial_history else {
        "turnover": None, "profit": None, "employees": base_company_info.get("employee_count"), "year": base_company_info.get("tax_data_year")
    }
    if financial_history:
        latest = financial_history[0]
        full_data["finances"].update({"turnover_growth": latest["turnover_growth"], "profit_growth": latest["profit_growth"]})
    
    full_data["tax_history"] = tax_history
    full_data["rating"] = rating
    full_data["risks"] = risks_by_type
    full_data["total_risk_score"] = total_risk_score
    full_data["risk_level"] = "CRITICAL" if total_risk_score >= 100 else "HIGH" if total_risk_score >= 50 else "MEDIUM" if total_risk_score >= 30 else "LOW" if total_risk_score > 0 else "NONE"
    
    full_data["ubos"] = ubos
    full_data["members"] = members
    full_data["officers"] = officers
    full_data["total_capital"] = total_capital
    full_data["procurements"] = procurements
    
    return full_data

# ============================================================================
# SITEMAP ENDPOINTS (must be before /{regcode} route)
# ============================================================================

@router.get("/companies/sitemap-info")
def get_sitemap_info():
    """
    Get total count of active companies for sitemap pagination.
    """
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM companies WHERE status = 'active'")).scalar()
        return {"total": count}

@router.get("/companies/sitemap-ids")
def get_sitemap_ids(page: int = Query(1, ge=1), limit: int = Query(50000, le=50000)):
    """
    Get batch of company regcodes for sitemap generation.
    Optimized for minimal data transfer.
    """
    offset = (page - 1) * limit
    
    with engine.connect() as conn:
        query = text("""
            SELECT regcode, registration_date as updated_at
            FROM companies 
            WHERE status = 'active'
            ORDER BY regcode
            LIMIT :limit OFFSET :offset
        """)
        
        rows = conn.execute(query, {"limit": limit, "offset": offset}).fetchall()
        
        return {
            "page": page,
            "limit": limit,
            "ids": [
                {
                    "regcode": r.regcode, 
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None
                } 
                for r in rows
            ]
        }

@router.get("/companies/{regcode}")
async def get_company_details(regcode: str, response: Response, request: Request, background_tasks: BackgroundTasks):
    # NO HTTP CACHE - Access control must run every time
    response.headers["Cache-Control"] = "no-store"
    
    # Check Access Level
    has_full_access = await check_access(request)
    
    # 1. Main Info - Get this first to ensure company exists
    with engine.connect() as conn:
        res = conn.execute(text("SELECT * FROM companies WHERE regcode = :r"), {"r": regcode}).fetchone()
        if not res:
            raise HTTPException(status_code=404, detail="Company not found")
            
        # Basic company object
        company = {
            "regcode": res.regcode,
            "name": res.name,
            "name_in_quotes": res.name_in_quotes if hasattr(res, 'name_in_quotes') else None,
            "type": res.type if hasattr(res, 'type') else None,
            "type_text": res.type_text if hasattr(res, 'type_text') else None,
            "addressid": res.addressid if hasattr(res, 'addressid') else None,
            "address": res.address,
            "registration_date": str(res.registration_date),
            "status": res.status,
            "sepa_identifier": res.sepa_identifier,
            "pvn_number": res.pvn_number if hasattr(res, 'pvn_number') else None,
            "is_pvn_payer": res.is_pvn_payer if hasattr(res, 'is_pvn_payer') else False,
            "company_size_badge": res.company_size_badge,
            "latest_size_year": res.latest_size_year if hasattr(res, 'latest_size_year') else None,
            "size_changed_recently": res.size_changed_recently if hasattr(res, 'size_changed_recently') else False,
            "nace_code": res.nace_code,
            "nace_text": res.nace_text,
            "nace_section": res.nace_section,
            "nace_section_text": res.nace_section_text,
            "employee_count": res.employee_count,
            "tax_data_year": res.tax_data_year,
            # Add access flag to response so Frontend knows whether to show Teaser UI
            "has_full_access": has_full_access
        }
    
    # Log view history in background (if user is authenticated)
    try:
        current_user = await get_current_user(request)
        if current_user:
            from app.routers.history import log_view_history
            background_tasks.add_task(
                log_view_history,
                str(current_user.id),
                str(regcode),
                'company',
                company['name'],
                None  # db parameter not used anymore
            )
    except Exception as e:
        # Silently fail if user is not authenticated
        logger.debug(f"History tracking skipped: {e}")

    # Create Cache Table if not exists
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS company_profile_cache (
                company_regcode BIGINT PRIMARY KEY,
                profile_data JSONB,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()

    # 2. Try Cache
    full_profile = None
    with engine.connect() as conn:
        row = conn.execute(text("SELECT profile_data FROM company_profile_cache WHERE company_regcode = :r AND updated_at > NOW() - INTERVAL '24 HOURS'"), {"r": regcode}).fetchone()
        if row and row.profile_data:
            full_profile = row.profile_data
            full_profile["has_full_access"] = has_full_access
            logger.info(f"[CACHE] Hit for company profile {regcode}")

    if not full_profile:
        logger.info(f"[CACHE] Miss for company profile {regcode}. Calculating...")
        full_profile = build_full_profile(regcode, company)
        full_profile["has_full_access"] = has_full_access
        try:
            with engine.connect() as conn:
                conn.execute(text("INSERT INTO company_profile_cache (company_regcode, profile_data, updated_at) VALUES (:r, :d, NOW()) ON CONFLICT (company_regcode) DO UPDATE SET profile_data = :d, updated_at = NOW()"), {"r": regcode, "d": json.dumps(full_profile, default=str)})
                conn.commit()
        except Exception as e:
            logger.error(f"[CACHE] Error saving profile: {e}")

    # Access Control - Don't scrub data, just add flag for frontend
    # Frontend decides what to show/hide based on tab and access level
    # Overview tab always shows officers summary, other tabs may be locked
    full_profile["is_locked"] = not has_full_access

    return full_profile


@router.get("/companies/{regcode}/quick")
async def get_company_quick(regcode: str, response: Response, request: Request):
    """
    Ultra-fast endpoint for initial page render.
    Returns: Main info, latest finances, risks, rating.
    Frontend calls lazy-load endpoints for history data after render.
    
    Target: <200ms response time (vs 900ms for full /companies/{regcode})
    """
    # NO CACHE - Access control must run every time
    response.headers["Cache-Control"] = "no-store"
    
    # Check Access Level
    has_full_access = await check_access(request)
    
    with engine.connect() as conn:
        # Single query: Company + Latest Financial + Rating in one round-trip
        res = conn.execute(text("""
            SELECT 
                c.*,
                f.year as fin_year, f.turnover, f.profit, f.employees as fin_employees,
                r.rating_grade, r.rating_explanation,
                ist.avg_gross_salary as industry_avg_salary
            FROM companies c
            LEFT JOIN LATERAL (
                SELECT year, turnover, profit, employees 
                FROM financial_reports 
                WHERE company_regcode = c.regcode 
                ORDER BY year DESC LIMIT 1
            ) f ON true
            LEFT JOIN company_ratings r ON r.company_regcode = c.regcode
            LEFT JOIN industry_stats_materialized ist ON 
                ist.nace_code = SUBSTRING(c.nace_code FROM 1 FOR 3)
                AND ist.nace_level = 3
            WHERE c.regcode = :r
        """), {"r": regcode}).fetchone()
        
        if not res:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get active risks count and total score (single query with fallback scoring)
        risks_summary = conn.execute(text("""
            SELECT 
                COUNT(*) as count, 
                SUM(COALESCE(NULLIF(risk_score, 0), 
                    CASE 
                        WHEN risk_type = 'sanction' THEN 100
                        WHEN risk_type = 'liquidation' THEN 50
                        WHEN risk_type = 'suspension' THEN 30
                        WHEN risk_type = 'securing_measure' THEN 10
                        ELSE 0 
                    END
                )) as total_score,
                MAX(CASE 
                    WHEN risk_type = 'sanction' THEN 4
                    WHEN risk_type = 'liquidation' THEN 3
                    WHEN risk_type = 'suspension' THEN 2
                    WHEN risk_type = 'securing_measure' THEN 1
                    ELSE 0
                END) as max_severity
            FROM risks 
            WHERE company_regcode = :r AND (active = TRUE OR active IS NULL)
        """), {"r": regcode}).fetchone()
        
        total_risk_score = int(risks_summary.total_score) if risks_summary and risks_summary.total_score else 0
        
        return {
            "regcode": res.regcode,
            "name": res.name,
            "name_in_quotes": res.name_in_quotes if hasattr(res, 'name_in_quotes') else None,
            "type": res.type if hasattr(res, 'type') else None,
            "type_text": res.type_text if hasattr(res, 'type_text') else None,
            "addressid": res.addressid if hasattr(res, 'addressid') else None,
            "address": res.address,
            "registration_date": str(res.registration_date),
            "status": res.status,
            "nace_code": res.nace_code,
            "nace_text": res.nace_text,
            "company_size_badge": res.company_size_badge,
            "pvn_number": res.pvn_number if hasattr(res, 'pvn_number') else None,
            "is_pvn_payer": res.is_pvn_payer if hasattr(res, 'is_pvn_payer') else False,
            "industry_avg_salary": res.industry_avg_salary if hasattr(res, 'industry_avg_salary') else None,
            # Latest finances (just the most recent year)
            "finances": {
                "year": res.fin_year,
                "turnover": safe_float(res.turnover),
                "profit": safe_float(res.profit),
                "employees": res.fin_employees
            },
            # Rating
            "rating": {
                "grade": res.rating_grade,
                "explanation": res.rating_explanation
            } if res.rating_grade else None,
            # Risk summary (not full list)
            "risk_summary": {
                "count": risks_summary.count if risks_summary else 0,
                "total_score": total_risk_score,
                "level": "CRITICAL" if total_risk_score >= 100 else "HIGH" if total_risk_score >= 50 else "MEDIUM" if total_risk_score >= 30 else "LOW" if total_risk_score > 0 else "NONE"
            }
        }


# ================================================================================
# OPTIMIZED FULL DATA ENDPOINT (Replaces 9 separate API calls with 1)
# ================================================================================

# Helper for graph data (Unified logic for full profile and graph endpoint)
def _get_graph_data_internal(conn, regcode: int, year: int = 2024):
    """
    Retrieves or calculates comprehensive company graph data.
    - Checks cache first
    - If miss: Calculates chain effects, physical person control, etc.
    - Fetches financials
    - Enriches and formats data
    - Saves to cache
    """
    # 1. Try Cache
    cached_graph = conn.execute(text("SELECT graph_data FROM company_graph_cache WHERE company_regcode = :r"), {"r": regcode}).fetchone()
    if cached_graph and cached_graph.graph_data:
        return cached_graph.graph_data

    # 2. Calculate
    logger.info(f"[GRAPH] Cache miss for {regcode}, calculating...")
    comp = find_all_linked_entities(conn, regcode, year)
    
    # 3. Collect regs for financials
    all_regs = []
    for e in comp["linked"]:
        if e.get("regcode"): all_regs.append(e["regcode"])
    for e in comp["partners"]:
        if e.get("regcode"): all_regs.append(e["regcode"])
    for e in comp["via_person"]:
        if e.get("regcode"): all_regs.append(e["regcode"])
    for e in comp["needs_confirmation"]:
        if e.get("regcode"): all_regs.append(e["regcode"])
        
    # 4. Bulk fetch financials
    fin_map = bulk_fetch_financials(conn, list(set(all_regs)), year)
    
    def enrich(entity):
        if entity.get("regcode") and entity["regcode"] in fin_map:
            f = fin_map[entity["regcode"]]
            return {**entity, "employees": f["employees"], "turnover": f["turnover"], "balance": f["balance"]}
        return {**entity, "employees": None, "turnover": None, "balance": None}

    # 5. Build enriched lists and merge via_person
    linked = [enrich(e) for e in comp["linked"]]
    partners = [enrich(e) for e in comp["partners"]]
    
    # Merge via_person into linked/partners based on classification
    for e in comp["via_person"]:
        enriched = enrich(e)
        if e["classification"] == "linked":
            linked.append(enriched)
        else:
            partners.append(enriched)
            
    # 6. Determine status
    status = "AUTONOMOUS"
    if linked: status = "LINKED"
    elif partners: status = "PARTNER"

    # 7. Get total capital (Calculated from persons as column might not exist in companies)
    cap_row = conn.execute(text("""
        SELECT SUM(number_of_shares * share_nominal_value) as total_capital 
        FROM persons 
        WHERE company_regcode = :r AND role = 'member'
    """), {"r": regcode}).fetchone()
    total_capital = float(cap_row.total_capital) if cap_row and cap_row.total_capital else 0
    
    result = {
        "status": status,
        "linked": linked,
        "partners": partners,
        "via_person": [enrich(e) for e in comp["via_person"]], # Keep separately for UI if needed
        "needs_confirmation": [enrich(e) for e in comp["needs_confirmation"]],
        "total_capital": total_capital,
        "year": year
    }
    
    # 8. Save to Cache
    save_cached_graph(conn, regcode, result)
    
    return result

@router.get("/companies/{regcode}/full")
async def get_company_full_data(regcode: str, response: Response, request: Request):
    """
    🚀 PERFORMANCE OPTIMIZED: Returns ALL company data in a single response.
    Replaces 9 separate API calls (/quick, /financial-history, /persons, /risks, 
    /graph, /benchmark, /competitors, /tax-history, /procurements) with 1 call.
    
    Result: 9x faster page load + reduced server load.
    """
    response.headers["Cache-Control"] = "no-store"  # Access control requires fresh check
    
    # Check Access Level
    has_full_access = await check_access(request)
    
    # 🚀 PARALLEL OPTIMIZATION: Start benchmark and competitors in background threads
    # These use separate DB connections and can run concurrently with main queries
    executor = ThreadPoolExecutor(max_workers=2)
    benchmark_future = executor.submit(get_company_benchmark, int(regcode))
    competitors_future = executor.submit(get_top_competitors, regcode, 5)
    
    try:
        with engine.connect() as conn:
            # 1. Get basic company info
            company_row = conn.execute(
                text("SELECT * FROM companies WHERE regcode = :r"), 
                {"r": regcode}
            ).fetchone()
            
            if not company_row:
                executor.shutdown(wait=False)
                raise HTTPException(status_code=404, detail="Company not found")
            
            # 2. Sequential fetching of base data
            fin_history_rows = conn.execute(text("""
                SELECT year, turnover, profit, employees, cash_balance,
                       current_ratio, quick_ratio, cash_ratio,
                       net_profit_margin, roe, roa, debt_to_equity, equity_ratio, ebitda,
                       interest_expenses, depreciation_expenses, provision_for_income_taxes, by_nature_labour_expenses,
                       accounts_receivable, inventories, current_liabilities, non_current_liabilities, equity, total_assets, total_current_assets,
                       cfo_im_net_operating_cash_flow, cff_net_financing_cash_flow, cfi_acquisition_of_fixed_assets_intangible_assets,
                       cfo_im_income_taxes_paid
                FROM financial_reports 
                WHERE company_regcode = :r 
                ORDER BY year DESC
            """), {"r": regcode}).fetchall()
            
            rating_row = conn.execute(text("""
                SELECT cr.rating_grade, cr.last_evaluated_on, cr.rating_explanation, c.nace_code, c.nace_text
                FROM companies c
                LEFT JOIN company_ratings cr ON c.regcode = cr.company_regcode
                WHERE c.regcode = :r
            """), {"r": regcode}).fetchone()

            persons_rows = conn.execute(text("""
                SELECT person_name, person_code, role, share_percent, date_from, 
                       position, rights_of_representation, representation_with_at_least,
                       number_of_shares, share_nominal_value, share_currency, legal_entity_regcode,
                       nationality, residence
                FROM persons WHERE company_regcode = :r
            """), {"r": regcode}).fetchall()

            # Derive latest_fin from history (guarantees consistency with charts)
            latest_fin = fin_history_rows[0] if fin_history_rows else None
            
            # 4. Get persons (officers, members, ubos) from single 'persons' table
            
            # Process persons by role
            officers, members, ubos = [], [], []
            db_total_capital = float(company_row.total_capital) if hasattr(company_row, 'total_capital') and company_row.total_capital else 0
            calc_total_capital = sum((float(p.number_of_shares or 0) * float(p.share_nominal_value or 0)) 
                              for p in persons_rows if p.role == 'member')
            total_capital = max(calc_total_capital, db_total_capital)
            
            for p in persons_rows:
                birth_date = str(p.birth_date) if hasattr(p, 'birth_date') and p.birth_date else None
                if p.role == 'ubo':
                    ubos.append({
                        "name": p.person_name,
                        "person_hash": p.person_code,
                        "person_code": p.person_code,
                        "birth_date": birth_date
                    })
                elif p.role == 'member':
                    share_value = float(p.number_of_shares or 0) * float(p.share_nominal_value or 0)
                    percent = (share_value / total_capital * 100) if total_capital > 0 else 0
                    if (percent == 0 or percent is None) and hasattr(p, 'share_percent') and p.share_percent:
                        percent = float(p.share_percent)
                    
                    # Back-calculate value if missing
                    if share_value == 0 and percent > 0 and total_capital > 0:
                        share_value = total_capital * (percent / 100)

                    members.append({
                        "name": p.person_name,
                        "number_of_shares": int(p.number_of_shares) if p.number_of_shares else None,
                        "share_value": round(share_value, 2),
                        "share_currency": p.share_currency or 'EUR',
                        "percent": round(percent, 2),
                        "person_hash": p.person_code,
                        "person_code": p.person_code,
                        "date_from": str(p.date_from) if p.date_from else None,
                        "legal_entity_regcode": p.legal_entity_regcode,
                        "birth_date": birth_date
                    })
                elif p.role == 'officer':
                    officers.append({
                        "name": p.person_name,
                        "position": p.position,
                        "person_hash": p.person_code,
                        "person_code": p.person_code,
                        "registered_on": str(p.date_from) if p.date_from else None,
                        "rights_of_representation": p.rights_of_representation,
                        "representation_with_at_least": p.representation_with_at_least
                    })
            
            # 5. Get risks using existing function
            risks_by_type, total_risk_score = get_risks(regcode)
            
            # 6. Graph data (ASYNC OPTIMIZATION)
            # Instead of calculating heavy graph here, we return basic structure.
            # Frontend calls /companies/{regcode}/graph separately.
            # This makes the initial page load FAST.
            cached_graph = conn.execute(text("SELECT graph_data FROM company_graph_cache WHERE company_regcode = :r"), {"r": regcode}).fetchone()
            if cached_graph and cached_graph.graph_data:
                graph_data = cached_graph.graph_data
            else:
                # Return basic empty structure, let frontend fetch via dedicated endpoint
                graph_data = {"status": "LOADING", "linked": [], "partners": [], "via_person": [], "needs_confirmation": []}

            # 7. Get tax history with metrics
            tax_rows = conn.execute(text("""
                SELECT tp.year, 
                       tp.labor_tax_iin, 
                       tp.social_tax_vsaoi, 
                       tp.total_tax_paid,
                       tp.avg_employees,
                       cm.avg_gross_salary
                FROM tax_payments tp
                LEFT JOIN company_computed_metrics cm ON tp.company_regcode = cm.company_regcode AND tp.year = cm.year
                WHERE tp.company_regcode = :r
                ORDER BY tp.year DESC
            """), {"r": regcode}).fetchall()
            
            # Process tax history (Calculate salary if missing)
            processed_tax_history = []
            latest_avg_salary = None
            VSAOI_RATE = 0.3409
            
            for t in tax_rows:
                avg_gross = safe_float(t.avg_gross_salary)
                
                # Calculate from VSAOI if missing
                if avg_gross is None and t.social_tax_vsaoi and t.avg_employees and float(t.avg_employees) > 0:
                    try:
                        monthly_vsaoi = float(t.social_tax_vsaoi) / 12 / float(t.avg_employees)
                        avg_gross = monthly_vsaoi / VSAOI_RATE
                    except:
                        pass
                
                if latest_avg_salary is None and avg_gross:
                    latest_avg_salary = avg_gross

                processed_tax_history.append({
                    "year": t.year, 
                    "total_tax_paid": safe_float(t.total_tax_paid),
                    "social_tax_vsaoi": safe_float(t.social_tax_vsaoi),
                    "labor_tax_iin": safe_float(t.labor_tax_iin),
                    "avg_employees": t.avg_employees,
                    "avg_gross_salary": round(avg_gross, 2) if avg_gross else None
                })
            
            # 8. Get procurements (with subject and date)
            proc_rows = conn.execute(text("""
                SELECT authority_name, subject, amount, contract_date
                FROM procurements WHERE winner_regcode = :r
                ORDER BY contract_date DESC
            """), {"r": regcode}).fetchall()

            # Process procurements: Group by authority+date to sum amounts and show all parts
            proc_map = {}
            for p in proc_rows:
                # Key based on date and authority (to group parts of same tender)
                key = f"{p.contract_date}_{p.authority_name}"
                if key not in proc_map:
                    proc_map[key] = {
                        "authority": p.authority_name,
                        "subject": p.subject,  # Initial subject
                        "amount": 0.0,
                        "contract_date": str(p.contract_date) if p.contract_date else None,
                        "count": 0
                    }
                else:
                    existing_subject = proc_map[key]["subject"] or ""
                    if p.subject and p.subject not in existing_subject:
                        proc_map[key]["subject"] = f"{existing_subject}; {p.subject}" if existing_subject else p.subject
                
                proc_map[key]["amount"] += float(p.amount or 0)
                proc_map[key]["count"] += 1
            
            processed_procurements = list(proc_map.values())
            # Sort by date
            processed_procurements.sort(key=lambda x: x["contract_date"] or "", reverse=True)
        
        # Build response
        return {
            "company": {
                "regcode": regcode,
                "name": company_row.name,
                "type": company_row.type if hasattr(company_row, 'type') else None,
                "address": company_row.address,
                "registration_date": str(company_row.registration_date),
                "status": company_row.status,
                "has_full_access": has_full_access,
                "latest_year": latest_fin.year if latest_fin else None,
                "nace_code": rating_row.nace_code if rating_row else None,
                "nace_text": rating_row.nace_text if rating_row else None,
                "finances": {
                    "year": latest_fin.year if latest_fin else None,
                    "turnover": safe_float(latest_fin.turnover) if latest_fin else None,
                    "profit": safe_float(latest_fin.profit) if latest_fin else None,
                    "employees": (latest_fin.employees if latest_fin and latest_fin.employees is not None 
                              else (processed_tax_history[0]["avg_employees"] if processed_tax_history and processed_tax_history[0]["avg_employees"] is not None 
                              else (company_row.employee_count if hasattr(company_row, 'employee_count') else None))),
                    "avg_salary": round(latest_avg_salary, 2) if latest_avg_salary else None,
                },
                "rating": {
                    "grade": rating_row.rating_grade if rating_row else None,
                    "last_updated": str(rating_row.last_evaluated_on) if rating_row and rating_row.last_evaluated_on else None,
                    "explanation": rating_row.rating_explanation if rating_row else None
                } if rating_row and rating_row.rating_grade else None,
                "total_capital": total_capital
            },
            "financial_history": [
                {
                    "year": f.year,
                    "turnover": safe_float(f.turnover),
                    "profit": safe_float(f.profit),
                    "employees": f.employees,
                    # Balance Sheet & Ratios
                    "total_assets": safe_float(f.total_assets),
                    "equity": safe_float(f.equity),
                    "current_liabilities": safe_float(f.current_liabilities),
                    "non_current_liabilities": safe_float(f.non_current_liabilities),
                    "total_current_assets": safe_float(f.total_current_assets),
                    "cash_balance": safe_float(f.cash_balance),
                    "accounts_receivable": safe_float(f.accounts_receivable),
                    "inventories": safe_float(f.inventories),
                    # Income Statement
                    "labour_costs": safe_float(f.by_nature_labour_expenses),
                    "interest_payment": safe_float(f.interest_expenses),
                    "depreciation": safe_float(f.depreciation_expenses),
                    "corporate_income_tax": safe_float(f.provision_for_income_taxes),
                    # Ratios
                    "current_ratio": safe_float(f.current_ratio),
                    "quick_ratio": safe_float(f.quick_ratio),
                    "cash_ratio": safe_float(f.cash_ratio),
                    "net_profit_margin": safe_float(f.net_profit_margin),
                    "roe": safe_float(f.roe),
                    "roa": safe_float(f.roa),
                    "debt_to_equity": safe_float(f.debt_to_equity),
                    "equity_ratio": safe_float(f.equity_ratio),
                    "ebitda": safe_float(f.ebitda),
                    # Cash flow (Short names for frontend RawDataAccordions)
                    "cfo": safe_float(f.cfo_im_net_operating_cash_flow),
                    "cfi": safe_float(f.cfi_acquisition_of_fixed_assets_intangible_assets),
                    "cff": safe_float(f.cff_net_financing_cash_flow),
                    "taxes_paid_cf": safe_float(f.cfo_im_income_taxes_paid),
                    # Long names if needed elsewhere
                    "net_operating_cash_flow": safe_float(f.cfo_im_net_operating_cash_flow),
                    "acquisition_of_fixed_assets": safe_float(f.cfi_acquisition_of_fixed_assets_intangible_assets),
                    "net_financing_cash_flow": safe_float(f.cff_net_financing_cash_flow)
                } for f in fin_history_rows
            ],
            "officers": officers,
            "members": members,
            "ubos": ubos,
            "risks": risks_by_type,
            "total_risk_score": total_risk_score,
            "risk_level": "CRITICAL" if total_risk_score >= 100 else "HIGH" if total_risk_score >= 50 else "MEDIUM" if total_risk_score >= 30 else "LOW" if total_risk_score > 0 else "NONE",
            "graph": graph_data,
            "tax_history": processed_tax_history,
            "procurements": processed_procurements,
            # 🚀 PARALLEL: Collect results from background threads
            "benchmark": benchmark_future.result(),
            "competitors": competitors_future.result()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching full data for {regcode}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        executor.shutdown(wait=False)


# ================================================================================
# LAZY-LOAD ENDPOINTS (For faster initial page render)
# ================================================================================

@router.get("/companies/{regcode}/financial-history")
async def get_financial_history_endpoint(regcode: str, response: Response):
    """
    Lazy-load endpoint for full financial history.
    Called by frontend AFTER initial page render.
    """
    response.headers["Cache-Control"] = "public, max-age=3600"
    
    with engine.connect() as conn:
        fin_rows = conn.execute(text("""
            SELECT year, turnover, profit, employees, cash_balance,
                   current_ratio, quick_ratio, cash_ratio,
                   net_profit_margin, roe, roa, debt_to_equity, equity_ratio, ebitda,
                   -- Extended fields for advanced financial analysis
                   total_assets, equity, current_liabilities, total_current_assets,
                   accounts_receivable, by_nature_labour_expenses,
                   cfo_im_net_operating_cash_flow, cfo_im_income_taxes_paid,
                   cfi_acquisition_of_fixed_assets_intangible_assets, cff_net_financing_cash_flow,
                   -- Fix: Select missing columns
                   interest_expenses, depreciation_expenses, provision_for_income_taxes,
                   inventories, non_current_liabilities
            FROM financial_reports 
            WHERE company_regcode = :r 
            ORDER BY year DESC
        """), {"r": regcode}).fetchall()
        
        history = []
        prev_turnover = None
        prev_profit = None
        
        fin_list = list(fin_rows)
        fin_list.reverse()
        
        for f in fin_list:
            row = {
                "year": f.year,
                "turnover": safe_float(f.turnover),
                "profit": safe_float(f.profit),
                "employees": f.employees,
                "cash_balance": safe_float(f.cash_balance),
                "turnover_growth": None,
                "profit_growth": None,
                "current_ratio": safe_float(f.current_ratio),
                "quick_ratio": safe_float(f.quick_ratio),
                "cash_ratio": safe_float(f.cash_ratio),
                "net_profit_margin": safe_float(f.net_profit_margin),
                "roe": safe_float(f.roe),
                "roa": safe_float(f.roa),
                "debt_to_equity": safe_float(f.debt_to_equity),
                "equity_ratio": safe_float(f.equity_ratio),
                "ebitda": safe_float(f.ebitda),
                # Extended fields - P&L
                "labour_costs": safe_float(f.by_nature_labour_expenses),
                "interest_payment": safe_float(f.interest_expenses),
                "depreciation": safe_float(f.depreciation_expenses),
                "corporate_income_tax": safe_float(f.provision_for_income_taxes),
                # Extended fields - Balance Sheet
                "total_assets": safe_float(f.total_assets),
                "equity": safe_float(f.equity),
                "current_liabilities": safe_float(f.current_liabilities),
                "non_current_liabilities": safe_float(f.non_current_liabilities),
                "total_current_assets": safe_float(f.total_current_assets),
                "accounts_receivable": safe_float(f.accounts_receivable),
                "inventories": safe_float(f.inventories),
                # Extended fields - Cash Flow (mapped to short keys for frontend)
                "cfo": safe_float(f.cfo_im_net_operating_cash_flow),
                "taxes_paid_cf": safe_float(f.cfo_im_income_taxes_paid),
                "cfi": safe_float(f.cfi_acquisition_of_fixed_assets_intangible_assets),
                "cff": safe_float(f.cff_net_financing_cash_flow)
            }
            
            if prev_turnover and f.turnover and prev_turnover != 0:
                row["turnover_growth"] = round(((float(f.turnover) - prev_turnover) / abs(prev_turnover)) * 100, 1)
            if prev_profit and f.profit and prev_profit != 0:
                row["profit_growth"] = round(((float(f.profit) - prev_profit) / abs(prev_profit)) * 100, 1)
            
            prev_turnover = safe_float(f.turnover)
            prev_profit = safe_float(f.profit)
            history.append(row)
        
        history.reverse()
        return {"financial_history": history}


@router.get("/companies/{regcode}/tax-history")
async def get_tax_history_endpoint(regcode: str, response: Response):
    """Lazy-load endpoint for tax payment history."""
    response.headers["Cache-Control"] = "public, max-age=3600"
    
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT year, total_tax_paid, labor_tax_iin, social_tax_vsaoi, avg_employees, nace_code
            FROM tax_payments 
            WHERE company_regcode = :r 
            ORDER BY year DESC
        """), {"r": regcode}).fetchall()
        
        history = []
        VSAOI_RATE = 0.3409
        
        for t in rows:
            row = {
                "year": t.year,
                "total_tax_paid": safe_float(t.total_tax_paid),
                "labor_tax_iin": safe_float(t.labor_tax_iin),
                "social_tax_vsaoi": safe_float(t.social_tax_vsaoi),
                "avg_employees": safe_float(t.avg_employees),
                "nace_code": t.nace_code,
                "avg_gross_salary": None,
                "avg_net_salary": None
            }
            
            if t.social_tax_vsaoi and t.avg_employees and float(t.avg_employees) > 0:
                vsaoi = float(t.social_tax_vsaoi)
                employees = float(t.avg_employees)
                gross_yearly = vsaoi / VSAOI_RATE
                gross_monthly = gross_yearly / employees / 12
                row["avg_gross_salary"] = round(gross_monthly, 2)
                
                vsaoi_employee = gross_monthly * 0.105
                iin = (gross_monthly - vsaoi_employee) * 0.20
                net_monthly = gross_monthly - vsaoi_employee - iin
                row["avg_net_salary"] = round(net_monthly, 2)
                
            history.append(row)
        return {"tax_history": history}


@router.get("/companies/{regcode}/procurements")
async def get_procurements_endpoint(regcode: str, response: Response, limit: int = 50):
    """Lazy-load endpoint for procurement history."""
    response.headers["Cache-Control"] = "public, max-age=3600"
    
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT authority_name, subject, amount, contract_date, contract_end_date, termination_date, procurement_id, part_number
            FROM procurements WHERE winner_regcode = :r
            ORDER BY contract_date DESC LIMIT :limit
        """), {"r": regcode, "limit": limit}).fetchall()
        
        # Aggregation Logic
        aggregated = {}
        history = []
        
        for p in rows:
            # If procurement_id exists, use it for grouping, otherwise use subject+date as fallback key
            key = p.procurement_id if p.procurement_id else f"{p.subject}_{p.contract_date}"
            
            if key in aggregated:
                # Aggregate
                existing = aggregated[key]
                existing["amount"] += safe_float(p.amount)
                if p.part_number and str(p.part_number).lower() != 'nan':
                    existing["parts"].append(p.part_number)
            else:
                # New entry
                entry = {
                    "authority": p.authority_name, 
                    "subject": p.subject,
                    "amount": safe_float(p.amount), 
                    "date": str(p.contract_date),
                    "end_date": str(p.contract_end_date) if p.contract_end_date else None,
                    "termination_date": str(p.termination_date) if p.termination_date else None,
                    "parts": [p.part_number] if p.part_number and str(p.part_number).lower() != 'nan' else []
                }
                aggregated[key] = entry
                history.append(entry) # Keep order

        # Format parts as string
        for entry in history:
            if len(entry["parts"]) > 0:
                # Numeric sort if possible
                try:
                    sorted_parts = sorted(entry["parts"], key=lambda x: float(x) if x.replace('.','',1).isdigit() else x)
                except:
                    sorted_parts = sorted(entry["parts"])
                entry["parts_text"] = ", ".join(sorted_parts)
            else:
                entry["parts_text"] = None
            del entry["parts"]

        return {"procurements": history}


@router.get("/companies/{regcode}/persons")
async def get_persons_endpoint(regcode: str, response: Response):
    """Lazy-load endpoint for UBOs, members, and officers."""
    response.headers["Cache-Control"] = "public, max-age=3600"
    
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT person_name, person_code, role, share_percent, date_from, birth_date,
                   position, rights_of_representation, representation_with_at_least,
                   number_of_shares, share_nominal_value, share_currency, legal_entity_regcode,
                   nationality, residence
            FROM persons WHERE company_regcode = :r
        """), {"r": regcode}).fetchall()
        
        # Try to get total capital from company first if possible
        company_reg = conn.execute(text("SELECT total_capital FROM companies WHERE regcode = :r"), {"r": regcode}).fetchone()
        db_total_capital = float(company_reg.total_capital) if company_reg and company_reg.total_capital else 0

        calc_total_capital = sum((float(p.number_of_shares or 0) * float(p.share_nominal_value or 0)) for p in rows if p.role == 'member')
        total_capital = max(calc_total_capital, db_total_capital)
        
        ubos, members, officers = [], [], []
        
        for p in rows:
            birth_date = str(p.birth_date) if hasattr(p, 'birth_date') and p.birth_date else None
            if p.role == 'ubo':
                ubos.append({
                    "name": p.person_name, "person_code": p.person_code, "nationality": p.nationality,
                    "residence": p.residence, "registered_on": str(p.date_from) if p.date_from else None,
                    "birth_date": birth_date
                })
            elif p.role == 'member':
                share_value = float(p.number_of_shares or 0) * float(p.share_nominal_value or 0)
                percent = (share_value / total_capital * 100) if total_capital > 0 else 0
                if (percent == 0 or percent is None) and hasattr(p, 'share_percent') and p.share_percent:
                    percent = float(p.share_percent)

                # Back-calculate value if missing
                if share_value == 0 and percent > 0 and total_capital > 0:
                    share_value = total_capital * (percent / 100)

                members.append({
                    "name": p.person_name, "person_code": p.person_code, "legal_entity_regcode": int(p.legal_entity_regcode) if p.legal_entity_regcode else None,
                    "number_of_shares": int(p.number_of_shares) if p.number_of_shares else None,
                    "share_value": round(share_value, 2), "share_currency": p.share_currency or "EUR",
                    "percent": round(percent, 2), "date_from": str(p.date_from) if p.date_from else None,
                    "birth_date": birth_date
                })
            elif p.role == 'officer':
                officers.append({
                    "name": p.person_name, "person_code": p.person_code, "position": p.position,
                    "rights_of_representation": p.rights_of_representation,
                    "representation_with_at_least": int(p.representation_with_at_least) if p.representation_with_at_least else None,
                    "registered_on": str(p.date_from) if p.date_from else None,
                    "birth_date": birth_date
                })
                
        return {"ubos": ubos, "members": members, "officers": officers, "total_capital": total_capital}


@router.get("/companies/{regcode}/risks")
async def get_risks_endpoint(regcode: str, response: Response):
    """Lazy-load endpoint for risks."""
    response.headers["Cache-Control"] = "public, max-age=3600"
    
    risks_by_type, total_risk_score = get_risks(regcode)
    
    # Calculate level for consistency
    risk_level = "CRITICAL" if total_risk_score >= 100 else "HIGH" if total_risk_score >= 50 else "MEDIUM" if total_risk_score >= 30 else "LOW" if total_risk_score > 0 else "NONE"
    
    return {
        "risks": risks_by_type,
        "total_risk_score": total_risk_score,
        "risk_level": risk_level
    }


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
    
    if result and result.owner_value and result.total_capital and safe_float(result.total_capital) > 0:
        return (safe_float(result.owner_value) / safe_float(result.total_capital)) * 100
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
    
    return [{"regcode": r.owner_regcode, "name": r.owner_name, "percent": safe_float(r.ownership_percent)} for r in result]


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
    Find all linked entities through ownership chain using PostgreSQL Recursive CTE.
    
    PERFORMANCE: Replaces Python recursion (N+1 queries) with single SQL query.
    E kritērijs: Ja A→B un B→C (>50%), tad A↔C ir saistīti.
    """
    # Use Recursive CTE for single-query traversal
    result = conn.execute(text("""
        WITH RECURSIVE ownership_tree AS (
            -- 1. STARTING POINT: Direct owners and subsidiaries of target company
            SELECT 
                p.company_regcode,
                p.legal_entity_regcode,
                p.person_name,
                p.number_of_shares,
                p.share_nominal_value,
                1 as depth,
                CASE 
                    WHEN p.legal_entity_regcode IS NOT NULL THEN 'upstream'
                    ELSE 'downstream'
                END as direction
            FROM persons p
            WHERE (p.company_regcode = :start_reg OR p.legal_entity_regcode = :start_reg)
              AND p.role = 'member'

            UNION ALL

            -- 2. RECURSION: Follow the ownership chain
            SELECT 
                p.company_regcode,
                p.legal_entity_regcode,
                p.person_name,
                p.number_of_shares,
                p.share_nominal_value,
                ot.depth + 1,
                ot.direction
            FROM persons p
            JOIN ownership_tree ot ON (
                -- Upstream: find owners of owners
                (ot.direction = 'upstream' AND p.company_regcode = ot.legal_entity_regcode)
                OR
                -- Downstream: find subsidiaries of subsidiaries  
                (ot.direction = 'downstream' AND p.legal_entity_regcode = ot.company_regcode)
            )
            WHERE ot.depth < :max_depth
              AND p.role = 'member'
              AND p.legal_entity_regcode IS NOT NULL
        ),
        -- Calculate ownership percentages
        with_percentages AS (
            SELECT 
                ot.*,
                c.name as entity_name,
                CASE ot.direction
                    WHEN 'upstream' THEN ot.legal_entity_regcode
                    ELSE ot.company_regcode
                END as target_regcode,
                SUM(ot.number_of_shares * ot.share_nominal_value) OVER (PARTITION BY ot.company_regcode, ot.legal_entity_regcode) as share_value,
                SUM(ot.number_of_shares * ot.share_nominal_value) OVER (PARTITION BY ot.company_regcode) as total_capital
            FROM ownership_tree ot
            LEFT JOIN companies c ON c.regcode = COALESCE(ot.legal_entity_regcode, ot.company_regcode)
        )
        SELECT DISTINCT
            target_regcode as regcode,
            entity_name as name,
            direction,
            depth,
            CASE WHEN total_capital > 0 THEN (share_value / total_capital * 100) ELSE NULL END as percent
        FROM with_percentages
        WHERE target_regcode != :start_reg
          AND target_regcode IS NOT NULL
    """), {"start_reg": start_regcode, "max_depth": max_depth}).fetchall()
    
    # Convert to expected format, filtering for >50% (linked)
    all_linked = []
    seen = set()
    
    for row in result:
        if row.regcode and row.regcode not in seen:
            # Only include if >50% ownership (linked status)
            if row.percent and row.percent > 50:
                seen.add(row.regcode)
                all_linked.append({
                    "regcode": row.regcode,
                    "name": row.name or f"Company {row.regcode}",
                    "relation": "owner" if row.direction == "upstream" else "subsidiary",
                    "ownership_percent": round(row.percent, 2) if row.percent else None,
                    "chain_depth": row.depth,
                    "chain_type": row.direction
                })
    
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
        "percent": safe_float(r.ownership_percent) if r.ownership_percent else 0
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
            "ownership_percent": safe_float(r.ownership_percent) if r.ownership_percent else 0,
            "classification": r.classification
        })
    
    logger.info(f"[PERSON] Found {len(companies)} companies for '{person_name}'")
    return companies


def find_all_companies_via_persons_bulk(conn, regcode: int) -> list:
    """
    PERFORMANCE: Find ALL companies controlled by significant persons in ONE query.
    
    Replaces the N+1 pattern of:
    - Get N significant persons
    - For each person, query their other companies
    
    With single SQL query that:
    1. Finds all persons with ≥25% in target company
    2. Finds all other companies where those persons have ≥25%
    """
    result = conn.execute(text("""
        WITH target_owners AS (
            -- Step 1: Find all significant owners (≥25%) of target company
            SELECT 
                p.person_name,
                p.person_code,
                SUM(p.number_of_shares * p.share_nominal_value) as person_value,
                (SELECT SUM(number_of_shares * share_nominal_value) 
                 FROM persons WHERE company_regcode = :r AND role = 'member') as total_capital
            FROM persons p
            WHERE p.company_regcode = :r
              AND p.role = 'member'
              AND p.legal_entity_regcode IS NULL
            GROUP BY p.person_name, p.person_code
            HAVING SUM(p.number_of_shares * p.share_nominal_value) / 
                   NULLIF((SELECT SUM(number_of_shares * share_nominal_value) 
                          FROM persons WHERE company_regcode = :r AND role = 'member'), 0) >= 0.25
        ),
        -- Step 2: Find all OTHER companies where these persons are owners
        other_companies AS (
            SELECT 
                p.company_regcode,
                c.name as company_name,
                c.nace_code,
                c.nace_section,
                tow.person_name,
                tow.person_code,
                (tow.person_value / NULLIF(tow.total_capital, 0) * 100) as person_percent_in_target,
                SUM(p.number_of_shares * p.share_nominal_value) as person_value_in_other,
                (SELECT SUM(number_of_shares * share_nominal_value) 
                 FROM persons WHERE company_regcode = p.company_regcode AND role = 'member') as other_total_capital
            FROM persons p
            JOIN target_owners tow ON (
                LOWER(TRIM(p.person_name)) = LOWER(TRIM(tow.person_name))
                AND (
                    tow.person_code IS NULL 
                    OR p.person_code LIKE SPLIT_PART(tow.person_code, '-', 1) || '%'
                )
            )
            JOIN companies c ON c.regcode = p.company_regcode
            WHERE p.company_regcode != :r
              AND p.role = 'member'
              AND p.legal_entity_regcode IS NULL
            GROUP BY p.company_regcode, c.name, c.nace_code, c.nace_section, 
                     tow.person_name, tow.person_code, tow.person_value, tow.total_capital
        )
        SELECT 
            company_regcode as regcode,
            company_name as name,
            nace_code,
            nace_section,
            person_name,
            person_code,
            person_percent_in_target,
            COALESCE((person_value_in_other / NULLIF(other_total_capital, 0)) * 100, 0) as ownership_percent,
            CASE 
                WHEN (person_value_in_other / NULLIF(other_total_capital, 0)) > 0.5 THEN 'linked'
                WHEN (person_value_in_other / NULLIF(other_total_capital, 0)) >= 0.25 THEN 'partner'
                ELSE 'minor'
            END as classification
        FROM other_companies
        WHERE (person_value_in_other / NULLIF(other_total_capital, 0)) >= 0.25
    """), {"r": regcode}).fetchall()
    
    return [{
        "regcode": r.regcode,
        "name": r.name,
        "nace_code": r.nace_code,
        "nace_section": r.nace_section,
        "controlling_person": r.person_name,
        "person_code": r.person_code,
        "person_percent": safe_float(r.person_percent_in_target) if r.person_percent_in_target else 0,
        "ownership_percent": safe_float(r.ownership_percent) if r.ownership_percent else 0,
        "classification": r.classification
    } for r in result]


def find_all_linked_entities(conn, regcode: int, year: int = 2024) -> dict:
    """
    Galvenā funkcija: Atrod VISUS saistītos uzņēmumus pēc ES MVU noteikumiem.
    
    Ietver:
    - A1/A2: Tiešā kapitāla/balsstiesību kontrole (>50%)
    - E: Ķēdes efekts (A→B→C = A↔C saistīti)
    - F1: Fiziskās personas kontrole (viena persona kontrolē vairākus uzņēmumus)
    - NACE pārbaude: Fizisko personu grupām jābūt tajā pašā/blakustirgū
    """
    
    # Get company info including NACE code for market comparison
    company = conn.execute(text("""
        SELECT name, nace_code, nace_section 
        FROM companies WHERE regcode = :r
    """), {"r": regcode}).fetchone()
    if not company:
        return {"linked": [], "partners": [], "via_person": [], "needs_confirmation": []}
    
    company_name = company.name
    company_nace = company.nace_code  # Full NACE code (e.g., "62.01")
    nace_prefix = company_nace[:2] if company_nace else None  # First 2 digits for market comparison

    
    all_linked = []
    all_partners = []
    via_person = []
    seen_regcodes = set([regcode])  # Don't include self
    needs_confirmation = []  # Companies that need manual NACE confirmation
    
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
    
    # 2. Physical person control (F1 criterion) - BULK QUERY
    # PERFORMANCE: Single query finds all companies controlled by all significant persons
    logger.info(f"[LINKED] Finding companies via physical persons for {regcode}")
    person_controlled = find_all_companies_via_persons_bulk(conn, regcode)
    logger.info(f"[LINKED] Found {len(person_controlled)} companies via physical persons")
    
    for other in person_controlled:
        if other["regcode"] not in seen_regcodes:
            seen_regcodes.add(other["regcode"])
            
            # Check NACE code match (same market = first 2 digits match)
            other_nace = other.get("nace_code") or ""
            other_nace_prefix = other_nace[:2] if other_nace else None
            same_market = (nace_prefix == other_nace_prefix) if (nace_prefix and other_nace_prefix) else False
            
            entry = {
                "regcode": other["regcode"],
                "name": other["name"],
                "ownership_percent": other["ownership_percent"],
                "controlling_person": other["controlling_person"],
                "person_percent": other["person_percent"],
                "relation": "via_person",
                "classification": other["classification"],
                "nace_code": other_nace,
                "same_market": same_market,
                "link_reason": f"Kontrolē {other['controlling_person']} ({other['person_percent']:.1f}%)"
            }
            
            # Classify based on person's ownership AND market similarity
            if other["classification"] == "linked":
                if same_market:
                    # >50% in same market = LINKED (automatic)
                    entry["link_reason"] += " - tā pati nozare"
                    all_linked.append(entry)
                else:
                    # >50% in different market = needs confirmation
                    entry["needs_confirmation"] = True
                    entry["link_reason"] += " - cita nozare (jāapstiprina)"
                    needs_confirmation.append(entry)
            else:
                # 25-50% in other company = via_person (show separately)
                via_person.append(entry)
    
    logger.info(f"[LINKED] Found {len(via_person)} companies via physical person control")
    logger.info(f"[LINKED] Found {len(needs_confirmation)} companies needing NACE confirmation")
    
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
                "ownership_percent": safe_float(p.ownership_percent),
                "relation": "owner",
                "entity_type": "legal_entity"
            })
        elif not p.partner_regcode and p.person_code:
            # Physical person partner
            all_partners.append({
                "regcode": None,
                "name": p.partner_name,
                "ownership_percent": safe_float(p.ownership_percent),
                "relation": "owner",
                "entity_type": "physical_person"
            })
    
    # 4. Get LINKED entities' partners (spec: Linked's partner = our partner)
    # X → Linked B (100%) → Partner C (30%) = C is partner of X
    for linked_entity in all_linked:
        linked_regcode = linked_entity.get("regcode")
        if not linked_regcode:
            continue
        
        linked_partners_result = conn.execute(text("""
            WITH company_capital AS (
                SELECT SUM(number_of_shares * share_nominal_value) as total
                FROM persons WHERE company_regcode = :r AND role = 'member'
            )
            SELECT 
                p.legal_entity_regcode as partner_regcode,
                p.person_name as partner_name,
                SUM(p.number_of_shares * p.share_nominal_value) as value,
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
            HAVING (SUM(p.number_of_shares * p.share_nominal_value) / NULLIF(cc.total, 0)) BETWEEN 0.25 AND 0.50
        """), {"r": linked_regcode}).fetchall()
        
        for lp in linked_partners_result:
            if lp.partner_regcode and lp.partner_regcode not in seen_regcodes:
                seen_regcodes.add(lp.partner_regcode)
                all_partners.append({
                    "regcode": lp.partner_regcode,
                    "name": lp.partner_name,
                    "ownership_percent": safe_float(lp.ownership_percent),
                    "relation": "owner",
                    "entity_type": "legal_entity",
                    "via_linked": linked_entity["name"],
                    "link_reason": f"Saistītā {linked_entity['name']} partneris ({lp.ownership_percent:.1f}%)"
                })
    
    logger.info(f"[LINKED] Final: {len(all_linked)} linked, {len(all_partners)} partners, {len(needs_confirmation)} pending")
    
    return {
        "linked": all_linked,
        "partners": all_partners,
        "via_person": via_person,
        "needs_confirmation": needs_confirmation,
        "company_nace": company_nace,
        "total_linked_count": len(all_linked) + len(via_person)
    }

from app.services.graph_service import calculate_company_graph


def save_cached_graph(conn, regcode: int, data: dict):
    """Save computed graph to cache"""
    try:
        import json
        # Ensure table exists
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS company_graph_cache (
                company_regcode BIGINT PRIMARY KEY,
                graph_data JSONB,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Upsert
        conn.execute(text("""
            INSERT INTO company_graph_cache (company_regcode, graph_data, updated_at)
            VALUES (:r, :d, NOW())
            ON CONFLICT (company_regcode) 
            DO UPDATE SET graph_data = :d, updated_at = NOW()
        """), {"r": regcode, "d": json.dumps(data)})
        conn.commit()
        logger.info(f"[CACHE] Saved graph for company {regcode}")
    except Exception as e:
        logger.error(f"[CACHE] Error saving cache: {e}")

@router.get("/companies/{regcode}/graph")
def get_related_companies(regcode: int, year: int = 2024):
    """
    Returns comprehensive company relationship data (EU SME classification).
    """
    with engine.connect() as conn:
        return _get_graph_data_internal(conn, regcode, year)

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
    
    # Financial cache for bulk prefetch optimization (N+1 fix)
    _fin_cache = {}
    
    def get_financial_data(conn, related_regcode: int, year: int):
        """Get financial data from cache or single query as fallback"""
        if not related_regcode:
            return {"employees": None, "turnover": None, "balance": None}
        
        # Check cache first
        if related_regcode in _fin_cache:
            return _fin_cache[related_regcode]
        
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
            SELECT person_name, position, person_code
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
                p.person_name, p.number_of_shares, p.share_nominal_value, p.person_code,
                p.legal_entity_regcode, c.name as legal_entity_name
            FROM persons p
            LEFT JOIN companies c ON c.regcode = p.legal_entity_regcode
            WHERE p.company_regcode = :r AND p.role = 'member'
        """), {"r": regcode}).fetchall()
        
        # PERFORMANCE: Bulk prefetch financials for all owner legal entities (N+1 fix)
        owner_regcodes = [o.legal_entity_regcode for o in owners if o.legal_entity_regcode]
        if owner_regcodes:
            _fin_cache.update(bulk_fetch_financials(conn, owner_regcodes, year))
        
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
                
                person_hash = get_person_hash(owner.person_code) if not is_legal_entity else None

                entry = {
                    "name": owner.person_name,
                    "regcode": owner.legal_entity_regcode,
                    "person_hash": person_hash,
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
                "authorized_person_hash": get_person_hash(auth_person.person_code) if auth_person else None,
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


