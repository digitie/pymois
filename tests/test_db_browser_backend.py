from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from apps.db_browser.backend import load_postgis  # noqa: E402
from apps.db_browser.backend.app import create_app  # noqa: E402
from pymois.files import iter_records_from_bytes  # noqa: E402

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
        limit: int,
        offset: int,
    ) -> dict[str, object]:
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
    assert client.get("/api/services").json()["items"][0]["serviceSlug"] == "hospitals"

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


def test_db_browser_api_without_database_url_returns_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MOIS_DATABASE_URL", raising=False)
    client = TestClient(create_app(database_url=None, repository=None))

    response = client.get("/api/stats")

    assert response.status_code == 503
    assert "MOIS_DATABASE_URL" in response.json()["detail"]


def test_load_records_to_postgis_commits_by_batch(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeSession:
        commits = 0

        def commit(self) -> None:
            self.commits += 1

    upserted: list[str | None] = []

    def fake_upsert(session: object, record: object) -> None:
        upserted.append(getattr(record, "management_number", None))

    monkeypatch.setattr(load_postgis, "upsert_place", fake_upsert)
    session = FakeSession()
    records = iter_records_from_bytes(CSV_TEXT.encode("cp949"), slug="hospitals")

    count = load_postgis.load_records_to_postgis(session, records, batch_size=1)

    assert count == 2
    assert session.commits == 2
    assert upserted == ["PHMA1", "PHMA2"]


def test_load_records_to_postgis_rejects_invalid_batch_size() -> None:
    with pytest.raises(ValueError, match="batch_size"):
        load_postgis.load_records_to_postgis(object(), [], batch_size=0)  # type: ignore[arg-type]
