import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import text
from app.core.database import engine
from app.routers.companies import build_full_profile
from app.services.graph_service import calculate_company_graph
from app.routers.benchmarking import get_company_benchmark, get_top_competitors

REGCODE = 40003041848

def mock_company_info():
    with engine.connect() as conn:
        return conn.execute(text("SELECT * FROM companies WHERE regcode = :r"), {"r": REGCODE}).fetchone()

def test_full_profile():
    start = time.time()
    info = mock_company_info()
    # Convert Row to dict for the function
    audit = {k: v for k, v in info._mapping.items()}
    build_full_profile(REGCODE, audit)
    print(f"[Profile] {time.time() - start:.4f}s")

def test_graph():
    start = time.time()
    with engine.connect() as conn:
        calculate_company_graph(conn, REGCODE)
    print(f"[Graph] {time.time() - start:.4f}s")

def test_benchmark():
    start = time.time()
    # get_company_benchmark expects just regcode, it handles connection internally
    get_company_benchmark(REGCODE) 
    print(f"[Benchmark] {time.time() - start:.4f}s")

def test_competitors():
    start = time.time()
    # get_top_competitors expects just regcode, it handles connection internally
    get_top_competitors(REGCODE, limit=5)
    print(f"[Competitors] {time.time() - start:.4f}s")

if __name__ == "__main__":
    print(f"Testing for Regcode: {REGCODE}")
    test_full_profile()
    test_graph()
    test_benchmark()
    test_competitors()
