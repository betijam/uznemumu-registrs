"""
Generate city coordinates from VARIS address data or from location_statistics
Creates a JSON file with city centers for map overlay
"""

import json
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Known city coordinates (approximate centers)
# Source: OpenStreetMap / Wikipedia
CITY_COORDS = {
    # Republic cities (already in GeoJSON as polygons)
    "Rīga": [56.9496, 24.1052],
    "Liepāja": [56.5047, 21.0108],
    "Jelgava": [56.6511, 23.7211],
    "Jūrmala": [56.9681, 23.7703],
    "Rēzekne": [56.5099, 27.3345],
    "Ventspils": [57.3942, 21.5647],
    
    # Major cities in municipalities
    "Daugavpils": [55.8747, 26.5360],
    "Valmiera": [57.5384, 25.4263],
    "Ogre": [56.8166, 24.6055],
    "Cēsis": [57.3119, 25.2744],
    "Tukums": [56.9669, 23.1552],
    "Salaspils": [56.8617, 24.3492],
    "Kuldīga": [56.9678, 21.9686],
    "Saldus": [56.6636, 22.4883],
    "Talsi": [57.2453, 22.5756],
    "Sigulda": [57.1536, 24.8536],
    "Bauska": [56.4075, 24.1944],
    "Dobele": [56.6253, 23.2781],
    "Krāslava": [55.8958, 27.1689],
    "Madona": [56.8536, 26.2178],
    "Ludza": [56.5486, 27.7192],
    "Gulbene": [57.1769, 26.7511],
    "Alūksne": [57.4217, 27.0472],
    "Balvi": [57.1311, 27.2658],
    "Preiļi": [56.2942, 26.7247],
    "Limbaži": [57.5147, 24.7133],
    "Aizkraukle": [56.6006, 25.2556],
    "Jēkabpils": [56.5000, 25.8667],
    "Līvāni": [56.3542, 26.1764],
    "Smiltene": [57.4244, 25.9019],
    "Valka": [57.7750, 26.0092],
    "Vaiņode": [56.4175, 21.8519],
    "Aizpute": [56.7183, 21.6000],
    "Durbe": [56.5875, 21.3658],
    "Skrunda": [56.6761, 22.0203],
    "Pāvilosta": [56.8892, 21.1781],
    "Kandava": [57.0356, 22.7683],
    "Stende": [57.1856, 22.5378],
    "Sabile": [57.0461, 22.5711],
    "Mārupe": [56.9069, 24.0389],
    "Ķekava": [56.8269, 24.2292],
    "Olaine": [56.7853, 23.9381],
    "Ādaži": [57.0753, 24.3214],
    "Stopiņi": [56.9489, 24.2889],
    "Carnikava": [57.1292, 24.2808],
    "Ropaži": [56.9744, 24.6339],
    "Ikšķile": [56.8336, 24.5028],
    "Lielvārde": [56.7208, 24.8053],
    "Baldone": [56.7456, 24.3933],
    "Ķegums": [56.7433, 24.7250],
    "Saulkrasti": [57.2594, 24.4094],
    "Jaunjelgava": [56.6128, 25.0781],
    "Aknīste": [56.1606, 25.7489],
    "Viesīte": [56.3447, 25.5550],
    "Koknese": [56.6539, 25.4378],
    "Pļaviņas": [56.6175, 25.7197],
    "Auce": [56.4594, 22.8997],
    "Vecumnieki": [56.6083, 24.5222],  
    "Brocēni": [56.6836, 22.5783],
    "Jaunpils": [56.7311, 23.0133],
    "Engure": [57.1650, 23.2219],
    "Jaunpiebalga": [57.1850, 26.0483],
    "Ērgļi": [56.8961, 25.6419],
    "Lubāna": [56.9000, 26.7167],
    "Cesvaine": [56.9683, 26.3089],
    "Varakļāni": [56.6094, 26.7556],
    "Viļāni": [56.5500, 26.9250],
    "Kārsava": [56.7836, 27.6850],
    "Zilupe": [56.3875, 28.1211],
    "Viļaka": [57.1844, 27.6728],
    "Rugāji": [56.9953, 27.1364],
    "Dagda": [56.0947, 27.5361],
    "Cibla": [56.5492, 27.8842],
    "Riebiņi": [56.3433, 26.7983],
    "Vārkava": [56.2308, 26.4508],
    "Ilūkste": [55.9789, 26.2967],
    "Daugavpils nov.": [55.8747, 26.5360],  # Center at city
    "Naujene": [55.8556, 26.6861],
    "Kalupes": [55.8167, 26.2833],
}

def generate_city_coords():
    """Generate city coordinates from database and known coords"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Get all cities from location_statistics
        result = conn.execute(text("""
            SELECT 
                location_name,
                company_count,
                total_employees,
                total_revenue,
                total_profit,
                avg_salary
            FROM location_statistics
            WHERE location_type = 'city'
            ORDER BY company_count DESC
        """))
        
        cities = []
        unmatched = []
        
        for row in result:
            name = row.location_name
            if name in CITY_COORDS:
                cities.append({
                    "name": name,
                    "lat": CITY_COORDS[name][0],
                    "lng": CITY_COORDS[name][1],
                    "company_count": row.company_count or 0,
                    "total_employees": int(row.total_employees) if row.total_employees else 0,
                    "total_revenue": float(row.total_revenue) if row.total_revenue else 0,
                    "total_profit": float(row.total_profit) if row.total_profit else 0,
                    "avg_salary": float(row.avg_salary) if row.avg_salary else 0,
                })
            else:
                unmatched.append(name)
        
        print(f"✅ Matched {len(cities)} cities with coordinates")
        if unmatched:
            print(f"⚠️ Unmatched cities ({len(unmatched)}):")
            for name in unmatched[:20]:
                print(f"   - {name}")
        
        # Save to JSON
        output_path = "../frontend/public/cities.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cities, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Saved {len(cities)} cities to {output_path}")
        
        # Show sample
        print("\nSample data:")
        for city in cities[:5]:
            print(f"  {city['name']}: {city['company_count']} companies, €{city['avg_salary']:.0f} avg salary")

if __name__ == "__main__":
    generate_city_coords()
