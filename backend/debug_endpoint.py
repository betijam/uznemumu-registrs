import time
import logging
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import text
from app.core.database import engine

# Mock functions to simulate DB work
def get_financial_history(regcode):
    with engine.connect() as conn:
        conn.execute(text("SELECT 1")).fetchall()
    return []

def get_risks(regcode):
    with engine.connect() as conn:
        conn.execute(text("SELECT 1")).fetchall()
    return [], 0

def get_persons(regcode):
    with engine.connect() as conn:
        conn.execute(text("SELECT 1")).fetchall()
    return [], [], [], 0

def get_procurements(regcode):
    with engine.connect() as conn:
        conn.execute(text("SELECT 1")).fetchall()
    return []

def get_rating(regcode):
    with engine.connect() as conn:
        conn.execute(text("SELECT 1")).fetchall()
    return None

def get_tax_history(regcode):
    with engine.connect() as conn:
        conn.execute(text("SELECT 1")).fetchall()
    return []

def test_parallel(regcode):
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=6) as executor:
        f_fin = executor.submit(get_financial_history, regcode)
        f_risk = executor.submit(get_risks, regcode)
        f_pers = executor.submit(get_persons, regcode)
        f_proc = executor.submit(get_procurements, regcode)
        f_rate = executor.submit(get_rating, regcode)
        f_tax = executor.submit(get_tax_history, regcode)
        
        r1 = f_fin.result()
        r2 = f_risk.result()
        r3 = f_pers.result()
        r4 = f_proc.result()
        r5 = f_rate.result()
        r6 = f_tax.result()
        
    print(f"Parallel Time: {time.time() - start_time:.4f}s")

def test_sequential(regcode):
    start_time = time.time()
    r1 = get_financial_history(regcode)
    r2 = get_risks(regcode)
    r3 = get_persons(regcode)
    r4 = get_procurements(regcode)
    r5 = get_rating(regcode)
    r6 = get_tax_history(regcode)
    print(f"Sequential Time: {time.time() - start_time:.4f}s")

if __name__ == "__main__":
    regcode = 40003041848
    print("--- WARMUP ---")
    test_sequential(regcode)
    test_parallel(regcode)
    
    print("\n--- TEST ---")
    test_sequential(regcode)
    test_parallel(regcode)
