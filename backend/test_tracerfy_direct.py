"""Debug: test Tracerfy API directly with a known address."""

import asyncio
import json

from app.core.config import get_settings
from app.enrichment.tracerfy import TracerfyClient


async def run():
    settings = get_settings()
    print(f"API key set: {bool(settings.tracerfy_api_key)}")
    print(f"Key starts: {settings.tracerfy_api_key[:30]}...")

    client = TracerfyClient()
    print(f"Client enabled: {client.enabled}")

    # Check balance first
    print("\n--- Checking balance ---")
    balance = await client.check_balance()
    print(f"Balance response: {json.dumps(balance, indent=2) if balance else 'None'}")

    # Test with a sample address
    test_addresses = [
        {
            "address": "6327 EBENEZER RD",
            "city": "Baltimore",
            "state": "MD",
            "zip_code": "21220",
        },
        {
            "address": "1711 PARSONAGE RD",
            "city": "Baltimore",
            "state": "MD",
            "zip_code": "21234",
        },
    ]

    print("\n--- Submitting trace for 2 test addresses ---")
    queue_id = await client.submit_trace(test_addresses)
    print(f"Queue ID: {queue_id}")

    if queue_id:
        print("Polling for results...")
        records = await client.poll_until_complete(queue_id, poll_interval=3, max_wait=120)
        print(f"\nGot {len(records)} records back:")
        for i, rec in enumerate(records):
            print(f"\n  Record {i}:")
            print(f"    Address: {rec.address}")
            print(f"    Name: {rec.first_name} {rec.last_name}")
            print(f"    Primary phone: {rec.primary_phone} ({rec.primary_phone_type})")
            print(f"    Mobiles: {rec.mobiles}")
            print(f"    Landlines: {rec.landlines}")
            print(f"    Emails: {rec.emails}")


if __name__ == "__main__":
    asyncio.run(run())
