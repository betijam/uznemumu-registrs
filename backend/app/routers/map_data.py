"""
Map Data API - Serves GeoJSON and cities data for the regions map
"""
from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
import os
import json

router = APIRouter(prefix="/map", tags=["map"])

# Get the path to the frontend public folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_PUBLIC = os.path.join(BASE_DIR, "..", "frontend", "public")


@router.get("/geojson")
async def get_geojson():
    """Return the Latvia regions GeoJSON data"""
    filepath = os.path.join(FRONTEND_PUBLIC, "lv-enriched.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    return JSONResponse(content={"error": "GeoJSON file not found"}, status_code=404)


@router.get("/cities")
async def get_cities():
    """Return cities data for the map overlay"""
    filepath = os.path.join(FRONTEND_PUBLIC, "cities.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    return JSONResponse(content={"error": "Cities file not found"}, status_code=404)
