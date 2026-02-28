"""Melissa Data integration — phone, email, and address validation."""

import asyncio
import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

MELISSA_BASE = "https://personator.melissadata.net/v3/WEB/ContactVerify/doContactVerify"


class MelissaClient:
    """Client for Melissa Global Contact Verification API."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.melissa_api_key

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    async def validate_contact(
        self,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        city: str | None = None,
        state: str | None = None,
        zip_code: str | None = None,
    ) -> dict | None:
        """Validate contact info via Melissa.

        Returns normalized validation dict or None if not configured.
        """
        if not self.enabled:
            logger.info("Melissa not configured — skipping validation")
            return None

        params: dict[str, str] = {
            "id": self.api_key,
            "act": "Check,Verify",
            "format": "json",
        }

        if phone:
            params["phone"] = phone
        if email:
            params["email"] = email
        if address:
            params["a1"] = address
        if city:
            params["city"] = city
        if state:
            params["state"] = state
        if zip_code:
            params["postal"] = zip_code

        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        MELISSA_BASE,
                        params=params,
                        timeout=15,
                    )

                    if resp.status_code == 429:
                        retry_after = int(resp.headers.get("Retry-After", 2 ** attempt))
                        logger.warning("Melissa: rate limited, retrying in %ds", retry_after)
                        await asyncio.sleep(retry_after)
                        continue

                    resp.raise_for_status()
                    data = resp.json()

                records = data.get("Records", [])
                if not records:
                    return None

                return _normalize_melissa(records[0])

            except httpx.HTTPError as e:
                logger.error("Melissa validation error (attempt %d/%d): %s", attempt + 1, max_retries, e)
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None

        return None


def _normalize_melissa(record: dict) -> dict:
    """Normalize Melissa response into our standard validation format."""
    results = record.get("Results", "")

    # Phone results
    phone_valid = "PS01" in results or "PS02" in results  # Valid phone
    phone_type = record.get("PhoneType", "unknown").lower()

    # Email results
    email_valid = "ES01" in results  # Valid email
    email_deliverable = "ES03" not in results  # Not undeliverable

    # Address results
    address_valid = "AS01" in results or "AS02" in results  # Valid address
    address_deliverable = "AS01" in results  # USPS deliverable

    return {
        "phone_valid": phone_valid if record.get("PhoneNumber") else None,
        "phone_type": phone_type if record.get("PhoneNumber") else None,
        "phone_carrier": record.get("PhoneCarrierName"),
        "phone_line_status": record.get("PhoneLineStatus", "").lower() or None,
        "email_valid": email_valid if record.get("EmailAddress") else None,
        "email_deliverable": email_deliverable if record.get("EmailAddress") else None,
        "email_disposable": "ES04" in results if record.get("EmailAddress") else None,
        "address_valid": address_valid if record.get("AddressLine1") else None,
        "address_deliverable": address_deliverable if record.get("AddressLine1") else None,
        "confidence": _compute_confidence(results),
        "raw_response": record,
    }


def _compute_confidence(results: str) -> float:
    """Compute a confidence score 0.0-1.0 from Melissa result codes."""
    score = 0.5  # baseline
    # Phone verified
    if "PS01" in results or "PS02" in results:
        score += 0.2
    # Email verified
    if "ES01" in results:
        score += 0.15
    # Address verified
    if "AS01" in results:
        score += 0.15
    return min(score, 1.0)
