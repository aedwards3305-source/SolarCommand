"""Quick test: skip-trace top 20 leads via Tracerfy."""

import asyncio
import json

import httpx


async def run():
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=120) as c:
        # Login
        r = await c.post(
            "/auth/login",
            json={"email": "admin@solarcommand.local", "password": "SolarAdmin1!"},
        )
        data = r.json()
        if "access_token" not in data:
            print(f"Login failed: {data}")
            return
        token = data["access_token"]
        print(f"Logged in. Token: {token[:20]}...")

        headers = {"Authorization": f"Bearer {token}"}

        # Skip-trace top 20
        print("\nRunning skip-trace on top 20 leads...")
        r = await c.post(
            "/discovered/skip-trace",
            json={"limit": 20, "auto_activate": True},
            headers=headers,
        )
        print(f"Status: {r.status_code}")
        print(json.dumps(r.json(), indent=2))


if __name__ == "__main__":
    asyncio.run(run())
