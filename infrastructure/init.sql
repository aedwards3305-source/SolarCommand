-- Bootstrap SQL: runs on first Postgres startup.
-- Schema is managed by Alembic migrations (runs in api container).
-- This file only sets up extensions; seed data runs after migrations.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
