"""Check share_percent data in persons table"""
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    # Check share_percent availability
    print("=== Share Percent Data ===")
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_members,
            COUNT(share_percent) as with_share_percent,
            COUNT(number_of_shares) as with_number_of_shares,
            AVG(share_percent) as avg_share_percent
        FROM persons 
        WHERE role = 'member'
    """)).fetchone()
    
    print(f"Total members: {result.total_members:,}")
    print(f"With share_percent: {result.with_share_percent:,}")
    print(f"With number_of_shares: {result.with_number_of_shares:,}")
    print(f"Avg share_percent: {result.avg_share_percent}")
    
    # Check if we need to calculate from number_of_shares
    print("\n=== Sample Member Data ===")
    result = conn.execute(text("""
        SELECT person_name, company_regcode, share_percent, number_of_shares, share_nominal_value
        FROM persons 
        WHERE role = 'member' 
        LIMIT 5
    """))
    for row in result:
        print(f"  {row.person_name}: share_percent={row.share_percent}, shares={row.number_of_shares}, nominal={row.share_nominal_value}")
    
    # Test wealth calculation with actual data
    print("\n=== Test Wealth Calculation ===")
    result = conn.execute(text("""
        SELECT 
            p.person_name,
            p.share_percent,
            f.equity,
            (COALESCE(p.share_percent, 0) / 100.0) * COALESCE(f.equity, 0) as calculated_worth
        FROM persons p
        JOIN companies c ON p.company_regcode = c.regcode
        LEFT JOIN (
            SELECT DISTINCT ON (company_regcode) company_regcode, equity
            FROM financial_reports WHERE year >= 2020
            ORDER BY company_regcode, year DESC
        ) f ON c.regcode = f.company_regcode
        WHERE p.role = 'member' 
          AND c.status = 'active'
          AND f.equity > 0
          AND p.share_percent > 0
        ORDER BY calculated_worth DESC
        LIMIT 5
    """))
    for row in result:
        print(f"  {row.person_name}: {row.share_percent}% of €{row.equity:,.0f} = €{row.calculated_worth:,.0f}")
