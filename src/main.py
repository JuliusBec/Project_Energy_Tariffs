"""
DYNERGY - Energy Tariff Comparison Platform
Main Application Entry Point with Background Tasks

This module wraps the main FastAPI application and adds:
- Automated price forecasting on startup
- Hourly forecast scheduler
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_price_forecast():
    """Execute the price forecasting process."""
    try:
        logger.info("🔄 Running price forecast...")
        start_time = datetime.now()
        
        # Import and run forecast in a thread pool to avoid blocking
        from .backend.forecasting.energy_price_forecast import main as forecast_main
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, forecast_main)
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Price forecast completed in {duration:.1f}s")
        
    except Exception as e:
        logger.error(f"❌ Price forecast failed: {e}", exc_info=True)


async def forecast_scheduler():
    """Background task that runs forecasting every hour."""
    logger.info("📅 Forecast scheduler started (runs every hour)")
    
    while True:
        try:
            await asyncio.sleep(3600)  # Wait 1 hour
            await run_price_forecast()
        except asyncio.CancelledError:
            logger.info("Forecast scheduler cancelled")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}", exc_info=True)
            await asyncio.sleep(60)  # Wait 1 minute before retrying


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    On startup:
    - Run initial price forecast
    - Start hourly forecast scheduler
    """
    logger.info("🚀 Starting DYNERGY application...")
    
    # Run initial forecast
    await run_price_forecast()
    
    # Start background scheduler
    scheduler_task = asyncio.create_task(forecast_scheduler())
    logger.info("✅ Application startup complete")
    
    yield
    
    # Cleanup on shutdown
    logger.info("🛑 Shutting down DYNERGY application...")
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass
    logger.info("✅ Shutdown complete")


# Import the main app and add lifespan
from .backend.app import app as original_app

# Create new app with lifespan
app = FastAPI(
    title=original_app.title,
    description=original_app.description,
    lifespan=lifespan
)

# Copy all routes and middleware from original app
app.router = original_app.router
app.middleware_stack = original_app.middleware_stack


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
