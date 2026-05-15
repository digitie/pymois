"""data.go.kr 지방행정 인허가정보 OpenAPI 클라이언트."""

from __future__ import annotations

import os
from collections.abc import Iterable, Iterator, Mapping
from datetime import date, datetime
from typing import Any

from requests import RequestException

from ._http import build_session, raise_for_http_error
from .catalogs import get_openapi_service
from .debug import DebugRun, error_to_dict, jsonable, redact_sensitive
from .exceptions import MoisRequestError
from .models import Condition, ConditionOperator, MoisResponse, OpenApiKind
from .parser import parse_openapi_response
from .processor import process_openapi_response


class MoisClient:
    """공공데이터포털 195개 인허가정보 OpenAPI 공통 클라이언트."""

    def __init__(
        self,
        service_key: str,
        *,
        timeout: float = 10.0,
        retries: int = 2,
        session: Any | None = None,
        base_url: str | None = None,
    ) -> None:
        if not service_key:
            raise ValueError("service_key is required")
        self.service_key = service_key
        self.timeout = timeout
        self.session = session or build_session(retries)
        self.base_url = base_url.rstrip("/") if base_url else None

    @classmethod
    def from_env(cls, name: str = "MOIS_SERVICE_KEY", **kwargs: Any) -> MoisClient:
        """환경변수에서 서비스키를 읽어 클라이언트를 만듭니다."""

        try:
            service_key = os.environ[name]
        except KeyError as exc:
            raise ValueError(f"{name} is not set") from exc
        return cls(service_key, **kwargs)

    def request(
        self,
        slug: str,
        *,
        kind: str | OpenApiKind = OpenApiKind.INFO,
        page_no: int = 1,
        num_of_rows: int = 100,
        conditions: Mapping[str, Any] | Iterable[Condition] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> MoisResponse:
        """업종 slug와 구분(info/history)으로 한 페이지를 호출합니다."""

        url, request_params, kind_value = self._build_openapi_request(
            slug,
            kind=kind,
            page_no=page_no,
            num_of_rows=num_of_rows,
            conditions=conditions,
            params=params,
        )
        response = self._send_openapi_request(url, request_params, context=f"{slug}/{kind_value}")
        return parse_openapi_response(response, page_no=page_no, num_of_rows=num_of_rows)

    def debug_request(
        self,
        slug: str,
        *,
        kind: str | OpenApiKind = OpenApiKind.INFO,
        page_no: int = 1,
        num_of_rows: int = 100,
        conditions: Mapping[str, Any] | Iterable[Condition] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> DebugRun:
        """OpenAPI 1회 실행의 요청/응답/파싱/가공 결과를 디버그 구조로 반환합니다."""

        trace: list[str] = []
        request_data: dict[str, Any] = {}
        response_data: dict[str, Any] = {}
        parsed: MoisResponse | None = None
        processed: list[Mapping[str, Any]] | None = None
        error: dict[str, Any] | None = None
        input_data: dict[str, Any] = {
            "slug": slug,
            "kind": str(kind),
            "page_no": page_no,
            "num_of_rows": num_of_rows,
            "params": dict(params or {}),
        }

        try:
            url, request_params, kind_value = self._build_openapi_request(
                slug,
                kind=kind,
                page_no=page_no,
                num_of_rows=num_of_rows,
                conditions=conditions,
                params=params,
            )
            input_data["conditions"] = {
                key: value for key, value in request_params.items() if key.startswith("cond[")
            }
            request_data = {
                "method": "GET",
                "url": url,
                "query": request_params,
                "headers": {"Accept": "*/*"},
            }
            trace.append("OpenAPI 요청을 구성했습니다.")

            response = self._send_openapi_request(
                url,
                request_params,
                context=f"{slug}/{kind_value}",
            )
            response_data = _response_debug_data(response)
            trace.append("OpenAPI 응답을 받았습니다.")

            parsed = parse_openapi_response(response, page_no=page_no, num_of_rows=num_of_rows)
            trace.append("원본 응답을 MoisResponse로 파싱했습니다.")

            processed = process_openapi_response(parsed)
            trace.append("파싱 결과를 라이브러리 반환 형태로 가공했습니다.")
        except Exception as exc:
            error = error_to_dict(exc)
            trace.append("실행 중 예외를 캡처했습니다.")

        return DebugRun(
            function="openapi_request",
            input=redact_sensitive(jsonable(input_data)),
            request=redact_sensitive(jsonable(request_data)),
            response=redact_sensitive(jsonable(response_data)),
            parsed=parsed,
            processed=processed,
            trace=tuple(trace),
            error=error,
        )

    def get(
        self,
        slug: str,
        *,
        kind: str | OpenApiKind = OpenApiKind.INFO,
        page_no: int = 1,
        num_of_rows: int = 100,
        conditions: Mapping[str, Any] | Iterable[Condition] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> list[Mapping[str, Any]]:
        """한 페이지의 item 목록만 반환합니다."""

        return process_openapi_response(
            self.request(
                slug,
                kind=kind,
                page_no=page_no,
                num_of_rows=num_of_rows,
                conditions=conditions,
                params=params,
            )
        )

    def iter_records(
        self,
        slug: str,
        *,
        kind: str | OpenApiKind = OpenApiKind.INFO,
        num_of_rows: int = 100,
        conditions: Mapping[str, Any] | Iterable[Condition] | None = None,
        params: Mapping[str, Any] | None = None,
        max_pages: int | None = None,
    ) -> Iterator[Mapping[str, Any]]:
        """페이지를 넘기며 모든 item을 순회합니다."""

        page_no = 1
        seen = 0
        while True:
            response = self.request(
                slug,
                kind=kind,
                page_no=page_no,
                num_of_rows=num_of_rows,
                conditions=conditions,
                params=params,
            )
            if not response.items:
                return
            for item in response.items:
                seen += 1
                yield item
            if response.total_count is not None and seen >= response.total_count:
                return
            page_no += 1
            if max_pages is not None and page_no > max_pages:
                return

    def iter_updated(
        self,
        slug: str,
        since: date | datetime | str,
        *,
        source_modified: bool = False,
        num_of_rows: int = 100,
        params: Mapping[str, Any] | None = None,
        max_pages: int | None = None,
    ) -> Iterator[Mapping[str, Any]]:
        """증분 변경분을 순회합니다.

        기본값은 개방데이터 갱신시점(`DAT_UPDT_PNT`) 기준입니다. 원천데이터의
        최종수정시점만 기준으로 삼으려면 `source_modified=True`를 사용합니다.
        """

        field = "LAST_MDFCN_PNT" if source_modified else "DAT_UPDT_PNT"
        return self.iter_records(
            slug,
            num_of_rows=num_of_rows,
            conditions=[Condition(field, ConditionOperator.GTE, _timestamp_param(since))],
            params=params,
            max_pages=max_pages,
        )

    def get_updated(
        self,
        slug: str,
        since: date | datetime | str,
        *,
        source_modified: bool = False,
        num_of_rows: int = 100,
        params: Mapping[str, Any] | None = None,
        max_pages: int | None = None,
    ) -> list[Mapping[str, Any]]:
        """증분 변경분을 목록으로 반환합니다."""

        return list(
            self.iter_updated(
                slug,
                since,
                source_modified=source_modified,
                num_of_rows=num_of_rows,
                params=params,
                max_pages=max_pages,
            )
        )

    def iter_history_at(
        self,
        slug: str,
        base_date: date | str,
        *,
        org_code: str | None = None,
        num_of_rows: int = 100,
        params: Mapping[str, Any] | None = None,
        max_pages: int | None = None,
    ) -> Iterator[Mapping[str, Any]]:
        """특정 기준일자의 이력 데이터를 순회합니다."""

        conditions: list[Condition] = [
            Condition("BASE_DATE", ConditionOperator.EQ, _date_param(base_date))
        ]
        if org_code:
            conditions.append(Condition("OPN_ATMY_GRP_CD", ConditionOperator.EQ, org_code))
        return self.iter_records(
            slug,
            kind="history",
            num_of_rows=num_of_rows,
            conditions=conditions,
            params=params,
            max_pages=max_pages,
        )

    def get_history_at(
        self,
        slug: str,
        base_date: date | str,
        *,
        org_code: str | None = None,
        num_of_rows: int = 100,
        params: Mapping[str, Any] | None = None,
        max_pages: int | None = None,
    ) -> list[Mapping[str, Any]]:
        """특정 기준일자의 이력 데이터를 목록으로 반환합니다."""

        return list(
            self.iter_history_at(
                slug,
                base_date,
                org_code=org_code,
                num_of_rows=num_of_rows,
                params=params,
                max_pages=max_pages,
            )
        )

    def __getattr__(self, name: str) -> Any:
        """`get_hospitals()`나 `get_updated_hospitals()` 같은 편의 메서드를 제공합니다."""

        if name.startswith("get_updated_"):
            slug = name[len("get_updated_") :]

            def updated_getter(
                since: date | datetime | str,
                **kwargs: Any,
            ) -> list[Mapping[str, Any]]:
                return self.get_updated(slug, since, **kwargs)

            return updated_getter
        if name.startswith("iter_updated_"):
            slug = name[len("iter_updated_") :]

            def updated_iterator(
                since: date | datetime | str,
                **kwargs: Any,
            ) -> Iterator[Mapping[str, Any]]:
                return self.iter_updated(slug, since, **kwargs)

            return updated_iterator

        if name.startswith("get_"):
            slug, kind = _dynamic_name_to_slug(name[4:])

            def getter(**kwargs: Any) -> list[Mapping[str, Any]]:
                return self.get(slug, kind=kind, **kwargs)

            return getter
        if name.startswith("iter_"):
            slug, kind = _dynamic_name_to_slug(name[5:])

            def iterator(**kwargs: Any) -> Iterator[Mapping[str, Any]]:
                return self.iter_records(slug, kind=kind, **kwargs)

            return iterator
        raise AttributeError(name)

    def _endpoint_url(self, slug: str, kind: str) -> str:
        service = get_openapi_service(slug)
        if self.base_url:
            return f"{self.base_url}/{slug}/{kind}"
        return service.info_url if kind == "info" else service.history_url

    def _build_openapi_request(
        self,
        slug: str,
        *,
        kind: str | OpenApiKind,
        page_no: int,
        num_of_rows: int,
        conditions: Mapping[str, Any] | Iterable[Condition] | None,
        params: Mapping[str, Any] | None,
    ) -> tuple[str, dict[str, Any], str]:
        kind_value = str(kind)
        if kind_value not in {OpenApiKind.INFO.value, OpenApiKind.HISTORY.value}:
            raise ValueError('kind must be "info" or "history"')
        if page_no < 1:
            raise ValueError("page_no must be >= 1")
        if not 1 <= num_of_rows <= 100:
            raise ValueError("num_of_rows must be between 1 and 100")

        url = self._endpoint_url(slug, kind_value)
        request_params: dict[str, Any] = {
            "serviceKey": self.service_key,
            "pageNo": page_no,
            "numOfRows": num_of_rows,
        }
        request_params.update(_condition_params(conditions))
        if params:
            request_params.update(params)
        return url, request_params, kind_value

    def _send_openapi_request(
        self,
        url: str,
        request_params: Mapping[str, Any],
        *,
        context: str,
    ) -> Any:
        try:
            response = self.session.get(url, params=dict(request_params), timeout=self.timeout)
            raise_for_http_error(response, context)
        except RequestException as exc:
            raise MoisRequestError(f"{context}: request failed") from exc
        return response


def _response_debug_data(response: Any) -> dict[str, Any]:
    headers = dict(getattr(response, "headers", {}) or {})
    return {
        "status_code": getattr(response, "status_code", None),
        "headers": headers,
        "body": _response_debug_body(response, headers),
    }


def _response_debug_body(response: Any, headers: Mapping[str, Any]) -> Any:
    content_type = str(
        headers.get("Content-Type") or headers.get("content-type") or ""
    ).lower()
    text = getattr(response, "text", "")
    if "json" in content_type or str(text).lstrip().startswith("{"):
        try:
            return response.json()
        except (AttributeError, ValueError):
            return text
    return text


def _dynamic_name_to_slug(name: str) -> tuple[str, str]:
    if name.endswith("_history"):
        return name[: -len("_history")], "history"
    return name, "info"


def _condition_params(conditions: Mapping[str, Any] | Iterable[Condition] | None) -> dict[str, Any]:
    if conditions is None:
        return {}
    if isinstance(conditions, Mapping):
        params: dict[str, Any] = {}
        for field, value in conditions.items():
            if isinstance(value, tuple) and len(value) == 2:
                operator, actual_value = value
            else:
                operator, actual_value = ConditionOperator.EQ, value
            params[f"cond[{field}::{str(operator)}]"] = actual_value
        return params
    return {condition.param_name(): condition.value for condition in conditions}


def _timestamp_param(value: date | datetime | str) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y%m%d%H%M%S")
    if isinstance(value, date):
        return value.strftime("%Y%m%d000000")
    text = str(value).strip()
    digits = "".join(char for char in text if char.isdigit())
    if len(digits) == 8:
        return f"{digits}000000"
    if len(digits) == 14:
        return digits
    raise ValueError("since must be YYYYMMDD, YYYYMMDDHHMMSS, date, or datetime")


def _date_param(value: date | str) -> str:
    if isinstance(value, date):
        return value.strftime("%Y%m%d")
    text = str(value).strip()
    digits = "".join(char for char in text if char.isdigit())
    if len(digits) != 8:
        raise ValueError("base_date must be YYYYMMDD or date")
    return digits
