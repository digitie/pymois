from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from pymois import (
    PlaceMaster,
    PlaceRecord,
    build_place_models,
    infer_domain_category,
    record_to_place_record,
)
from pymois.db import place_master_values
from pymois.files import load_records_from_text

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
    assert isinstance(place.data_updated_at, datetime)

    specific_data = place.specific_data()
    assert specific_data["SCKBD_CNT"] == 92
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


def test_build_place_models_creates_master_detail_pair() -> None:
    record = load_records_from_text(CSV_TEXT, slug="hospitals")[0]
    place = record_to_place_record(record)
    place_id = UUID("11111111-1111-1111-1111-111111111111")

    master, detail = build_place_models(place, place_id=place_id)

    assert master.place_id == place_id
    assert master.service_slug == "hospitals"
    assert master.mng_no == "PHMA1"
    assert master.geom is not None
    assert master.geom.data.startswith("POINT(")
    assert detail.place_id == place_id
    assert detail.specific_data["SCKBD_CNT"] == 92
    assert detail.record_data["ROAD_NM_ADDR"] == "서울특별시 종로구 세종대로 209"


def test_postgis_master_table_ddl_contains_geometry_and_indexes() -> None:
    ddl = str(CreateTable(PlaceMaster.__table__).compile(dialect=postgresql.dialect()))

    assert "geometry(POINT,4326)" in ddl
    assert "uq_mois_place_master_source" in ddl
    assert "service_slug" in ddl
    assert "mng_no" in ddl

    index_names = {index.name for index in PlaceMaster.__table__.indexes}
    assert "ix_mois_place_master_geom" in index_names
    assert "ix_mois_place_master_legal_dong" in index_names
    assert "ix_mois_place_master_road_name" in index_names


def test_place_master_values_requires_management_number() -> None:
    with pytest.raises(ValueError):
        place_master_values(PlaceRecord(service_slug="hospitals"))


def test_infer_domain_category_uses_travel_friendly_groups() -> None:
    assert infer_domain_category("식품", "식품_일반음식점") == "식음료"
    assert infer_domain_category("문화", "문화_관광숙박업") == "숙박/체류"
    assert infer_domain_category("건강", "건강_약국") == "안전/보건"
