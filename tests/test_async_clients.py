from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from mois import LocalDataFileClient, MoisClient


@dataclass
class FakeResponse:
    payload: dict[str, Any] | None = None
    content: bytes = b""
    text: str = ""
    status_code: int = 200
    headers: dict[str, str] | None = None
    chunks: list[bytes] | None = None

    def json(self) -> dict[str, Any]:
        assert self.payload is not None
        return self.payload

    async def aiter_bytes(self, chunk_size: int = 1024) -> Any:
        for chunk in self.chunks or [self.content]:
            yield chunk


class FakeAsyncTransport:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.closed = False

    async def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append((url, kwargs))
        return self.response

    async def aclose(self) -> None:
        self.closed = True


class FakeAsyncFileTransport:
    def __init__(self) -> None:
        self.urls: list[str] = []
        self.kwargs: list[dict[str, object]] = []
        self.closed = False

    async def get(self, url: str, **kwargs: object) -> FakeResponse:
        self.urls.append(url)
        self.kwargs.append(kwargs)
        if url.endswith("/file/download/hospitals/info"):
            content = CSV_TEXT.encode("cp949")
            midpoint = len(content) // 2
            return FakeResponse(chunks=[content[:midpoint], content[midpoint:]])
        return FakeResponse()

    async def aclose(self) -> None:
        self.closed = True


CSV_TEXT = (
    "개방자치단체코드,관리번호,인허가일자,영업상태명,사업장명,"
    "데이터갱신시점,좌표정보(X),좌표정보(Y),병상수\n"
    "3000000,PHMA1,2025-02-28,영업/정상,포레스트병원,2026-04-30 22:30:12,"
    "199642.716240024,452606.614384676,92\n"
)


def test_async_mois_client_uses_aio_context_and_dynamic_helpers() -> None:
    payload = {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "NORMAL"},
            "body": {
                "pageNo": 1,
                "numOfRows": 100,
                "totalCount": 1,
                "items": {"item": [{"MNG_NO": "A1"}]},
            },
        }
    }
    transport = FakeAsyncTransport(
        FakeResponse(payload=payload, headers={"Content-Type": "application/json"})
    )

    async def run() -> None:
        async with MoisClient.aio("KEY", transport=transport) as client:
            response = await client.request(
                "hospitals",
                conditions={"DAT_UPDT_PNT": ("GTE", "20260301000000")},
            )
            assert response.total_count == 1
            assert await client.get_updated_hospitals("20260505") == [{"MNG_NO": "A1"}]

    asyncio.run(run())

    assert transport.closed is True
    url, kwargs = transport.calls[0]
    assert url == "http://apis.data.go.kr/1741000/hospitals/info"
    assert kwargs["params"]["serviceKey"] == "KEY"
    assert kwargs["params"]["cond[DAT_UPDT_PNT::GTE]"] == "20260301000000"
    _, updated_kwargs = transport.calls[1]
    assert updated_kwargs["params"]["cond[DAT_UPDT_PNT::GTE]"] == "20260505000000"


def test_async_file_client_downloads_then_loads_with_browser_flow() -> None:
    transport = FakeAsyncFileTransport()

    async def run() -> None:
        async with LocalDataFileClient.aio(transport=transport) as files:
            records = await files.load_hospitals()
            assert records[0].management_number == "PHMA1"

            streamed = []
            async for record in files.iter_hospitals():
                streamed.append(record)
            assert streamed[0].business_name == "포레스트병원"

    asyncio.run(run())

    assert transport.closed is True
    assert transport.urls[0].endswith("/file/hospitals/info")
    assert transport.urls[1].endswith("/file/validate/download-count")
    assert transport.urls[2].endswith("/file/download/hospitals/info")
    assert transport.kwargs[2]["stream"] is True
