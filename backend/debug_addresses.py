import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/ur_db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

print("=== Checking address_objects type codes ===")
with engine.connect() as conn:
    result = conn.execute(text("SELECT tips_cd, COUNT(*) as cnt FROM core.address_objects GROUP BY tips_cd ORDER BY tips_cd"))
    for row in result:
        print(f"Type: {row.tips_cd} - Count: {row.cnt}")

print("\n=== Checking address_types ===")
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM core.address_types"))
    for row in result:
        print(f"Type: {row.tips_cd} - Name: {row.type_name} - Group: {row.type_group}")

print("\n=== Checking address_dimension count ===")
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM address_dimension"))
    count = result.scalar()
    print(f"Total rows: {count}")

print("\n=== Sample from address_dimension ===")
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM address_dimension LIMIT 5"))
    for row in result:
        print(f"ID: {row.address_id}, Address: {row.full_address}, City: {row.city_name}, Muni: {row.municipality_name}")

print("\n=== Checking a sample hierarchy ===")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT o.kods, o.tips_cd, o.nosaukums, o.vkur_cd, o.vkur_tips 
        FROM core.address_objects o 
        WHERE o.tips_cd = '109' 
        LIMIT 3
    """))
    for row in result:
        print(f"Kods: {row.kods}, Tipus: {row.tips_cd}, Nosaukums: {row.nosaukums}, Parent: {row.vkur_cd}/{row.vkur_tips}")
