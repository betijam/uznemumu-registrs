
import os
from sqlalchemy import create_engine, text
import json
from decimal import Decimal
from datetime import date, datetime

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ Error: DATABASE_URL not found in environment variables")
    exit(1)

engine = create_engine(DATABASE_URL)

def get_schema_info():
    schema_info = {}
    
    # Tables of interest requested by user
    target_tables = [
        'companies', 
        'persons', 
        'financial_reports', 
        'procurements', 
        'risks', 
        'tax_payments',
        # Territories and Industry might be named differently, let's find them
    ]
    
    with engine.connect() as conn:
        # 1. Find all relevant tables
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
        all_tables = [r[0] for r in result]
        
        # Match requested logic
        final_list = []
        for t in all_tables:
            if t in target_tables:
                final_list.append(t)
            elif 'territor' in t or 'atvk' in t: # flexible match for territories
                 final_list.append(t)
            elif 'industry' in t or 'nace' in t: # flexible match for industry
                 final_list.append(t)
        
        # 2. Get columns for each table
        for table in final_list:
            cols = conn.execute(text(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = '{table}'
                ORDER BY ordinal_position
            """)).fetchall()
            
            schema_info[table] = []
            for c in cols:
                schema_info[table].append({
                    "name": c.column_name,
                    "type": c.data_type,
                    "nullable": c.is_nullable == 'YES',
                    "default": str(c.column_default) if c.column_default else None
                })
                
    return schema_info

if __name__ == "__main__":
    result = get_schema_info()
    print(json.dumps(result, indent=2))
