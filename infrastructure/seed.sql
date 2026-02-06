-- Seed data: run AFTER Alembic migrations create the tables.

-- Default admin user
INSERT INTO rep_user (email, name, role, is_active)
VALUES ('admin@solarcommand.local', 'System Admin', 'admin', true)
ON CONFLICT (email) DO NOTHING;

-- Default rep user
INSERT INTO rep_user (email, name, role, is_active)
VALUES ('rep@solarcommand.local', 'Demo Rep', 'rep', true)
ON CONFLICT (email) DO NOTHING;

-- Initial voice call script
INSERT INTO script_version (version_label, channel, content, is_active, created_by)
SELECT 'v1.0', 'voice',
    'Hi, this is Sarah calling from {{company}} Solar. We help homeowners in {{county}} save on electricity with solar panels. Is now a good time for a quick 2-minute chat?',
    true, 'system'
WHERE NOT EXISTS (SELECT 1 FROM script_version WHERE version_label = 'v1.0' AND channel = 'voice');
