"""디버그 UI와 fixture 저장에 재사용할 실행 결과 구조."""

from __future__ import annotations

import traceback
from collections.abc import Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel

SENSITIVE_KEYS = frozenset(
    {
        "authorization",
        "x-api-key",
        "api_key",
        "apikey",
        "servicekey",
        "service_key",
        "access_token",
        "refresh_token",
    }
)


@dataclass(frozen=True, slots=True)
class DebugRun:
    """라이브러리 함수 1회 실행의 입력, 요청, 응답, 파싱/가공 결과입니다."""

    function: str
    input: Mapping[str, Any]
    request: Mapping[str, Any]
    response: Mapping[str, Any]
    parsed: Any
    processed: Any
    trace: tuple[str, ...]
    error: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """JSON 저장과 UI 표시가 쉬운 dict로 변환합니다."""

        return {
            "function": self.function,
            "input": jsonable(self.input),
            "request": jsonable(self.request),
            "response": jsonable(self.response),
            "parsed": jsonable(self.parsed),
            "processed": jsonable(self.processed),
            "trace": list(self.trace),
            "error": jsonable(self.error),
        }


def jsonable(obj: Any) -> Any:
    """Pydantic 모델, dataclass, 날짜 값을 JSON 호환 값으로 바꿉니다."""

    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if is_dataclass(obj) and not isinstance(obj, type):
        return jsonable(asdict(obj))
    if isinstance(obj, Mapping):
        return {str(key): jsonable(value) for key, value in obj.items()}
    if isinstance(obj, list | tuple):
        return [jsonable(value) for value in obj]
    if isinstance(obj, date | datetime):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, Path):
        return str(obj)
    return obj


def redact_sensitive(obj: Any) -> Any:
    """fixture와 UI 표시용 payload에서 인증 정보를 제거합니다."""

    if isinstance(obj, Mapping):
        result: dict[str, Any] = {}
        for key, value in obj.items():
            key_text = str(key)
            if key_text.lower() in SENSITIVE_KEYS:
                result[key_text] = "<REDACTED>"
            else:
                result[key_text] = redact_sensitive(value)
        return result
    if isinstance(obj, list | tuple):
        return [redact_sensitive(value) for value in obj]
    return obj


def error_to_dict(exc: BaseException) -> dict[str, Any]:
    """예외를 디버그 UI에서 표시할 수 있는 구조로 변환합니다."""

    return {
        "type": exc.__class__.__name__,
        "module": exc.__class__.__module__,
        "message": str(exc),
        "traceback": traceback.format_exception(exc),
    }
