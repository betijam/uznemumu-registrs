from app.routers.industries import get_industry_detail
from fastapi import Response

r = Response()
data = get_industry_detail('10', 2024, r)

print(f'NACE 10 sub-industries:')
print(f"Total: {len(data['sub_industries'])} sub-industries\n")
for i, sub in enumerate(data['sub_industries'], 1):
    print(f"  {i}. {sub['code']} - {sub['name'][:50]}")
    print(f"     Turnover: {sub['formatted_turnover']}, Share: {sub['share']}%, Companies: {sub.get('companies', 'N/A')}")
