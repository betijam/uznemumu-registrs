from app.routers.explore import list_companies
from fastapi import Response

r = Response()
# Test sorting by turnover desc
data = list_companies(
    response=r,
    page=1, 
    limit=10, 
    sort_by="turnover", 
    order="desc"
)

print(f"Total companies: {data['meta']['total']}")
print("First 10 companies by turnover DESC:")
for i, c in enumerate(data['data'][:10], 1):
    print(f"  {i}. {c['name'][:40]:<40} | Turnover: {c['turnover']}")
