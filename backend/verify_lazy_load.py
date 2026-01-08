from app.routers.companies import (
    get_financial_history, get_tax_history, get_procurements, 
    get_persons, get_risks
)
from app.routers.benchmarking import get_company_benchmark, get_top_competitors
from app.services.graph_service import calculate_company_graph
from app.core.database import engine
from sqlalchemy import text
import time

REGCODE = 40003041848

def test_quick():
    with engine.connect() as conn:
        start = time.time()
        # Simulate the query from check_quick
        conn.execute(text("SELECT * FROM companies WHERE regcode = :r"), {"r": REGCODE}).fetchone()
        conn.execute(text("SELECT * FROM financial_reports WHERE company_regcode = :r ORDER BY year DESC LIMIT 1"), {"r": REGCODE}).fetchone()
        print(f"[Quick Load] {time.time() - start:.4f}s (Target: <0.2s)")

def test_lazy_parallel():
    print("\n--- Simulating Lazy Fetching ---")
    
    start_total = time.time()
    
    # Financials
    s = time.time()
    get_financial_history(REGCODE)
    print(f"[Financials] {time.time() - s:.4f}s")
    
    # Tax
    s = time.time()
    get_tax_history(REGCODE)
    print(f"[Tax History] {time.time() - s:.4f}s")

    # Persons
    s = time.time()
    get_persons(REGCODE)
    print(f"[Persons] {time.time() - s:.4f}s")

    # Procurements
    s = time.time()
    get_procurements(REGCODE)
    print(f"[Procurements] {time.time() - s:.4f}s")

    # Risks
    s = time.time()
    get_risks(REGCODE)
    print(f"[Risks] {time.time() - s:.4f}s")

    # Graph
    s = time.time()
    with engine.connect() as conn:
        calculate_company_graph(conn, REGCODE)
    print(f"[Graph] {time.time() - s:.4f}s")

    # Benchmark
    s = time.time()
    get_company_benchmark(REGCODE)
    print(f"[Benchmark] {time.time() - s:.4f}s")
    
    # Competitors
    s = time.time()
    get_top_competitors(REGCODE)
    print(f"[Competitors] {time.time() - s:.4f}s")

    print(f"--- Total Background Work: {time.time() - start_total:.4f}s ---")

if __name__ == "__main__":
    test_quick()
    test_lazy_parallel()

