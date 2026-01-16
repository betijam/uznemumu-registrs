import sys
import os
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.routers.industries import get_industry_detail
from fastapi import Response

def test_industry_detail():
    print("🧪 Testing get_industry_detail for NACE '02'...")
    try:
        # Create a dummy response object
        response = Response()
        
        # Call the function
        result = get_industry_detail(nace_code="02", year=2023, response=response)
        
        if "error" in result:
            print(f"❌ API returned error: {result['error']}")
        else:
            print("✅ API returned success!")
            stats = result.get('stats', {})
            print(f"   Turnover: {stats.get('total_turnover_formatted')}")
            print(f"   Active Companies: {stats.get('active_companies')}")
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_industry_detail()
