from __future__ import annotations

from datetime import date, datetime

from pymois.convert import KST, convert_value, field_for_header, to_date, to_datetime, to_number


def test_field_for_header_uses_response_mapping_and_aliases() -> None:
    assert field_for_header("관리번호") == "MNG_NO"
    assert field_for_header("도로명전체주소") == "ROAD_NM_ADDR"
    assert field_for_header("좌표정보(X)") == "CRD_INFO_X"
    assert field_for_header("전화번호") == "TELNO"


def test_date_and_datetime_conversion() -> None:
    assert to_date("20260131") == date(2026, 1, 31)
    assert to_date("2026-01-31") == date(2026, 1, 31)
    assert to_datetime("20260301010203") == datetime(2026, 3, 1, 1, 2, 3, tzinfo=KST)
    assert to_datetime("2026-03-01 01:02:03") == datetime(2026, 3, 1, 1, 2, 3, tzinfo=KST)


def test_number_conversion_preserves_int_when_possible() -> None:
    assert to_number("1,234") == 1234
    assert to_number("12.50") == 12.5
    assert to_number("abc") is None


def test_convert_value_uses_field_semantics() -> None:
    assert convert_value("LCPMT_YMD", "인허가일자", "2026-01-02") == date(2026, 1, 2)
    assert convert_value("DAT_UPDT_PNT", "데이터갱신시점", "20260102030405") == datetime(
        2026, 1, 2, 3, 4, 5, tzinfo=KST
    )
    assert convert_value("SCKBD_CNT", "병상수", "42") == 42
    assert convert_value("BPLC_NM", "사업장명", " 테스트 ") == "테스트"
