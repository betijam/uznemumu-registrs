from app.routers.industries import get_industry_detail
from fastapi import Response

# Test with 4-digit code (1051 = Piena produktu ražošana)
r = Response()
data = get_industry_detail('1051', 2024, r)

print('NACE 1051 detail:')
print(f"Name: {data['nace_name']}")
print(f"Year: {data['year']}")
print(f"Turnover: {data['stats']['total_turnover_formatted']}")
print(f"Companies: {data['stats']['active_companies']}")
print(f"Avg Salary: {data['stats']['avg_salary']}")
print(f"Leaders count: {len(data['leaders'])}")
print(f"Sub-industries count: {len(data['sub_industries'])}")

if data['leaders']:
    print("\nTop 3 leaders:")
    for i, l in enumerate(data['leaders'][:3], 1):
        print(f"  {i}. {l['name'][:40]} - {l['turnover_formatted']}")
