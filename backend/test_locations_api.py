"""
Quick test of locations API endpoints
"""
import requests

BASE_URL = "http://localhost:8000/api"

print("=== Testing Locations API ===\n")

# Test municipalities
print("1. GET /locations/municipalities (top 10)")
r = requests.get(f"{BASE_URL}/locations/municipalities", params={"limit": 10})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Found {len(data)} municipalities")
    for loc in data[:5]:
        print(f"  {loc['name']}: {loc['company_count']} companies")
print()

# Test cities  
print("2. GET /locations/cities (top 10)")
r = requests.get(f"{BASE_URL}/locations/cities", params={"limit": 10})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Found {len(data)} cities")
    for loc in data[:5]:
        print(f"  {loc['name']}: {loc['company_count']} companies")
print()

# Test specific location stats
print("3. GET /locations/city/Rīga/stats")
r = requests.get(f"{BASE_URL}/locations/city/Rīga/stats")
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"  Name: {data['name']}")
    print(f"  Companies: {data['company_count']}")
    print(f"  Employees: {data['total_employees']}")
    print(f"  Revenue: {data['total_revenue']}")
print()

print("✅ API tests complete!")
