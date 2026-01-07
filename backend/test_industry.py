from app.routers.industries import get_industry_detail
from fastapi import Response

r = Response()
data = get_industry_detail('10', None, r)

print('NACE 10 detail:')
print(f"Name: {data['nace_name']}")
print(f"Year: {data['year']}")
print(f"Turnover: {data['stats']['total_turnover_formatted']}")
print(f"Companies: {data['stats']['active_companies']}")
print(f"Avg Salary: {data['stats']['avg_salary']}")
