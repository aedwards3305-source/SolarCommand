"""SolarCommand FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, appointments, leads, outreach
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    settings = get_settings()
    print(f"Starting {settings.app_name}...")
    yield
    print(f"Shutting down {settings.app_name}...")


app = FastAPI(
    title="SolarCommand API",
    description="Solar Lead Automation System — Lead Intelligence + AI Outreach + CRM",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow Next.js frontend in dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(leads.router)
app.include_router(outreach.router)
app.include_router(appointments.router)
app.include_router(admin.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "solarcommand"}
