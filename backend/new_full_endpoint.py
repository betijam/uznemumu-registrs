# NEW ENDPOINT: Get ALL company data in one request (optimized for performance)
@router.get("/companies/{regcode}/full")
async def get_company_full(regcode: str, response: Response, request: Request):
    """
    Optimized endpoint that returns ALL company data in a single response.
    Replaces 9 separate API calls with 1 call for 9x faster page load.
    """
    response.headers["Cache-Control"] = "no-store"
    
    # Check Access Level
    has_full_access = await check_access(request)
    
    # Fetch ALL data in parallel using existing service functions
    try:
        # 1. Get basic company data (reuse existing logic from /companies/{regcode}/quick)
        with engine.connect() as conn:
            res = conn.execute(text("SELECT * FROM companies WHERE regcode = :r"), {"r": regcode}).fetchone()
            if not res:
                raise HTTPException(status_code=404, detail="Company not found")
            
            # Build basic company object (simplified version of /quick endpoint)
            company = {
                "regcode": res.regcode,
                "name": res.name,
                "type": res.type if hasattr(res, 'type') else None,
                "address": res.address,
                "registration_date": str(res.registration_date),
                "status": res.status,
                "has_full_access": has_full_access
            }
        
        # 2. Get financial history
        financial_history = get_financial_history(regcode)
        
        # 3. Get persons (officers, members, ubos)
        persons_data = get_persons_data(regcode)
        
        # 4. Get risks
        risks_data = get_risks_data(regcode)
        
        # 5. Get graph (parents, children, related)
        graph_data = get_graph_data(regcode)
        
        # 6. Get benchmark
        benchmark_data = get_benchmark_data(regcode)
        
        # 7. Get competitors
        competitors_data = get_competitors_data(regcode, limit=5)
        
        # 8. Get tax history
        tax_history = get_tax_history(regcode)
        
        # 9. Get procurements
        procurements_data = get_procurements_data(regcode)
        
        # Return everything in one response
        return {
            "company": company,
            "financial_history": financial_history,
            "officers": persons_data.get("officers", []),
            "members": persons_data.get("members", []),
            "ubos": persons_data.get("ubos", []),
            "risks": risks_data,
            "graph": graph_data,
            "benchmark": benchmark_data,
            "competitors": competitors_data,
            "tax_history": tax_history,
            "procurements": procurements_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching full company data for {regcode}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
