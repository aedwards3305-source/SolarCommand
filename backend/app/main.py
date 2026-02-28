"""SolarCommand FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, ai_routes, appointments, auth, cost_center, dashboard, discovery, insights, leads, messages, nba, outreach, portal, qa, scripts, vapi_tools, webhooks
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
    version="0.3.0",
    lifespan=lifespan,
)

# CORS — configurable via CORS_ORIGINS env var (comma-separated)
_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(leads.router)
app.include_router(outreach.router)
app.include_router(appointments.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(messages.router)
app.include_router(qa.router)
app.include_router(nba.router)
app.include_router(scripts.router)
app.include_router(insights.router)
app.include_router(webhooks.router)
app.include_router(ai_routes.router)
app.include_router(cost_center.router)
app.include_router(vapi_tools.router)
app.include_router(discovery.router)
app.include_router(portal.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "solarcommand"}
