"""
Map Data API - Serves GeoJSON and cities data for the regions map
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os
import json

router = APIRouter(prefix="/map", tags=["map"])

# Get the path to the static folder in backend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATIC_DIR = os.path.join(BASE_DIR, "static")


@router.get("/geojson")
async def get_geojson():
    """Return the Latvia regions GeoJSON data"""
    filepath = os.path.join(STATIC_DIR, "lv-enriched.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    return JSONResponse(content={"error": f"GeoJSON file not found at {filepath}"}, status_code=404)


@router.get("/cities")
async def get_cities():
    """Return cities data for the map overlay"""
    filepath = os.path.join(STATIC_DIR, "cities.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    return JSONResponse(content={"error": f"Cities file not found at {filepath}"}, status_code=404)


@router.get("/logo")
async def get_logo():
    """Return the ANIMAS logo"""
    filepath = os.path.join(STATIC_DIR, "animas-logo.jpg")
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="image/jpeg")
    return JSONResponse(content={"error": "Logo not found"}, status_code=404)
