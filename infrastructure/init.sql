-- Bootstrap SQL: runs on first Postgres startup.
-- The actual schema is managed by Alembic migrations.
-- This file exists only for manual setup or seeding.

-- Seed a default admin user
INSERT INTO rep_user (email, name, role, is_active)
VALUES ('admin@solarcommand.local', 'System Admin', 'admin', true)
ON CONFLICT (email) DO NOTHING;

-- Seed a default rep user
INSERT INTO rep_user (email, name, role, is_active)
VALUES ('rep@solarcommand.local', 'Demo Rep', 'rep', true)
ON CONFLICT (email) DO NOTHING;

-- Seed initial voice call script
INSERT INTO script_version (version_label, channel, content, is_active, created_by)
VALUES (
    'v1.0',
    'voice',
    'Hi, this is Sarah calling from {{company}} Solar. We help homeowners in {{county}} save on electricity with solar panels. Is now a good time for a quick 2-minute chat?',
    true,
    'system'
);
