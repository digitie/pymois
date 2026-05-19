from __future__ import annotations

import asyncio
import os
from collections.abc import Mapping
from typing import Any

import pytest

from mois import MoisClient


@pytest.mark.live
def test_live_hospitals_first_page_sync_and_async() -> None:
    key = os.getenv("MOIS_SERVICE_KEY")
    if not key:
        pytest.skip("MOIS_SERVICE_KEY가 없습니다")

    with MoisClient(key, timeout=30.0, max_rps=2.0) as client:
        sync_rows = client.get_hospitals(num_of_rows=1)
    assert isinstance(sync_rows, list)
    if sync_rows:
        assert isinstance(sync_rows[0], Mapping)

    async def run() -> list[Mapping[str, Any]]:
        async with MoisClient.aio(key, timeout=30.0, max_rps=2.0) as client:
            return await client.get_hospitals(num_of_rows=1)

    async_rows = asyncio.run(run())
    assert isinstance(async_rows, list)
    if async_rows:
        assert isinstance(async_rows[0], Mapping)
