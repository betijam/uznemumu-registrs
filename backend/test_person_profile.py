# Quick Test Script for Person Profile Feature
# Run this to get a test person code from your database

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv('../.env')
url = os.getenv("DATABASE_URL")

if not url:
    print("❌ DATABASE_URL not found!")
    exit(1)

engine = create_engine(url)

with engine.connect() as conn:
    # Get a sample person with their companies
    result = conn.execute(text("""
        SELECT DISTINCT 
            p.person_code,
            p.person_name,
            COUNT(DISTINCT p.company_regcode) as company_count
        FROM persons p
        WHERE p.person_code IS NOT NULL 
          AND p.person_code != ''
          AND p.date_to IS NULL  -- Active roles only
        GROUP BY p.person_code, p.person_name
        HAVING COUNT(DISTINCT p.company_regcode) >= 2  -- At least 2 companies
        ORDER BY company_count DESC
        LIMIT 5
    """)).fetchall()
    
    print("\n🔍 Sample persons to test with:\n")
    print(f"{'Person Code':<20} {'Name':<30} {'Companies'}")
    print("-" * 70)
    
    for row in result:
        print(f"{row.person_code:<20} {row.person_name:<30} {row.company_count}")
    
    if result:
        test_person = result[0]
        print(f"\n✅ Test with this person:")
        print(f"   Person Code: {test_person.person_code}")
        print(f"   Name: {test_person.person_name}")
        print(f"   Companies: {test_person.company_count}")
        print(f"\n📡 API Test:")
        print(f"   curl http://localhost:8001/person/{test_person.person_code}")
        print(f"\n🌐 Frontend Test:")
        print(f"   http://localhost:3000/person/{test_person.person_code}")
        
        # Also show the first 6 chars (birth date) for fragment-based URL
        fragment = test_person.person_code[:6] if len(test_person.person_code) >= 6 else test_person.person_code
        slug = test_person.person_name.lower().replace(' ', '-').replace(',', '')
        print(f"\n🔗 Alternative URL (fragment-slug):")
        print(f"   http://localhost:3000/person/{fragment}-{slug}")
    else:
        print("\n⚠️  No persons found with multiple companies")
        print("   Try querying persons with at least 1 company:")
        single = conn.execute(text("""
            SELECT person_code, person_name 
            FROM persons 
            WHERE person_code IS NOT NULL 
            LIMIT 1
        """)).fetchone()
        if single:
            print(f"   Test person: {single.person_code} - {single.person_name}")
