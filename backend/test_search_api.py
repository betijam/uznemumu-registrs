import requests
import json

BASE_URL = "http://localhost:8000"

def test_search():
    print("Testing /analytics/people/search...")
    
    # Test 1: Basic list
    try:
        resp = requests.get(f"{BASE_URL}/analytics/people/search?limit=5")
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Success. Returned {len(data.get('items', []))} items. Total: {data.get('total')}")
            for item in data.get('items', []):
                print(f"   - {item['full_name']} ({item['net_worth']} EUR)")
        else:
            print(f"❌ Failed: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

    # Test 2: Filter by role
    print("\nTesting Filter by Role=owner...")
    try:
        resp = requests.get(f"{BASE_URL}/analytics/people/search?role=owner&limit=5")
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Success. Total owners: {data.get('total')}")
        else:
            print(f"❌ Failed: {resp.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 3: Filter by Region
    print("\nTesting Filter by Region=Rīga...")
    try:
        resp = requests.get(f"{BASE_URL}/analytics/people/search?region=Rīga&limit=5")
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Success. Total in Rīga: {data.get('total')}")
        else:
            print(f"❌ Failed: {resp.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_search()
