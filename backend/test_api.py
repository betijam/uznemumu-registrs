import requests
import json

print("=== Testing Locations API ===\n")

# Test cities
print("1. Testing /api/locations/cities...")
try:
    r = requests.get("http://localhost:8000/api/locations/cities?limit=3")
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   Count: {len(data)}")
        if data:
            print(f"   Sample: {data[0]}")
            print(f"   Has avg_salary: {'avg_salary' in data[0]}")
    else:
        print(f"   Error: {r.text}")
except Exception as e:
    print(f"   Exception: {e}")

print()

# Test municipalities
print("2. Testing /api/locations/municipalities...")
try:
    r = requests.get("http://localhost:8000/api/locations/municipalities?limit=3")
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   Count: {len(data)}")
        if data:
            print(f"   Sample: {data[0]}")
            print(f"   Has avg_salary: {'avg_salary' in data[0]}")
    else:
        print(f"   Error: {r.text}")
except Exception as e:
    print(f"   Exception: {e}")
