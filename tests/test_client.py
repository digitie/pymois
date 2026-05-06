from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import pytest

from pymois.client import MoisClient
from pymois.exceptions import MoisAuthError, MoisRequestError
from pymois.models import Condition


@dataclass
class FakeResponse:
    payload: dict[str, Any] | None = None
    text: str = ""
    status_code: int = 200
    headers: dict[str, str] | None = None

    def json(self) -> dict[str, Any]:
        assert self.payload is not None
        return self.payload


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append((url, kwargs))
        return self.response


def test_request_builds_condition_params_and_parses_json() -> None:
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
    session = FakeSession(
        FakeResponse(payload=payload, headers={"Content-Type": "application/json"})
    )
    client = MoisClient("KEY", session=session)
    response = client.request(
        "hospitals",
        conditions={
            "DAT_UPDT_PNT": ("GTE", "20260301000000"),
            "SALS_STTS_CD": "01",
        },
    )
    assert response.total_count == 1
    assert response.items == ({"MNG_NO": "A1"},)
    url, kwargs = session.calls[0]
    assert url == "http://apis.data.go.kr/1741000/hospitals/info"
    assert kwargs["params"]["serviceKey"] == "KEY"
    assert kwargs["params"]["cond[DAT_UPDT_PNT::GTE]"] == "20260301000000"
    assert kwargs["params"]["cond[SALS_STTS_CD::EQ]"] == "01"


def test_request_accepts_condition_objects_and_history_kind() -> None:
    payload = {"response": {"header": {"resultCode": "00"}, "body": {"items": {"item": []}}}}
    session = FakeSession(
        FakeResponse(payload=payload, headers={"Content-Type": "application/json"})
    )
    client = MoisClient("KEY", session=session)
    client.request(
        "hospitals",
        kind="history",
        conditions=[Condition("BASE_DATE", "EQ", "20260101")],
    )
    url, kwargs = session.calls[0]
    assert url.endswith("/hospitals/history")
    assert kwargs["params"]["cond[BASE_DATE::EQ]"] == "20260101"


def test_dynamic_getter_uses_slug_name() -> None:
    payload = {
        "response": {
            "header": {"resultCode": "00"},
            "body": {"items": {"item": {"MNG_NO": "A1"}}},
        }
    }
    session = FakeSession(
        FakeResponse(payload=payload, headers={"Content-Type": "application/json"})
    )
    client = MoisClient("KEY", session=session)
    assert client.get_hospitals() == [{"MNG_NO": "A1"}]


def test_incremental_update_helper_uses_dat_updt_pnt_by_default() -> None:
    payload = {
        "response": {
            "header": {"resultCode": "00"},
            "body": {"items": {"item": []}},
        }
    }
    session = FakeSession(
        FakeResponse(payload=payload, headers={"Content-Type": "application/json"})
    )
    client = MoisClient("KEY", session=session)
    assert client.get_updated("hospitals", datetime(2026, 3, 1, 1, 2, 3)) == []
    _, kwargs = session.calls[0]
    assert kwargs["params"]["cond[DAT_UPDT_PNT::GTE]"] == "20260301010203"


def test_incremental_update_helper_can_use_source_modified_timestamp() -> None:
    payload = {
        "response": {
            "header": {"resultCode": "00"},
            "body": {"items": {"item": []}},
        }
    }
    session = FakeSession(
        FakeResponse(payload=payload, headers={"Content-Type": "application/json"})
    )
    client = MoisClient("KEY", session=session)
    list(client.iter_updated("hospitals", "2026-03-01", source_modified=True))
    _, kwargs = session.calls[0]
    assert kwargs["params"]["cond[LAST_MDFCN_PNT::GTE]"] == "20260301000000"


def test_history_at_helper_builds_base_date_and_org_code_conditions() -> None:
    payload = {
        "response": {
            "header": {"resultCode": "00"},
            "body": {"items": {"item": []}},
        }
    }
    session = FakeSession(
        FakeResponse(payload=payload, headers={"Content-Type": "application/json"})
    )
    client = MoisClient("KEY", session=session)
    assert client.get_history_at("hospitals", date(2026, 1, 1), org_code="3000000") == []
    url, kwargs = session.calls[0]
    assert url.endswith("/hospitals/history")
    assert kwargs["params"]["cond[BASE_DATE::EQ]"] == "20260101"
    assert kwargs["params"]["cond[OPN_ATMY_GRP_CD::EQ]"] == "3000000"


def test_xml_response_parsing() -> None:
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header><resultCode>00</resultCode><resultMsg>NORMAL</resultMsg></header>
  <body>
    <pageNo>1</pageNo><numOfRows>100</numOfRows><totalCount>1</totalCount>
    <items><item><MNG_NO>A1</MNG_NO><BPLC_NM>병원</BPLC_NM></item></items>
  </body>
</response>"""
    session = FakeSession(FakeResponse(text=xml, headers={"Content-Type": "application/xml"}))
    client = MoisClient("KEY", session=session)
    response = client.request("hospitals")
    assert response.items == ({"MNG_NO": "A1", "BPLC_NM": "병원"},)
    assert response.total_count == 1


def test_result_codes_are_mapped_to_exceptions() -> None:
    payload = {
        "response": {
            "header": {"resultCode": "30", "resultMsg": "SERVICE KEY IS NOT REGISTERED"},
            "body": {},
        }
    }
    session = FakeSession(
        FakeResponse(payload=payload, headers={"Content-Type": "application/json"})
    )
    client = MoisClient("KEY", session=session)
    with pytest.raises(MoisAuthError):
        client.request("hospitals")


def test_invalid_request_parameters_fail_before_network() -> None:
    client = MoisClient("KEY", session=FakeSession(FakeResponse()))
    with pytest.raises(ValueError):
        client.request("hospitals", num_of_rows=101)
    with pytest.raises(MoisRequestError):
        MoisClient("KEY", session=FakeSession(FakeResponse(status_code=404))).request("hospitals")
