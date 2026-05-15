"""파싱된 OpenAPI 응답을 라이브러리 사용 결과로 가공합니다."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .models import MoisResponse


def process_openapi_response(response: MoisResponse) -> list[Mapping[str, Any]]:
    """OpenAPI 페이지 응답에서 item 목록을 반환합니다."""

    return list(response.items)
