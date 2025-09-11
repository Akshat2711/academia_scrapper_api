import asyncio
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from academia import SRMPortalScraper

# ✅ Windows fix for Playwright + FastAPI
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI(title="SRM Portal Scraper API")


class LoginRequest(BaseModel):
    email: str
    password: str


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/scrape")
async def scrape_portal(request: LoginRequest):
    try:
        scraper = SRMPortalScraper(request.email, request.password)
        data = await scraper.scrape_data()
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
