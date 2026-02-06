# SolarCommand

Solar Lead Automation System — Lead Intelligence + AI Outreach + Solar CRM.

Built for a Maryland-based solar company to replace/augment door-to-door canvassing with automated prospect identification, AI-powered multi-channel outreach (voice, SMS, email), and a solar-specific CRM.

## Quick Start (Local Development)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)
- Git

### 1. Clone and configure

```bash
git clone <repo-url> SolarCommand
cd SolarCommand
cp .env.example .env
```

### 2. Start all services

```bash
docker compose up --build
```

This starts:
- **PostgreSQL 16** on port 5432
- **Redis 7** on port 6379
- **FastAPI backend** on port 8000 (with auto-reload)
- **Celery worker** (background job processor)

Alembic migrations run automatically on startup.

### 3. Verify

```bash
curl http://localhost:8000/health
# → {"status":"healthy","service":"solarcommand"}
```

API docs: http://localhost:8000/docs

### 4. Try the API

**Ingest a property:**
```bash
curl -X POST http://localhost:8000/leads/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "address_line1": "123 Oak Street",
    "city": "Annapolis",
    "state": "MD",
    "zip_code": "21401",
    "county": "Anne Arundel",
    "parcel_id": "AA-001",
    "property_type": "SFH",
    "year_built": 2010,
    "roof_area_sqft": 1800,
    "assessed_value": 425000,
    "utility_zone": "BGE",
    "tree_cover_pct": 15,
    "neighborhood_solar_pct": 8,
    "has_existing_solar": false,
    "owner_first_name": "John",
    "owner_last_name": "Smith",
    "owner_occupied": true,
    "owner_phone": "+14105551234",
    "owner_email": "john@example.com",
    "median_household_income": 95000,
    "data_source": "manual"
  }'
```

**Score the lead:**
```bash
curl -X POST http://localhost:8000/leads/1/score
```

**Enqueue outreach:**
```bash
curl -X POST http://localhost:8000/outreach/1/enqueue
```

**List leads:**
```bash
curl http://localhost:8000/leads
```

## Project Structure

```
SolarCommand/
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── docs/
│   ├── SYSTEM_DESIGN.md      ← Full system design (Deliverables A-K)
│   └── schema.sql             ← Raw SQL schema
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── migrations/
│   ├── app/
│   │   ├── main.py            ← FastAPI app entry
│   │   ├── core/              ← Config, DB, auth
│   │   ├── models/            ← SQLAlchemy ORM models
│   │   ├── api/               ← Route handlers
│   │   ├── services/          ← Business logic
│   │   └── workers/           ← Celery background tasks
│   └── tests/
├── frontend/                   ← Next.js (future)
└── infrastructure/
    ├── render.yaml            ← Render deploy blueprint
    └── init.sql               ← DB seed data
```

## Running Tests

```bash
# Unit tests (no DB required)
cd backend
pip install -e ".[dev]"
pytest tests/test_scoring.py tests/test_outreach.py -v

# Integration tests (requires docker compose up)
pytest tests/ -v
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.12) |
| Database | PostgreSQL 16 |
| Queue | Redis 7 + Celery |
| Frontend | Next.js 14 (planned) |
| Voice/SMS | Twilio (planned) |
| Email | SendGrid (planned) |
| AI Agent | OpenAI GPT-4o-mini (planned) |
| Hosting | Render (blueprint included) |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/leads/ingest` | Ingest a property + create lead |
| POST | `/leads/{id}/score` | Compute Solar Readiness Score |
| GET | `/leads` | List leads (filterable) |
| POST | `/outreach/{id}/enqueue` | Queue next outreach action |
| GET | `/outreach/{id}/attempts` | List outreach attempts |
| POST | `/appointments` | Book an appointment |
| GET | `/appointments` | List appointments |
| GET | `/admin/audit-log` | Browse audit log |
| GET | `/admin/scripts` | List script versions |

## Documentation

See [docs/SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md) for:
- Executive Summary
- System Architecture
- Database Schema
- Lead Scoring Algorithm
- AI Call Center Design
- Outreach Orchestration
- Frontend/CRM UX Wireframes
- Implementation Roadmap
- Compliance Checklist
