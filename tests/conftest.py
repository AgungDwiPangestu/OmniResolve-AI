"""
tests/conftest.py — Shared Pytest Fixtures

Menyediakan fixtures yang digunakan di seluruh file test:
- event_loop: asyncio event loop untuk pytest-asyncio
- async_client: httpx.AsyncClient dengan ASGITransport ke FastAPI app
"""
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from src.api.main import app


@pytest.fixture(scope="module")
def event_loop():
    """Event loop yang di-share per module test."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_client():
    """
    Shared async HTTP client untuk test endpoints.
    Menggunakan ASGITransport agar tidak perlu server berjalan.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        timeout=120.0,  # Pipeline multi-agent butuh waktu
    ) as client:
        yield client
