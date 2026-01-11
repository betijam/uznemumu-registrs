import time
import requests
import json

API_URL = "http://localhost:8001" # Adjust if necessary, but usually standard in these tasks

def test_search(query):
    start_time = time.time()
    try:
        response = requests.get(f"{API_URL}/home/search-hint?q={query}")
        duration = time.time() - start_time
        if response.status_code == 200:
            data = response.json()
            companies = data.get("companies", [])
            print(f"Query: '{query}' | Duration: {duration:.4f}s")
            print(f"Top results:")
            for i, comp in enumerate(companies[:3]):
                print(f"  {i+1}. {comp['name']} (Reg: {comp['regcode']})")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    print("--- Verifying Search Optimization ---")
    test_search("ANIMAS")
    test_search("Cemeks")
    test_search("SIA")
