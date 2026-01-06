"""
People Analytics API Router
Endpoints for "Latvijas Biznesa Elite" dashboard
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import text
from etl.loader import engine

router = APIRouter(prefix="/api/analytics/people", tags=["People Analytics"])


class PersonHighlight(BaseModel):
    person_hash: str
    full_name: str
    value: float
    label: str
    subtitle: Optional[str] = None
    main_company: Optional[str] = None
    primary_nace: Optional[str] = None


class PersonRanking(BaseModel):
    rank: int
    person_hash: str
    full_name: str
    value: float
    change: Optional[float] = None
    main_company: Optional[str] = None
    primary_nace: Optional[str] = None
    active_companies: int


class HighlightsResponse(BaseModel):
    top_wealth: Optional[PersonHighlight] = None
    top_active: Optional[PersonHighlight] = None
    top_manager: Optional[PersonHighlight] = None


# NACE section names
NACE_SECTIONS = {
    "01": "Lauksaimniecība", "10": "Pārtikas ražošana", "41": "Būvniecība",
    "46": "Vairumtirdzniecība", "47": "Mazumtirdzniecība", "49": "Transports",
    "55": "Viesnīcas", "56": "Restorāni", "62": "IT pakalpojumi",
    "64": "Finanšu pakalpojumi", "68": "Nekustamais īpašums", 
    "69": "Juridiskie pakalpojumi", "70": "Konsultācijas", "85": "Izglītība",
    "86": "Veselības aprūpe",
}


def get_nace_name(code: str) -> str:
    if not code:
        return "Nav norādīts"
    return NACE_SECTIONS.get(code[:2], f"Nozare {code}")


@router.get("/highlights", response_model=HighlightsResponse)
async def get_highlights():
    """Get top 3 highlighted persons for Elite Grid cards"""
    with engine.connect() as conn:
        # Top by wealth
        result = conn.execute(text("""
            SELECT person_hash, full_name, net_worth, main_company_name, primary_nace
            FROM person_analytics_cache WHERE net_worth > 0
            ORDER BY net_worth DESC LIMIT 1
        """))
        row = result.fetchone()
        top_wealth = PersonHighlight(
            person_hash=row.person_hash, full_name=row.full_name,
            value=float(row.net_worth or 0), label="Kapitāla vērtība #1",
            subtitle="Aprēķinātā daļu vērtība", main_company=row.main_company_name,
            primary_nace=get_nace_name(row.primary_nace)
        ) if row else None

        # Top by activity
        result = conn.execute(text("""
            SELECT person_hash, full_name, active_companies_count, main_company_name, primary_nace
            FROM person_analytics_cache ORDER BY active_companies_count DESC LIMIT 1
        """))
        row = result.fetchone()
        top_active = PersonHighlight(
            person_hash=row.person_hash, full_name=row.full_name,
            value=float(row.active_companies_count or 0), label="Visvairāk uzņēmumu #1",
            subtitle="Aktīvi uzņēmumi portfelī", main_company=row.main_company_name,
            primary_nace=get_nace_name(row.primary_nace)
        ) if row else None

        # Top by managed turnover
        result = conn.execute(text("""
            SELECT person_hash, full_name, managed_turnover, main_company_name, primary_nace
            FROM person_analytics_cache WHERE managed_turnover > 0
            ORDER BY managed_turnover DESC LIMIT 1
        """))
        row = result.fetchone()
        top_manager = PersonHighlight(
            person_hash=row.person_hash, full_name=row.full_name,
            value=float(row.managed_turnover or 0), label="Vadītais apgrozījums #1",
            subtitle="Kopējais valdes apgrozījums", main_company=row.main_company_name,
            primary_nace=get_nace_name(row.primary_nace)
        ) if row else None

        return HighlightsResponse(top_wealth=top_wealth, top_active=top_active, top_manager=top_manager)


@router.get("/rankings", response_model=List[PersonRanking])
async def get_rankings(
    type: str = Query("wealth", pattern="^(wealth|active|turnover)$"),
    limit: int = Query(50, ge=1, le=100)
):
    """Get ranked list of persons by specified metric"""
    with engine.connect() as conn:
        col_map = {"wealth": "net_worth", "active": "active_companies_count", "turnover": "managed_turnover"}
        order_col = col_map.get(type, "net_worth")

        result = conn.execute(text(f"""
            SELECT ROW_NUMBER() OVER (ORDER BY {order_col} DESC) as rank,
                person_hash, full_name, {order_col} as value,
                main_company_name, primary_nace, active_companies_count
            FROM person_analytics_cache WHERE {order_col} > 0
            ORDER BY {order_col} DESC LIMIT :limit
        """), {"limit": limit})

        return [PersonRanking(
            rank=row.rank, person_hash=row.person_hash, full_name=row.full_name,
            value=float(row.value or 0), main_company=row.main_company_name,
            primary_nace=get_nace_name(row.primary_nace), active_companies=row.active_companies_count
        ) for row in result]
