from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pytest

from pymois import (
    LocalDataFileClient,
    LocalDataRecord,
    create_postgis_schema,
    list_file_downloads,
    record_to_place_record,
    upsert_place,
)
from pymois.db import build_place_models, place_master_values


@dataclass
class FakeResponse:
    content: bytes = b""
    status_code: int = 200
    text: str = ""
    headers: dict[str, str] | None = None


class AllLicenseFakeSession:
    def __init__(self) -> None:
        self.urls: list[str] = []

    def get(self, url: str, **kwargs: object) -> FakeResponse:
        self.urls.append(url)
        if "/file/download/" in url and url.endswith("/info"):
            slug = url.split("/file/download/", 1)[1].split("/info", 1)[0]
            return FakeResponse(content=_license_csv(slug).encode("cp949"))
        return FakeResponse()


def test_all_license_downloads_can_parse_and_prepare_db_models_without_network() -> None:
    downloads = list_file_downloads()
    session = AllLicenseFakeSession()
    client = LocalDataFileClient(session=session)

    seen_slugs: set[str] = set()
    for download in downloads:
        records = client.load(download.slug)

        assert len(records) == 1
        record = records[0]
        assert record.service_slug == download.slug
        assert record.category == download.category
        assert record.title == download.title
        assert record.management_number == f"{download.slug}-MNG-1"
        assert record.coordinates is not None
        assert record.coordinates.wgs84_point.as_tuple() == (
            record.coordinates.lon,
            record.coordinates.lat,
        )

        place = record_to_place_record(record)
        assert place.service_slug == download.slug
        assert place.mng_no == f"{download.slug}-MNG-1"
        assert place.wgs84_point is not None
        assert place.point_wkt == place.wgs84_point.to_wkt()

        master, detail = build_place_models(place)
        assert master.service_slug == download.slug
        assert master.mng_no == f"{download.slug}-MNG-1"
        assert master.geom is not None
        assert detail.record_data["MNG_NO"] == f"{download.slug}-MNG-1"
        assert place_master_values(place)["geom"] is not None
        seen_slugs.add(download.slug)

    assert len(downloads) == 195
    assert len(seen_slugs) == 195
    assert len(session.urls) == 195 * 3
    for index, download in enumerate(downloads):
        offset = index * 3
        assert session.urls[offset].endswith(download.info_path)
        assert session.urls[offset + 1].endswith("/file/validate/download-count")
        assert session.urls[offset + 2].endswith(download.download_path)


@pytest.mark.live
def test_live_all_license_downloads_and_optional_postgis_load() -> None:
    if os.getenv("MOIS_RUN_ALL_DOWNLOAD_LIVE") != "1":
        pytest.skip("MOIS_RUN_ALL_DOWNLOAD_LIVE=1일 때만 195개 실제 다운로드를 실행합니다")

    all_downloads = list_file_downloads()
    start_index = int(os.getenv("MOIS_LIVE_START_INDEX", "1"))
    end_index = int(os.getenv("MOIS_LIVE_END_INDEX", str(len(all_downloads))))
    downloads = all_downloads[start_index - 1 : end_index]
    client = LocalDataFileClient(timeout=60)
    progress_path = Path(
        os.getenv("MOIS_LIVE_PROGRESS_PATH", "artifacts/live_all_license_downloads_progress.txt")
    )
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    database_url = os.getenv("MOIS_DATABASE_URL")
    engine = None
    if database_url:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session

        engine = create_engine(database_url)
        create_postgis_schema(engine)

    failures: list[str] = []
    total_records = 0
    with progress_path.open("w", encoding="utf-8") as progress:
        progress.write(f"total={len(all_downloads)} range={start_index}-{end_index}\n")
    for index, download in enumerate(downloads, start=start_index):
        message = f"[{index}/{len(all_downloads)}] {download.slug}"
        print(message, flush=True)
        with progress_path.open("a", encoding="utf-8") as progress:
            progress.write(f"start {message}\n")
        try:
            record_count = 0
            if engine is not None:
                with Session(engine) as session:
                    for record in client.iter(download.slug):
                        record_count += 1
                        _assert_record_is_db_ready(record, download.slug)
                        upsert_place(session, record)
                        _write_record_progress(progress_path, message, record_count)
                    session.commit()
            else:
                for record in client.iter(download.slug):
                    record_count += 1
                    _assert_record_is_db_ready(record, download.slug)
                    _write_record_progress(progress_path, message, record_count)
            total_records += record_count
            with progress_path.open("a", encoding="utf-8") as progress:
                progress.write(f"ok {message} records={record_count}\n")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{download.slug}: {exc!r}")
            with progress_path.open("a", encoding="utf-8") as progress:
                progress.write(f"fail {message} error={exc!r}\n")

    assert not failures, "\n".join(failures)
    assert total_records > 0


def _assert_record_is_db_ready(record: LocalDataRecord, expected_slug: str) -> None:
    assert record.service_slug == expected_slug
    place = record_to_place_record(record)
    assert place.mng_no
    build_place_models(place)
    place_master_values(place)


def _write_record_progress(progress_path: Path, message: str, record_count: int) -> None:
    if record_count % 100000 != 0:
        return
    with progress_path.open("a", encoding="utf-8") as progress:
        progress.write(f"progress {message} records={record_count}\n")


def _license_csv(slug: str) -> str:
    return (
        "개방자치단체코드,관리번호,인허가일자,폐업일자,영업상태코드,영업상태명,"
        "사업장명,소재지전화번호,도로명전체주소,소재지전체주소,도로명우편번호,"
        "소재지우편번호,데이터갱신시점,최종수정시점,좌표정보(X),좌표정보(Y),병상수\n"
        f"3000000,{slug}-MNG-1,2025-02-28,,01,영업/정상,{slug} 테스트,"
        "02-123-4567,서울특별시 종로구 세종대로 209,서울특별시 종로구 세종로 1-91,"
        "03171,03171,2026-04-30 22:30:12,2026-04-29 11:22:33,"
        "199642.716240024,452606.614384676,1\n"
    )
