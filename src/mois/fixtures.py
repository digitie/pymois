"""디버그 실행 결과를 pytest replay fixture로 저장합니다."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .debug import DebugRun, jsonable, redact_sensitive

DEFAULT_ASSERTION: dict[str, Any] = {
    "mode": "snapshot",
    "exclude_fields": ["fetched_at", "request_id", "updated_at"],
    "required_fields": [],
}


def save_fixture(
    *,
    base_dir: str | Path,
    function_name: str,
    case_name: str,
    description: str,
    input_data: Mapping[str, Any],
    request_data: Mapping[str, Any],
    response_data: Mapping[str, Any],
    parsed_result: Any,
    processed_result: Any,
    assertion: Mapping[str, Any] | None = None,
    library_version: str | None = None,
    overwrite: bool = False,
) -> Path:
    """디버그 실행 1건을 `tests/fixtures/{function}/{case}.json` 형식으로 저장합니다."""

    safe_function_name = slugify(function_name)
    safe_case_name = slugify(case_name)
    fixture_dir = Path(base_dir) / safe_function_name
    fixture_dir.mkdir(parents=True, exist_ok=True)
    fixture_path = fixture_dir / f"{safe_case_name}.json"

    if fixture_path.exists() and not overwrite:
        raise FileExistsError(f"Fixture already exists: {fixture_path}")

    fixture: dict[str, Any] = {
        "name": safe_case_name,
        "function": function_name,
        "description": description,
        "input": redact_sensitive(jsonable(input_data)),
        "request": redact_sensitive(jsonable(request_data)),
        "response": redact_sensitive(jsonable(response_data)),
        "parsed": jsonable(parsed_result),
        "processed": jsonable(processed_result),
        "assertion": dict(assertion or DEFAULT_ASSERTION),
        "meta": {
            "created_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
            "library_version": library_version,
            "source": "debug_ui",
        },
    }

    with fixture_path.open("w", encoding="utf-8") as output:
        json.dump(fixture, output, ensure_ascii=False, indent=2)
        output.write("\n")

    return fixture_path


def save_debug_fixture(
    debug_run: DebugRun,
    *,
    base_dir: str | Path,
    case_name: str,
    description: str,
    assertion: Mapping[str, Any] | None = None,
    library_version: str | None = None,
    overwrite: bool = False,
) -> Path:
    """`DebugRun`을 replay fixture로 저장합니다."""

    return save_fixture(
        base_dir=base_dir,
        function_name=debug_run.function,
        case_name=case_name,
        description=description,
        input_data=debug_run.input,
        request_data=debug_run.request,
        response_data=debug_run.response,
        parsed_result=debug_run.parsed,
        processed_result=debug_run.processed,
        assertion=assertion,
        library_version=library_version,
        overwrite=overwrite,
    )


def slugify(value: str) -> str:
    """fixture 경로에 사용할 안전한 이름을 만듭니다."""

    text = re.sub(r"[^\w.-]+", "_", value.strip().lower(), flags=re.UNICODE)
    text = re.sub(r"_+", "_", text).strip("._-")
    return text or "case"
