"""Tracerfy skip-tracing integration — address-to-owner contact lookup.

API docs: https://www.tracerfy.com/skip-tracing-api-documentation/
Base URL: https://tracerfy.com/v1/api/
Auth: Bearer token

Flow: POST /trace/ (submit CSV) → poll GET /queues/ (check pending) →
      GET /queue/:id (fetch records as JSON array)
"""

import asyncio
import csv
import io
import logging
from dataclasses import dataclass

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

TRACERFY_BASE = "https://tracerfy.com/v1/api"


@dataclass
class TraceRecord:
    """A single skip-trace result from Tracerfy."""

    address: str
    city: str
    state: str
    first_name: str | None = None
    last_name: str | None = None
    primary_phone: str | None = None
    primary_phone_type: str | None = None
    mobiles: list[str] | None = None
    landlines: list[str] | None = None
    emails: list[str] | None = None
    mail_address: str | None = None
    mail_city: str | None = None
    mail_state: str | None = None


class TracerfyClient:
    """Client for Tracerfy skip-tracing API.

    Flow: submit CSV of addresses -> poll queue -> parse results.
    Normal trace: 1 credit/lead ($0.02/record).
    Enhanced trace: 15 credits/lead (includes relatives, aliases, past addresses).
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.tracerfy_api_key

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "SolarCommand/1.0",
            "Accept": "application/json",
        }

    async def check_balance(self) -> dict | None:
        """Check account balance and stats via GET /analytics/."""
        if not self.enabled:
            return None
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{TRACERFY_BASE}/analytics/",
                    headers=self._headers(),
                    timeout=15,
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as e:
            logger.error("Tracerfy analytics error: %s", e)
            return None

    async def submit_trace(
        self,
        leads: list[dict],
        trace_type: str = "normal",
    ) -> int | None:
        """Submit a batch of leads for skip tracing via POST /trace/.

        Args:
            leads: List of dicts with keys: address, city, state, zip_code
            trace_type: 'normal' (1 credit) or 'enhanced' (15 credits)

        Returns:
            queue_id integer, or None on failure.
        """
        if not self.enabled:
            logger.info("Tracerfy not configured -- skipping")
            return None

        if not leads:
            return None

        # Build CSV with all required columns (empty strings for ones we don't have)
        csv_buffer = io.StringIO()
        fieldnames = [
            "address", "city", "state", "zip",
            "first_name", "last_name",
            "mail_address", "mail_city", "mail_state", "mailing_zip",
        ]
        writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
        writer.writeheader()
        for lead in leads:
            writer.writerow({
                "address": lead.get("address", ""),
                "city": lead.get("city", ""),
                "state": lead.get("state", ""),
                "zip": lead.get("zip_code", ""),
                "first_name": "",
                "last_name": "",
                "mail_address": "",
                "mail_city": "",
                "mail_state": "",
                "mailing_zip": "",
            })

        csv_bytes = csv_buffer.getvalue().encode("utf-8")

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{TRACERFY_BASE}/trace/",
                    headers=self._headers(),
                    files={"csv_file": ("leads.csv", csv_bytes, "text/csv")},
                    data={
                        "address_column": "address",
                        "city_column": "city",
                        "state_column": "state",
                        "zip_column": "zip",
                        "first_name_column": "first_name",
                        "last_name_column": "last_name",
                        "mail_address_column": "mail_address",
                        "mail_city_column": "mail_city",
                        "mail_state_column": "mail_state",
                        "mailing_zip_column": "mailing_zip",
                        "trace_type": trace_type,
                    },
                    timeout=30,
                )

                if resp.status_code >= 400:
                    logger.error(
                        "Tracerfy submit error %d: %s",
                        resp.status_code, resp.text[:500],
                    )
                    return None

                data = resp.json()
                queue_id = data.get("queue_id")
                logger.info(
                    "Tracerfy trace submitted: queue_id=%s, rows=%s, type=%s",
                    queue_id, data.get("rows_uploaded"), trace_type,
                )
                return queue_id

        except httpx.HTTPError as e:
            logger.error("Tracerfy submit error: %s", e)
            return None

    async def poll_until_complete(
        self,
        queue_id: int,
        poll_interval: int = 5,
        max_wait: int = 300,
    ) -> list[TraceRecord]:
        """Poll GET /queues/ until our queue is complete, then fetch records.

        Args:
            queue_id: The queue ID from submit_trace()
            poll_interval: Seconds between polls
            max_wait: Maximum seconds to wait before giving up

        Returns:
            List of TraceRecord results.
        """
        elapsed = 0

        while elapsed < max_wait:
            try:
                async with httpx.AsyncClient() as client:
                    # Check queue status via GET /queues/
                    resp = await client.get(
                        f"{TRACERFY_BASE}/queues/",
                        headers=self._headers(),
                        timeout=15,
                    )
                    resp.raise_for_status()
                    queues = resp.json()

                    # Find our queue
                    our_queue = None
                    for q in queues:
                        if q.get("id") == queue_id:
                            our_queue = q
                            break

                    if our_queue and not our_queue.get("pending", True):
                        # Queue complete — fetch records via GET /queue/:id
                        logger.info(
                            "Tracerfy queue %d complete (rows=%s, credits=%s)",
                            queue_id,
                            our_queue.get("rows_uploaded"),
                            our_queue.get("credits_deducted"),
                        )
                        return await self._fetch_records(queue_id)

                    if our_queue:
                        logger.debug("Tracerfy queue %d still pending (%ds elapsed)", queue_id, elapsed)
                    else:
                        logger.warning("Tracerfy queue %d not found in queues list", queue_id)

            except httpx.HTTPError as e:
                logger.error("Tracerfy poll error: %s", e)

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        logger.warning("Tracerfy queue %d timed out after %ds", queue_id, max_wait)
        return []

    async def _fetch_records(self, queue_id: int) -> list[TraceRecord]:
        """Fetch trace records via GET /queue/:id — returns JSON array directly."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{TRACERFY_BASE}/queue/{queue_id}",
                    headers=self._headers(),
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()

                # API returns a direct JSON array of record objects
                if isinstance(data, list):
                    return [_parse_record(r) for r in data]

                logger.warning("Unexpected queue response type: %s", type(data).__name__)
                return []

        except httpx.HTTPError as e:
            logger.error("Tracerfy fetch records error: %s", e)
            return []

    async def trace_and_wait(
        self,
        leads: list[dict],
        trace_type: str = "normal",
        max_wait: int = 300,
    ) -> list[TraceRecord]:
        """Submit a trace and wait for results (convenience method).

        Args:
            leads: List of dicts with keys: address, city, state, zip_code
            trace_type: 'normal' or 'enhanced'
            max_wait: Max seconds to wait for results

        Returns:
            List of TraceRecord results.
        """
        queue_id = await self.submit_trace(leads, trace_type)
        if not queue_id:
            return []

        logger.info("Waiting for Tracerfy queue %d (%d leads)...", queue_id, len(leads))
        return await self.poll_until_complete(queue_id, max_wait=max_wait)


def _parse_record(row: dict) -> TraceRecord:
    """Parse a single Tracerfy result row into a TraceRecord."""
    # Collect all mobile phones
    mobiles = []
    for i in range(1, 6):
        m = row.get(f"mobile_{i}", "")
        if m and m.strip():
            mobiles.append(m.strip())

    # Collect all landlines
    landlines = []
    for i in range(1, 4):
        ll = row.get(f"landline_{i}", "")
        if ll and ll.strip():
            landlines.append(ll.strip())

    # Collect all emails
    emails = []
    for i in range(1, 6):
        e = row.get(f"email_{i}", "")
        if e and e.strip():
            emails.append(e.strip())

    return TraceRecord(
        address=row.get("address", ""),
        city=row.get("city", ""),
        state=row.get("state", ""),
        first_name=row.get("first_name", "").strip() or None,
        last_name=row.get("last_name", "").strip() or None,
        primary_phone=row.get("primary_phone", "").strip() or None,
        primary_phone_type=row.get("primary_phone_type", "").strip() or None,
        mobiles=mobiles or None,
        landlines=landlines or None,
        emails=emails or None,
        mail_address=row.get("mail_address", "").strip() or None,
        mail_city=row.get("mail_city", "").strip() or None,
        mail_state=row.get("mail_state", "").strip() or None,
    )
