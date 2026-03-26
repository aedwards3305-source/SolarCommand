"""Remove duplicate properties/leads and add unique index on normalized address+zip.

Duplicates are identified by UPPER(address_line1) + zip_code. For each group of
duplicates, the oldest property (lowest id) is kept. Newer duplicate leads and
properties are deleted.

After cleanup, a unique index is created on (UPPER(address_line1), zip_code) to
prevent future duplicates at the database level.

Revision ID: 008_dedup_properties
Revises: 007_portal_token
Create Date: 2026-03-26
"""

from alembic import op

revision = "008_dedup_properties"
down_revision = "007_portal_token"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Build a CTE for duplicate lead IDs to delete (all child tables reference lead.id)
    dup_leads_subquery = """
        SELECT l.id FROM lead l
        INNER JOIN property p ON l.property_id = p.id
        INNER JOIN (
            SELECT UPPER(address_line1) AS norm_addr, zip_code, MIN(id) AS keep_id
            FROM property
            WHERE address_line1 IS NOT NULL AND zip_code IS NOT NULL
            GROUP BY UPPER(address_line1), zip_code
            HAVING COUNT(*) > 1
        ) dups
        ON UPPER(p.address_line1) = dups.norm_addr
        AND p.zip_code = dups.zip_code
        AND p.id != dups.keep_id
    """

    # Step 1: Delete all child rows referencing duplicate leads
    child_tables = [
        "lead_score", "outreach_attempt", "consent_log", "appointment",
        "note", "contact_intelligence", "inbound_message",
        "conversation_transcript", "qa_review", "objection_tag",
        "nba_decision", "ai_run", "contact_enrichment", "contact_validation",
    ]
    for table in child_tables:
        op.execute(f"DELETE FROM {table} WHERE lead_id IN ({dup_leads_subquery});")

    # Step 2: Delete duplicate leads
    op.execute(f"DELETE FROM lead WHERE id IN ({dup_leads_subquery});")

    # Step 3: Delete the duplicate property rows themselves
    op.execute("""
        DELETE FROM property
        WHERE id IN (
            SELECT p.id
            FROM property p
            INNER JOIN (
                SELECT UPPER(address_line1) AS norm_addr, zip_code, MIN(id) AS keep_id
                FROM property
                WHERE address_line1 IS NOT NULL AND zip_code IS NOT NULL
                GROUP BY UPPER(address_line1), zip_code
                HAVING COUNT(*) > 1
            ) dups
            ON UPPER(p.address_line1) = dups.norm_addr
            AND p.zip_code = dups.zip_code
            AND p.id != dups.keep_id
        );
    """)

    # Step 4: Normalize existing addresses to uppercase abbreviated form
    # Common suffix replacements
    for long, short in [
        ("STREET", "ST"), ("AVENUE", "AVE"), ("BOULEVARD", "BLVD"),
        ("DRIVE", "DR"), ("COURT", "CT"), ("PLACE", "PL"),
        ("LANE", "LN"), ("ROAD", "RD"), ("CIRCLE", "CIR"),
        ("TERRACE", "TER"), ("TRAIL", "TRL"), ("PARKWAY", "PKWY"),
    ]:
        op.execute(f"""
            UPDATE property
            SET address_line1 = REGEXP_REPLACE(
                UPPER(address_line1),
                '\\m{long}\\M',
                '{short}',
                'gi'
            )
            WHERE UPPER(address_line1) ~ '\\m{long}\\M';
        """)

    # Uppercase any remaining addresses for consistency
    op.execute("""
        UPDATE property
        SET address_line1 = UPPER(address_line1)
        WHERE address_line1 != UPPER(address_line1);
    """)

    # Step 5: Create unique index to prevent future duplicates
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_property_addr_zip
        ON property (UPPER(address_line1), zip_code)
        WHERE address_line1 IS NOT NULL AND zip_code IS NOT NULL;
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_property_addr_zip;")
