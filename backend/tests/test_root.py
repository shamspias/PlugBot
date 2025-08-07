import pytest, httpx, os, asyncio


@pytest.mark.asyncio
async def test_healthcheck():
    async with httpx.AsyncClient(base_url="http://backend:8000") as client:
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "healthy"}
