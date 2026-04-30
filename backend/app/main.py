import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import AsyncSessionLocal, create_tables
from app.api import health, routes, weather, emergency, reporters
from app.scrapers.imd import scrape_imd_mandi
from app.scrapers.sdma import scrape_sdma_alerts
from app.scrapers.pwd import scrape_pwd_status
from telegram import webhook as telegram_webhook
from whatsapp import webhook as whatsapp_webhook

logger = logging.getLogger(__name__)

# Tracks last successful run time for each scraper (used by /health)
scraper_status: dict[str, datetime | None] = {
    "imd": None,
    "sdma": None,
    "pwd": None,
}


async def _run_imd():
    async with AsyncSessionLocal() as db:
        result = await scrape_imd_mandi(db)
        if result:
            scraper_status["imd"] = datetime.now(timezone.utc)
            logger.info("Scheduler: IMD scrape complete")
        else:
            logger.warning("Scheduler: IMD scrape returned no data")


async def _run_sdma():
    async with AsyncSessionLocal() as db:
        count = await scrape_sdma_alerts(db)
        scraper_status["sdma"] = datetime.now(timezone.utc)
        logger.info("Scheduler: SDMA scrape complete, %d new alerts", count)


async def _run_pwd():
    async with AsyncSessionLocal() as db:
        count = await scrape_pwd_status(db)
        scraper_status["pwd"] = datetime.now(timezone.utc)
        logger.info("Scheduler: PWD scrape complete, %d new alerts", count)


async def _run_all_scrapers():
    """Run all scrapers sequentially on startup and on schedule."""
    await _run_imd()
    await _run_sdma()
    await _run_pwd()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()

    # Run scrapers immediately on startup so data is fresh from the first request
    try:
        await _run_all_scrapers()
    except Exception as exc:
        logger.error("Startup scrape failed (non-fatal): %s", exc)

    # Schedule to re-run every 6 hours
    scheduler = AsyncIOScheduler()
    scheduler.add_job(_run_imd, "interval", minutes=40, id="imd_scraper")
    scheduler.add_job(_run_sdma, "interval", minutes=40, id="sdma_scraper")
    scheduler.add_job(_run_pwd, "interval", minutes=40, id="pwd_scraper")
    scheduler.start()

    # Expose scheduler status so /health can read it
    app.state.scraper_status = scraper_status
    app.state.scheduler = scheduler

    yield

    scheduler.shutdown(wait=False)


app = FastAPI(
    title="SafarSathi API",
    description="Mountain travel safety system for Mandi region, HP",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(routes.router, tags=["Routes"])
app.include_router(weather.router, tags=["Weather"])
app.include_router(emergency.router, tags=["Emergency"])
app.include_router(reporters.router, tags=["Reporters"])
app.include_router(telegram_webhook.router, tags=["Telegram"])
app.include_router(whatsapp_webhook.router, tags=["WhatsApp"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "SafarSathi",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
