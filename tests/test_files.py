from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pymois.files import LocalDataFileClient, load_records_from_bytes, load_records_from_text

CSV_TEXT = (
    "개방자치단체코드,관리번호,인허가일자,영업상태명,사업장명,"
    "데이터갱신시점,좌표정보(X),좌표정보(Y),병상수\n"
    "3000000,PHMA1,2025-02-28,영업/정상,포레스트병원,2026-04-30 22:30:12,"
    "199642.716240024,452606.614384676,92\n"
)


def test_load_records_from_text_converts_common_python_types() -> None:
    records = load_records_from_text(CSV_TEXT, slug="hospitals")
    assert len(records) == 1
    record = records[0]
    assert record.service_slug == "hospitals"
    assert record.category == "건강"
    assert record.business_name == "포레스트병원"
    assert record.is_open is True
    assert record.license_date == date(2025, 2, 28)
    assert record.updated_at == datetime(2026, 4, 30, 22, 30, 12, tzinfo=ZoneInfo("Asia/Seoul"))
    assert record.data["SCKBD_CNT"] == 92
    assert record.coordinates is not None
    assert 126.99 < record.coordinates.lon < 127.01
    assert 37.57 < record.coordinates.lat < 37.58
    assert record.data["WGS84_LON"] == record.coordinates.lon


def test_local_data_record_detects_closed_status() -> None:
    text = (
        "관리번호,인허가일자,영업상태코드,영업상태명,사업장명\n"
        "PHMA2,2020-01-01,03,폐업,닫은병원\n"
    )
    record = load_records_from_text(text, slug="hospitals")[0]
    assert record.is_open is False


def test_load_records_from_bytes_detects_cp949() -> None:
    records = load_records_from_bytes(CSV_TEXT.encode("cp949"), slug="hospitals")
    assert records[0].business_name == "포레스트병원"


@dataclass
class FakeResponse:
    content: bytes = b""
    status_code: int = 200
    text: str = ""
    headers: dict[str, str] | None = None


class FakeSession:
    def __init__(self) -> None:
        self.urls: list[str] = []

    def get(self, url: str, **kwargs: object) -> FakeResponse:
        self.urls.append(url)
        if url.endswith("/file/download/hospitals/info"):
            return FakeResponse(content=CSV_TEXT.encode("cp949"))
        return FakeResponse()


def test_file_client_downloads_then_loads_with_browser_flow() -> None:
    session = FakeSession()
    client = LocalDataFileClient(session=session)
    records = client.load("hospitals")
    assert records[0].management_number == "PHMA1"
    assert session.urls[0].endswith("/file/hospitals/info")
    assert session.urls[1].endswith("/file/validate/download-count")
    assert session.urls[2].endswith("/file/download/hospitals/info")


def test_file_client_download_writes_path(tmp_path: Path) -> None:
    session = FakeSession()
    client = LocalDataFileClient(session=session)
    output = client.download_hospitals(tmp_path / "hospitals.csv")
    assert output.read_bytes().startswith("개방자치단체코드".encode("cp949"))
