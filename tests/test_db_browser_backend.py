from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from apps.db_browser.backend import load_sqlite  # noqa: E402
from apps.db_browser.backend.app import create_app  # noqa: E402
from mois.files import iter_records_from_bytes  # noqa: E402

CSV_TEXT = (
    "개방자치단체코드,관리번호,인허가일자,영업상태명,사업장명,"
    "데이터갱신시점,좌표정보(X),좌표정보(Y),병상수\n"
    "3000000,PHMA1,2025-02-28,영업/정상,포레스트병원,2026-04-30 22:30:12,"
    "199642.716240024,452606.614384676,92\n"
    "3000000,PHMA2,2025-03-01,영업/정상,메이플병원,2026-04-30 22:30:12,"
    "199642.716240024,452606.614384676,12\n"
)


class FakeRepository:
    def stats(self) -> dict[str, object]:
        return {
            "total": 2,
            "open": 1,
            "closedOrUnknown": 1,
            "withCoordinates": 1,
            "serviceCount": 1,
            "categories": [{"category": "건강", "count": 2}],
            "topServices": [{"serviceSlug": "hospitals", "name": "병원", "count": 2}],
        }

    def services(self) -> list[dict[str, object]]:
        return [
            {
                "serviceSlug": "hospitals",
                "category": "건강",
                "name": "병원",
                "title": "건강_병원",
                "total": 2,
                "open": 1,
                "downloadFunction": "files.iter_hospitals()",
            }
        ]

    def places(
        self,
        *,
        q: str | None,
        service_slug: str | None,
        category: str | None,
        is_open: bool | None,
        detail_status_code: str | None,
        business_type_name: str | None,
        subtype_name: str | None,
        sales_method_name: str | None,
        limit: int,
        offset: int,
    ) -> dict[str, object]:
        assert detail_status_code is None
        assert business_type_name is None
        assert subtype_name is None
        assert sales_method_name is None
        return {
            "items": [
                {
                    "placeId": "11111111-1111-1111-1111-111111111111",
                    "serviceSlug": service_slug or "hospitals",
                    "category": category or "건강",
                    "placeName": q or "포레스트병원",
                    "isOpen": is_open,
                    "lon": 126.978,
                    "lat": 37.5665,
                }
            ],
            "total": 1,
            "limit": limit,
            "offset": offset,
        }

    def place_detail(self, place_id: str) -> dict[str, object] | None:
        if place_id != "11111111-1111-1111-1111-111111111111":
            return None
        return {
            "placeId": place_id,
            "placeName": "포레스트병원",
            "detail": {
                "specificData": {"SCKBD_CNT": 92},
                "recordData": {"BPLC_NM": "포레스트병원"},
                "rawData": {"사업장명": "포레스트병원"},
            },
        }


def test_db_browser_api_with_fake_repository() -> None:
    client = TestClient(create_app(repository=FakeRepository()))

    assert client.get("/api/health").json()["databaseConfigured"] is True
    assert client.get("/api/stats").json()["total"] == 2
    service = client.get("/api/services").json()["items"][0]
    assert service["serviceSlug"] == "hospitals"
    assert service["applicationUrl"] == "https://www.data.go.kr/data/15154458/openapi.do"

    places = client.get(
        "/api/places",
        params={
            "q": "포레스트",
            "service_slug": "hospitals",
            "category": "건강",
            "is_open": "true",
        },
    ).json()
    assert places["items"][0]["placeName"] == "포레스트"
    assert places["items"][0]["isOpen"] is True

    detail = client.get("/api/places/11111111-1111-1111-1111-111111111111").json()
    assert detail["detail"]["specificData"]["SCKBD_CNT"] == 92
    assert client.get("/api/places/22222222-2222-2222-2222-222222222222").status_code == 404


def test_db_browser_api_without_database_path_returns_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MOIS_SQLITE_PATH", raising=False)
    client = TestClient(create_app(database_path=None, repository=None))

    response = client.get("/api/stats")

    assert response.status_code == 503
    assert "MOIS_SQLITE_PATH" in response.json()["detail"]


def test_load_records_to_sqlite_commits_by_batch(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeSession:
        commits = 0

        def commit(self) -> None:
            self.commits += 1

    batch_sizes: list[int] = []

    def fake_bulk_upsert(session: object, records: list[object]) -> None:
        batch_sizes.append(len(records))

    monkeypatch.setattr(load_sqlite, "_bulk_upsert_places", fake_bulk_upsert)
    session = FakeSession()
    records = iter_records_from_bytes(CSV_TEXT.encode("cp949"), slug="hospitals")

    count = load_sqlite.load_records_to_sqlite(session, records, batch_size=1)

    assert count == 2
    assert session.commits == 2
    assert batch_sizes == [1, 1]


def test_load_records_to_sqlite_rejects_invalid_batch_size() -> None:
    with pytest.raises(ValueError, match="batch_size"):
        load_sqlite.load_records_to_sqlite(object(), [], batch_size=0)  # type: ignore[arg-type]
