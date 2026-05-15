from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from mois import MoisClient, save_debug_fixture


@dataclass
class FakeResponse:
    payload: dict[str, Any]
    status_code: int = 200
    headers: dict[str, str] | None = None
    text: str = ""

    def json(self) -> dict[str, Any]:
        return self.payload


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        return self.response


def test_debug_request_captures_and_masks_openapi_run(tmp_path: Path) -> None:
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
    client = MoisClient("SECRET", session=session)

    debug_run = client.debug_request("hospitals", params={"api_key": "ANOTHER_SECRET"})

    assert debug_run.error is None
    assert debug_run.processed == [{"MNG_NO": "A1"}]
    assert debug_run.request["query"]["serviceKey"] == "<REDACTED>"
    assert debug_run.request["query"]["api_key"] == "<REDACTED>"

    fixture_path = save_debug_fixture(
        debug_run,
        base_dir=tmp_path,
        case_name="Hospitals normal",
        description="정상 병원 조회",
        library_version="0.1.0",
    )
    data = json.loads(fixture_path.read_text(encoding="utf-8"))

    assert fixture_path == tmp_path / "openapi_request" / "hospitals_normal.json"
    assert data["request"]["query"]["serviceKey"] == "<REDACTED>"
    assert data["processed"] == [{"MNG_NO": "A1"}]

    with pytest.raises(FileExistsError):
        save_debug_fixture(
            debug_run,
            base_dir=tmp_path,
            case_name="Hospitals normal",
            description="정상 병원 조회",
        )
