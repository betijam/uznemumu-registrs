import time
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

def verify_sql_performance():
    print("--- Verifying SQL Performance & Indexes ---")
    
    with engine.connect() as conn:
        # 1. Check if indexes exist
        print("\nChecking indexes:")
        indexes = conn.execute(text("""
            SELECT indexname FROM pg_indexes 
            WHERE indexname IN (
                'idx_companies_name_trgm', 
                'idx_persons_name_trgm', 
                'idx_companies_atvk_status',
                'idx_fin_reports_regcode_year_turnover'
            )
        """)).fetchall()
        for idx in indexes:
            print(f"  ✅ Found index: {idx[0]}")
        
        # 2. Test Search Query Relevance & Speed
        query = "ANIMAS"
        print(f"\nTesting search query for '{query}':")
        
        q_raw = query
        q_pattern = f"%{query}%"
        q_start = f"{query}%"
        
        sql = """
            WITH 
            q AS (SELECT immutable_unaccent(lower(:q_raw)) as val, :q_raw as raw_val),
            rank0 AS (
                SELECT name, 0 as rank, 0.0::float as dist
                FROM companies, q
                WHERE immutable_unaccent(lower(name)) LIKE q.val || '%'
                   OR immutable_unaccent(lower(name)) LIKE 'sia ' || q.val || '%'
                   OR immutable_unaccent(lower(name)) LIKE 'as ' || q.val || '%'
                   OR immutable_unaccent(lower(name)) LIKE 'sabiedriba ar ierobezotu atbildibu "' || q.val || '%'
                   OR immutable_unaccent(lower(name)) LIKE '"' || q.val || '%'
                LIMIT 7
            ),
            rank1 AS (
                SELECT name, 1 as rank,
                       (immutable_unaccent(lower(name)) <-> q.val) as dist
                FROM companies, q
                WHERE (
                    to_tsvector('simple', name) @@ to_tsquery('simple', q.raw_val || ':*')
                    OR immutable_unaccent(lower(name)) % q.val
                )
                  AND name NOT IN (SELECT name FROM rank0)
                LIMIT 7
            )
            SELECT * FROM rank0
            UNION ALL
            SELECT * FROM rank1
            ORDER BY rank, dist, name
            LIMIT 7
        """
        
        start_time = time.time()
        results = conn.execute(text(sql), {
            "q_raw": query
        }).fetchall()
        duration = time.time() - start_time
        
        print(f"Query duration: {duration:.4f}s")
        for i, row in enumerate(results):
            print(f"  {i+1}. {row.name} (Rank: {row.rank}, Dist: {row.dist:.4f})")

        # 3. Test Region Query Speed (Top Companies)
        print("\nTesting Region Top Companies query:")
        # Mocking a territory code (e.g., Riga - 0100000 or similar)
        territory_code = "0100000" 
        year = 2023
        
        sql_region = """
            EXPLAIN ANALYZE
            SELECT 
                c.regcode,
                c.name,
                fr.turnover
            FROM companies c
            JOIN financial_reports fr ON c.regcode = fr.company_regcode
               AND fr.year = :year
            WHERE c.atvk = :territory_code
              AND (c.status = 'active' OR c.status = 'A' OR c.status ILIKE 'aktīvs' OR c.status IS NULL OR c.status = '')
            ORDER BY fr.turnover DESC NULLS LAST
            LIMIT 5
        """
        
        start_time = time.time()
        # Using explain analyze to see index usage
        explain_results = conn.execute(text(sql_region), {
            "territory_code": territory_code,
            "year": year
        }).fetchall()
        duration = time.time() - start_time
        
        print(f"Region query duration: {duration:.4f}s")
        # print("\nExecution Plan Snippet:")
        # for row in explain_results[:10]:
        #    print(f"  {row[0]}")

if __name__ == "__main__":
    verify_sql_performance()
