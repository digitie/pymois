from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.dialects import sqlite
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateTable

from mois import (
    PlaceMaster,
    PlaceRecord,
    build_place_models,
    create_sqlite_schema,
    infer_domain_category,
    record_to_place_record,
    upsert_place,
)
from mois.db import place_master_values
from mois.files import load_records_from_text

CSV_TEXT = (
    "개방자치단체코드,관리번호,인허가일자,폐업일자,영업상태코드,영업상태명,사업장명,"
    "소재지전화번호,도로명전체주소,소재지전체주소,도로명우편번호,소재지우편번호,"
    "데이터갱신시점,최종수정시점,좌표정보(X),좌표정보(Y),병상수\n"
    "3000000,PHMA1,2025-02-28,,01,영업/정상,포레스트병원,02-123-4567,"
    "서울특별시 종로구 세종대로 209,서울특별시 종로구 세종로 1-91,03171,03171,"
    "2026-04-30 22:30:12,2026-04-29 11:22:33,199642.716240024,452606.614384676,92\n"
)


def test_place_record_extracts_db_and_linkage_fields() -> None:
    record = load_records_from_text(CSV_TEXT, slug="hospitals")[0]
    place = record_to_place_record(record)

    assert place.service_slug == "hospitals"
    assert place.mng_no == "PHMA1"
    assert place.domain_category == "안전/보건"
    assert place.opn_authority_code == "3000000"
    assert place.place_name == "포레스트병원"
    assert place.license_date == date(2025, 2, 28)
    assert place.road_address == "서울특별시 종로구 세종대로 209"
    assert place.lot_address == "서울특별시 종로구 세종로 1-91"
    assert place.road_zip == "03171"
    assert place.point_wkt is not None
    assert place.point_wkt.startswith("POINT(126.")
    assert place.katec_point is not None
    assert place.wgs84_point is not None
    assert place.station_coordinates is not None
    assert place.wgs84_point.as_tuple() == (place.lon, place.lat)
    assert isinstance(place.data_updated_at, datetime)
    assert place.detail_status_code is None
    assert place.data_update_type is None
    assert place.sickbed_count == 92

    specific_data = place.specific_data()
    assert "SCKBD_CNT" not in specific_data
    assert "ROAD_NM_ADDR" not in specific_data
    assert place.json_data()["LCPMT_YMD"] == "2025-02-28"


def test_place_record_accepts_external_address_codes_after_enrichment() -> None:
    place = PlaceRecord(
        service_slug="hospitals",
        mng_no="PHMA1",
        data={
            "MNG_NO": "PHMA1",
            "ADM_CD": "1111011900",
            "RN_MGT_SN": "111102005001",
            "BD_MGT_SN": "1111011900100010091000001",
        },
    )

    enriched = place.model_copy(
        update={
            "legal_dong_code": place.data["ADM_CD"],
            "road_name_code": place.data["RN_MGT_SN"],
            "building_management_number": place.data["BD_MGT_SN"],
        }
    )

    assert enriched.legal_dong_code == "1111011900"
    assert enriched.road_name_code == "111102005001"
    assert enriched.building_management_number == "1111011900100010091000001"


def test_record_to_place_record_generates_db_key_for_blank_management_number() -> None:
    blank_management_number_csv = CSV_TEXT.replace(",PHMA1,", ", ,", 1)
    record = load_records_from_text(blank_management_number_csv, slug="hospitals")[0]

    place = record_to_place_record(record)

    assert record.management_number is None
    assert place.mng_no is not None
    assert place.mng_no.startswith("missing-mng-no-")
    assert record_to_place_record(record).mng_no == place.mng_no
    assert place_master_values(place)["mng_no"] == place.mng_no


def test_build_place_models_creates_master_detail_pair() -> None:
    record = load_records_from_text(CSV_TEXT, slug="hospitals")[0]
    place = record_to_place_record(record)
    place_id = UUID("11111111-1111-1111-1111-111111111111")

    master, detail = build_place_models(place, place_id=place_id)

    assert master.place_id == place_id
    assert master.service_slug == "hospitals"
    assert master.mng_no == "PHMA1"
    assert master.geom_wkt is not None
    assert master.geom_wkt.startswith("POINT(")
    assert master.sickbed_count == 92
    assert detail.place_id == place_id
    assert "SCKBD_CNT" not in detail.specific_data
    assert "ROAD_NM_ADDR" not in detail.raw_data


def test_sqlite_master_table_ddl_contains_wkt_and_indexes() -> None:
    ddl = str(CreateTable(PlaceMaster.__table__).compile(dialect=sqlite.dialect()))

    assert "geom_wkt" in ddl
    assert "uq_mois_place_master_source" in ddl
    assert "service_slug" in ddl
    assert "mng_no" in ddl

    index_names = {index.name for index in PlaceMaster.__table__.indexes}
    assert "ix_mois_place_master_lon_lat" in index_names
    assert "ix_mois_place_master_legal_dong" in index_names
    assert "ix_mois_place_master_road_name" in index_names
    assert "ix_mois_place_master_detail_status" in index_names
    assert "ix_mois_place_master_subtype" in index_names


def test_sqlite_schema_upsert_and_json_filter() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    create_sqlite_schema(engine, load_spatialite=False)
    record = load_records_from_text(CSV_TEXT, slug="hospitals")[0]

    with Session(engine) as session:
        place_id = upsert_place(session, record, commit=True)
        stored = session.get(PlaceMaster, place_id)
        assert stored is not None
        assert stored.geom_wkt is not None
        assert stored.geom_wkt.startswith("POINT(")
        bed_count = session.scalar(select(PlaceMaster.sickbed_count))
        assert bed_count == 92


def test_place_master_values_requires_management_number() -> None:
    with pytest.raises(ValueError):
        place_master_values(PlaceRecord(service_slug="hospitals"))


def test_infer_domain_category_uses_travel_friendly_groups() -> None:
    assert infer_domain_category("식품", "식품_일반음식점") == "식음료"
    assert infer_domain_category("문화", "문화_관광숙박업") == "숙박/체류"
    assert infer_domain_category("건강", "건강_약국") == "안전/보건"
