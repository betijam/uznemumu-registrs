
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add parent directory to path to import app modules if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(database_url)

def create_materialized_view():
    print("Creating materialized view: company_stats_materialized...")
    
    with engine.connect() as conn:
        # Drop if exists
        conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS company_stats_materialized CASCADE;"))
        
        # Create View
        # We join companies with their latest financial report.
        # We use DISTINCT ON (company_regcode) in the subquery or LEFT JOIN LATERAL logic 
        # but for a materialized view, a window function usually performs well for selecting "latest".
        # However, since we want this to be robust, let's stick to the logic that filters for the latest year.
        
        sql = """
        CREATE MATERIALIZED VIEW company_stats_materialized AS
        SELECT
            c.regcode,
            c.name,
            c.nace_code,
            c.nace_text,
            c.nace_section,
            c.nace_section_text,
            c.company_size_badge,
            c.employee_count as c_employees,
            c.pvn_number,
            c.is_pvn_payer,
            c.status,
            f.year as data_year,
            f.turnover,
            f.profit,
            COALESCE(f.employees, c.employee_count) as employees,
            f.total_assets,
            f.equity
        FROM companies c
        JOIN LATERAL (
            SELECT turnover, profit, employees, year, total_assets, equity
            FROM financial_reports
            WHERE company_regcode = c.regcode
              AND turnover IS NOT NULL
              AND turnover > 0
              AND turnover < 1e15 -- Filter out anomalies
            ORDER BY year DESC
            LIMIT 1
        ) f ON true
        WHERE c.status = 'active';
        """
        
        conn.execute(text(sql))
        
        # Create Indexes for fast sorting and filtering
        print("Creating indexes...")
        conn.execute(text("CREATE INDEX idx_mv_turnover ON company_stats_materialized (turnover DESC);"))
        conn.execute(text("CREATE INDEX idx_mv_profit ON company_stats_materialized (profit DESC);"))
        conn.execute(text("CREATE INDEX idx_mv_nace_section ON company_stats_materialized (nace_section);"))
        conn.execute(text("CREATE UNIQUE INDEX idx_mv_regcode ON company_stats_materialized (regcode);"))
        
        conn.commit() # Important for DDL in some contexts, though engine usually autocommits or we need explicit commit
        
    print("Materialized view created successfully.")

if __name__ == "__main__":
    create_materialized_view()
