"""
Enrich GeoJSON with Business Data from Database

This script merges the lv.json GeoJSON file with location statistics from the database,
adding turnover, profit, employees, and salary data to each region's properties.
"""

import json
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def normalize_name(name: str) -> str:
    """Normalize name for matching by removing suffixes and lowercasing."""
    name = name.lower().strip()
    # Remove common suffixes
    for suffix in [' novads', ' nov.', ' pilsēta', 's pilsēta', 'as pilsēta', 'es pilsēta']:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    return name

def match_names(geo_name: str, db_name: str) -> bool:
    """Check if GeoJSON name matches database name."""
    geo_norm = normalize_name(geo_name)
    db_norm = normalize_name(db_name)
    
    # Direct match
    if geo_norm == db_norm:
        return True
    
    # Check if one contains the other
    if geo_norm.startswith(db_norm) or db_norm.startswith(geo_norm):
        return True
    
    # Handle special cases like "Jelgavas" -> "Jelgava"
    if geo_norm.endswith('s') and geo_norm[:-1] == db_norm:
        return True
    if db_norm.endswith('s') and db_norm[:-1] == geo_norm:
        return True
        
    return False

def load_location_stats():
    """Load location statistics from database."""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                location_name,
                location_type,
                company_count,
                total_employees,
                total_revenue,
                total_profit,
                avg_salary
            FROM location_statistics
        """))
        
        stats = {}
        for row in result:
            stats[row.location_name] = {
                "type": row.location_type,
                "company_count": row.company_count or 0,
                "total_employees": int(row.total_employees) if row.total_employees else 0,
                "total_revenue": float(row.total_revenue) if row.total_revenue else 0,
                "total_profit": float(row.total_profit) if row.total_profit else 0,
                "avg_salary": float(row.avg_salary) if row.avg_salary else 0
            }
        
        return stats

def enrich_geojson(input_path: str, output_path: str):
    """Enrich GeoJSON with business data."""
    
    print("Loading location statistics from database...")
    stats = load_location_stats()
    print(f"Loaded {len(stats)} locations from database")
    
    print(f"\nLoading GeoJSON from {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        geojson = json.load(f)
    
    print(f"Loaded {len(geojson['features'])} features")
    
    matched = 0
    unmatched = []
    
    for feature in geojson['features']:
        geo_name = feature['properties'].get('name', '')
        
        # Find matching location in database
        match_found = False
        for db_name, data in stats.items():
            if match_names(geo_name, db_name):
                # Add business data to properties
                feature['properties']['company_count'] = data['company_count']
                feature['properties']['total_employees'] = data['total_employees']
                feature['properties']['total_revenue'] = data['total_revenue']
                feature['properties']['total_profit'] = data['total_profit']
                feature['properties']['avg_salary'] = data['avg_salary']
                feature['properties']['db_name'] = db_name
                feature['properties']['location_type'] = data['type']
                matched += 1
                match_found = True
                break
        
        if not match_found:
            unmatched.append(geo_name)
            # Set default values
            feature['properties']['company_count'] = 0
            feature['properties']['total_employees'] = 0
            feature['properties']['total_revenue'] = 0
            feature['properties']['total_profit'] = 0
            feature['properties']['avg_salary'] = 0
    
    print(f"\n✅ Matched: {matched}/{len(geojson['features'])} features")
    
    if unmatched:
        print(f"⚠️ Unmatched features: {unmatched[:10]}...")
    
    # Save enriched GeoJSON
    print(f"\nSaving enriched GeoJSON to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False)
    
    print("✅ Done!")
    
    # Print sample
    print("\nSample enriched data:")
    for feat in geojson['features'][:3]:
        props = feat['properties']
        print(f"  {props['name']}: Revenue €{props['total_revenue']:,.0f}, Employees {props['total_employees']}, Salary €{props['avg_salary']:,.0f}")

if __name__ == "__main__":
    import sys
    
    input_path = sys.argv[1] if len(sys.argv) > 1 else "../lv.json"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "../frontend/public/lv-enriched.json"
    
    enrich_geojson(input_path, output_path)
