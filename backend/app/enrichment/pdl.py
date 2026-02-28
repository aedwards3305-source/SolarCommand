"""People Data Labs (PDL) integration — contact discovery & enrichment."""

import asyncio
import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

PDL_BASE = "https://api.peopledatalabs.com/v5"


class PDLClient:
    """Client for People Data Labs person enrichment & search API."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.pdl_api_key

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    async def enrich_person(
        self,
        name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        city: str | None = None,
        state: str | None = None,
        zip_code: str | None = None,
    ) -> dict | None:
        """Enrich a person record from PDL.

        Uses Person Enrich API when we have name/email/phone.
        Falls back to Person Search API for address-only lookups (SDAT leads).
        """
        if not self.enabled:
            logger.info("PDL not configured -- skipping enrichment")
            return None

        has_identity = name or phone or email

        if has_identity:
            return await self._enrich_by_identity(name, phone, email, address)
        elif address or (city and state):
            return await self._search_by_address(address, city, state, zip_code)
        else:
            return None

    async def _enrich_by_identity(
        self,
        name: str | None,
        phone: str | None,
        email: str | None,
        address: str | None,
    ) -> dict | None:
        """Person Enrich API — requires name, email, or phone."""
        params: dict[str, str] = {}
        if name:
            params["name"] = name
        if phone:
            params["phone"] = phone
        if email:
            params["email"] = email
        if address:
            params["location"] = address

        return await self._request_with_retry("GET", f"{PDL_BASE}/person/enrich", params=params)

    async def _search_by_address(
        self,
        address: str | None,
        city: str | None,
        state: str | None,
        zip_code: str | None,
    ) -> dict | None:
        """Person Search API (GET) — find residents by street address.

        Uses GET with SQL query param (works on free tier).
        Address values are lowercased since PDL stores them lowercase.
        """
        conditions = []
        if address:
            # Extract just the street part (before any comma), lowercase for PDL
            street = address.split(",")[0].strip().lower()
            # Expand common abbreviations to match PDL's format
            for abbr, full in [(" rd", " road"), (" dr", " drive"), (" ct", " court"),
                               (" ln", " lane"), (" st", " street"), (" ave", " avenue"),
                               (" blvd", " boulevard"), (" cir", " circle"), (" pl", " place"),
                               (" ter", " terrace"), (" pkwy", " parkway")]:
                if street.endswith(abbr):
                    street = street[:-len(abbr)] + full
                    break
            conditions.append(f"location_street_address='{street}'")
        if zip_code:
            conditions.append(f"location_postal_code='{zip_code}'")
        if state:
            conditions.append(f"location_region='{state.lower()}'")
        if city:
            conditions.append(f"location_locality='{city.lower()}'")

        if not conditions:
            return None

        sql = "SELECT * FROM person WHERE " + " AND ".join(conditions)

        # Use GET with query params (works reliably on all tiers)
        return await self._request_with_retry(
            "GET", f"{PDL_BASE}/person/search",
            params={"sql": sql, "size": "1"},
            is_search=True,
        )

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        json_body: dict | None = None,
        is_search: bool = False,
    ) -> dict | None:
        """Make a PDL API request with retry on 429."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    kwargs: dict = {
                        "headers": {"X-Api-Key": self.api_key, "Content-Type": "application/json"},
                        "timeout": 15,
                    }
                    if params:
                        kwargs["params"] = params
                    if json_body:
                        kwargs["json"] = json_body

                    resp = await client.request(method, url, **kwargs)

                    if resp.status_code == 404:
                        logger.info("PDL: no match found")
                        return None

                    if resp.status_code == 402:
                        logger.warning("PDL: credit limit reached")
                        return None

                    if resp.status_code == 429:
                        retry_after = int(resp.headers.get("Retry-After", 2 ** attempt))
                        logger.warning("PDL: rate limited, retrying in %ds", retry_after)
                        await asyncio.sleep(retry_after)
                        continue

                    if resp.status_code >= 400:
                        body = resp.text
                        logger.error("PDL %d error: %s", resp.status_code, body[:500])
                        return None

                    data = resp.json()

                    if is_search:
                        # Search returns {data: [...], total: N}
                        results = data.get("data") or []
                        if not results:
                            logger.info("PDL search: no results")
                            return None
                        return _normalize_pdl(results[0])
                    else:
                        return _normalize_pdl(data)

            except httpx.HTTPError as e:
                logger.error("PDL request error (attempt %d/%d): %s", attempt + 1, max_retries, e)
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None

        return None


def _normalize_pdl(data: dict) -> dict:
    """Normalize PDL response into our standard enrichment format.

    Handles free-tier masking where some fields return True instead of values.
    """
    raw_emails = data.get("emails")
    raw_phones = data.get("phone_numbers")
    raw_mobile = data.get("mobile_phone")

    emails = []
    if isinstance(raw_emails, list):
        emails = [{"email": e.get("address"), "type": e.get("type")} for e in raw_emails]

    phones = []
    if isinstance(raw_phones, list):
        phones = [{"number": p.get("number"), "type": p.get("type")} for p in raw_phones]
    elif isinstance(raw_mobile, str):
        phones = [{"number": raw_mobile, "type": "mobile"}]

    linkedin = data.get("linkedin_url")
    if isinstance(linkedin, bool):
        linkedin = None

    return {
        "full_name": data.get("full_name"),
        "emails": emails,
        "phones": phones,
        "job_title": data.get("job_title"),
        "linkedin_url": linkedin,
        "facebook_url": data.get("facebook_url") if not isinstance(data.get("facebook_url"), bool) else None,
        # Enrich endpoint returns "likelihood"; Search endpoint does not.
        # If a search matched by address+zip, assign 0.7 confidence.
        "confidence": data.get("likelihood") or (0.7 if data.get("full_name") else 0.0),
        "raw_response": data,
    }
