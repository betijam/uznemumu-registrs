from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from asgi_correlation_id import CorrelationIdMiddleware
import logging
from etl import run_all_etl
from app.routers import search, companies

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Scheduler setup
scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Company Registry Backend...")
    # Run ETL daily at 03:00
    scheduler.add_job(run_all_etl, 'cron', hour=3, minute=0, id='daily_etl')
    scheduler.start()
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    scheduler.shutdown()

app = FastAPI(title="Uzņēmumu Reģistrs API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)

# Include Routers
app.include_router(search.router)
app.include_router(companies.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "scheduler": "running" if scheduler.running else "stopped"}

@app.get("/")
def read_root():
    return {"message": "Welcome to Company Registry API"}

@app.post("/etl/run")
def run_etl_manually():
    """Manually trigger the ETL process immediately."""
    job = scheduler.add_job(run_all_etl, 'date')
    return {"message": "ETL job triggered", "job_id": job.id}
