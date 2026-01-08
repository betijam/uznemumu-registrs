from app.core.database import engine
from sqlalchemy import text
import time

def test_search(query):
    start = time.time()
    
    # Logic copied from search.py roughly
    query_words = query.strip().split()
    where_conditions = []
    params = {}
    
    for i, word in enumerate(query_words):
        # Use immutable_unaccent to hit the index we just created
        where_conditions.append(f"immutable_unaccent(lower(name)) LIKE immutable_unaccent(lower(:word{i}))")
        params[f"word{i}"] = f"%{word}%"
        
    where_clause = " AND ".join(where_conditions)
    sql = f"SELECT count(*) FROM companies WHERE {where_clause}"
    
    # Run EXPLAIN ANALYZE
    explain_sql = f"EXPLAIN ANALYZE SELECT count(*) FROM companies WHERE {where_clause}"
    
    with engine.connect() as conn:
        print(f"\n--- Plan for '{query}' ---")
        # We don't need to create extension every time, but we do need the function wrapper to exist (which it does now)
        try:
            result = conn.execute(text(explain_sql), params)
            for row in result:
                print(row[0])
        except Exception as e:
            print(f"Error explaining: {e}")
            
        # Actual run
        start = time.time()
        res = conn.execute(text(sql), params).scalar()
        
    duration = time.time() - start
    print(f"Search for '{query}': {duration:.4f}s (Found {res})")

if __name__ == "__main__":
    test_search("animas")
    test_search("latvijas gāze")
