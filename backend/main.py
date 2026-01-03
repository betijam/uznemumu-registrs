from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from asgi_correlation_id import CorrelationIdMiddleware
import logging
import os
from etl import run_all_etl
from app.routers import search, companies, benchmarking, industries, dashboard, explore, benchmark, regions, person

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if ETL scheduler should be enabled (default: false for API-only mode)
ENABLE_ETL_SCHEDULER = os.getenv("ENABLE_ETL_SCHEDULER", "false").lower() == "true"

# Scheduler setup
scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Company Registry Backend...")
    
    # Only start ETL scheduler if explicitly enabled
    if ENABLE_ETL_SCHEDULER:
        logger.info("⚙️  ETL Scheduler ENABLED - Starting daily ETL job at 03:00")
        scheduler.add_job(run_all_etl, 'cron', hour=3, minute=0, id='daily_etl')
        scheduler.start()
    else:
        logger.info("🚀 ETL Scheduler DISABLED - Running in API-only mode")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    if ENABLE_ETL_SCHEDULER and scheduler.running:
        scheduler.shutdown()

app = FastAPI(title="Uzņēmumu Reģistrs API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)

# Include Routers
app.include_router(search.router)
app.include_router(explore.router)  # Check explore before companies (to avoid /companies/list collision)
app.include_router(companies.router)
app.include_router(person.router)  # Person profiles
app.include_router(benchmark.router)
app.include_router(benchmarking.router)
app.include_router(industries.router)
app.include_router(dashboard.router)
app.include_router(regions.router)

@app.get("/health")
def health_check():
    """Health check endpoint showing service status"""
    return {
        "status": "ok",
        "mode": "etl-enabled" if ENABLE_ETL_SCHEDULER else "api-only",
        "scheduler": "running" if (ENABLE_ETL_SCHEDULER and scheduler.running) else "disabled"
    }

@app.get("/")
def read_root():
    return {"message": "Welcome to Company Registry API"}
