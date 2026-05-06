"""data.go.kr 지방행정 인허가정보 OpenAPI 클라이언트."""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Iterator, Mapping
from datetime import date, datetime
from typing import Any

from requests import RequestException

from ._http import build_session, raise_for_http_error
from .catalogs import get_openapi_service
from .exceptions import MoisAuthError, MoisParseError, MoisRequestError, MoisServerError
from .models import Condition, MoisResponse


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
        kind: str = "info",
        page_no: int = 1,
        num_of_rows: int = 100,
        conditions: Mapping[str, Any] | Iterable[Condition] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> MoisResponse:
        """업종 slug와 구분(info/history)으로 한 페이지를 호출합니다."""

        if kind not in {"info", "history"}:
            raise ValueError('kind must be "info" or "history"')
        if page_no < 1:
            raise ValueError("page_no must be >= 1")
        if not 1 <= num_of_rows <= 100:
            raise ValueError("num_of_rows must be between 1 and 100")

        url = self._endpoint_url(slug, kind)
        request_params: dict[str, Any] = {
            "serviceKey": self.service_key,
            "pageNo": page_no,
            "numOfRows": num_of_rows,
        }
        request_params.update(_condition_params(conditions))
        if params:
            request_params.update(params)

        try:
            response = self.session.get(url, params=request_params, timeout=self.timeout)
            raise_for_http_error(response, f"{slug}/{kind}")
        except RequestException as exc:
            raise MoisRequestError(f"{slug}/{kind}: request failed") from exc

        return _parse_openapi_response(response, page_no=page_no, num_of_rows=num_of_rows)

    def get(
        self,
        slug: str,
        *,
        kind: str = "info",
        page_no: int = 1,
        num_of_rows: int = 100,
        conditions: Mapping[str, Any] | Iterable[Condition] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> list[Mapping[str, Any]]:
        """한 페이지의 item 목록만 반환합니다."""

        return list(
            self.request(
                slug,
                kind=kind,
                page_no=page_no,
                num_of_rows=num_of_rows,
                conditions=conditions,
                params=params,
            ).items
        )

    def iter_records(
        self,
        slug: str,
        *,
        kind: str = "info",
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
            conditions=[Condition(field, "GTE", _timestamp_param(since))],
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

        conditions: list[Condition] = [Condition("BASE_DATE", "EQ", _date_param(base_date))]
        if org_code:
            conditions.append(Condition("OPN_ATMY_GRP_CD", "EQ", org_code))
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
        """`get_hospitals()`처럼 slug 기반 편의 메서드를 동적으로 제공합니다."""

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
                operator, actual_value = "EQ", value
            params[f"cond[{field}::{operator}]"] = actual_value
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


def _parse_openapi_response(response: Any, *, page_no: int, num_of_rows: int) -> MoisResponse:
    content_type = str(getattr(response, "headers", {}).get("Content-Type", "")).lower()
    text = getattr(response, "text", "")
    if "json" in content_type:
        try:
            payload = response.json()
        except ValueError as exc:
            raise MoisParseError("JSON 응답을 해석할 수 없습니다") from exc
        return _parse_json_payload(payload, page_no=page_no, num_of_rows=num_of_rows)
    stripped = text.lstrip()
    if stripped.startswith("{"):
        try:
            return _parse_json_payload(response.json(), page_no=page_no, num_of_rows=num_of_rows)
        except ValueError as exc:
            raise MoisParseError("JSON 응답을 해석할 수 없습니다") from exc
    return _parse_xml_payload(text, page_no=page_no, num_of_rows=num_of_rows)


def _parse_json_payload(payload: Any, *, page_no: int, num_of_rows: int) -> MoisResponse:
    if not isinstance(payload, Mapping):
        raise MoisParseError("JSON 응답 최상위가 객체가 아닙니다")
    envelope = payload.get("response", payload)
    if not isinstance(envelope, Mapping):
        raise MoisParseError("JSON response가 객체가 아닙니다")
    header = envelope.get("header", {})
    if isinstance(header, Mapping):
        _raise_for_result(header.get("resultCode"), header.get("resultMsg"))
    body = envelope.get("body", envelope)
    if not isinstance(body, Mapping):
        raise MoisParseError("JSON body가 객체가 아닙니다")
    items = _extract_items(body)
    return MoisResponse(
        items=tuple(items),
        page_no=_int_or_none(body.get("pageNo")) or page_no,
        num_of_rows=_int_or_none(body.get("numOfRows")) or num_of_rows,
        total_count=_int_or_none(body.get("totalCount")),
        raw=payload,
    )


def _parse_xml_payload(text: str, *, page_no: int, num_of_rows: int) -> MoisResponse:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise MoisParseError("XML 응답을 해석할 수 없습니다") from exc
    header = root.find(".//header")
    if header is not None:
        _raise_for_result(_child_text(header, "resultCode"), _child_text(header, "resultMsg"))
    body_element = root.find(".//body")
    body = body_element if body_element is not None else root
    items = [_xml_item_to_dict(item) for item in body.findall(".//item")]
    return MoisResponse(
        items=tuple(items),
        page_no=_int_or_none(_child_text(body, "pageNo")) or page_no,
        num_of_rows=_int_or_none(_child_text(body, "numOfRows")) or num_of_rows,
        total_count=_int_or_none(_child_text(body, "totalCount")),
        raw={"xml": text},
    )


def _extract_items(body: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    source = body.get("items", body.get("item", body.get("data", [])))
    if isinstance(source, Mapping) and "item" in source:
        source = source["item"]
    if source is None:
        return []
    if isinstance(source, Mapping):
        return [source]
    if isinstance(source, list) and all(isinstance(item, Mapping) for item in source):
        return source
    raise MoisParseError("items.item을 목록으로 해석할 수 없습니다")


def _xml_item_to_dict(element: ET.Element) -> dict[str, Any]:
    return {child.tag: child.text for child in list(element)}


def _child_text(element: ET.Element, name: str) -> str | None:
    child = element.find(name)
    return child.text if child is not None else None


def _raise_for_result(code: Any, message: Any) -> None:
    if code in (None, "", "00", "0"):
        return
    text = f"OpenAPI resultCode={code}: {message or ''}".strip()
    if str(code) in {"20", "30", "31"}:
        raise MoisAuthError(text)
    if str(code) in {"04", "99"}:
        raise MoisServerError(text)
    raise MoisRequestError(text)


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        return None
