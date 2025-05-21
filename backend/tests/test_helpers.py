import asyncio
import pytest

async def run_async_test(coro):
    """Kör en asynkron testfunktion"""
    try:
        return await asyncio.wait_for(coro, timeout=5.0)
    except asyncio.TimeoutError:
        pytest.fail("Test timeout") 