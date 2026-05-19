"""OpenAPI 원본 응답을 `MoisResponse`로 파싱합니다."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from typing import Any

from .exceptions import MoisAuthError, MoisParseError, MoisRequestError, MoisServerError
from .models import MoisResponse


def parse_openapi_response(response: Any, *, page_no: int, num_of_rows: int) -> MoisResponse:
    """HTTP 응답 객체를 JSON/XML 형식에 맞춰 파싱합니다."""

    headers = getattr(response, "headers", {}) or {}
    content_type = str(
        headers.get("Content-Type") or headers.get("content-type") or ""
    ).lower()
    text = getattr(response, "text", "")
    if "json" in content_type:
        try:
            payload = response.json()
        except ValueError as exc:
            raise MoisParseError("JSON 응답을 해석할 수 없습니다") from exc
        return parse_openapi_payload(payload, page_no=page_no, num_of_rows=num_of_rows)
    return parse_openapi_text(
        text,
        content_type=content_type,
        page_no=page_no,
        num_of_rows=num_of_rows,
    )


def parse_openapi_text(
    text: str,
    *,
    content_type: str = "",
    page_no: int = 1,
    num_of_rows: int = 100,
) -> MoisResponse:
    """문자열 응답 본문을 JSON 또는 XML로 파싱합니다."""

    stripped = text.lstrip()
    if "json" in content_type.lower() or stripped.startswith("{"):
        try:
            payload = json.loads(text)
        except ValueError as exc:
            raise MoisParseError("JSON 응답을 해석할 수 없습니다") from exc
        return parse_openapi_payload(payload, page_no=page_no, num_of_rows=num_of_rows)
    return _parse_xml_payload(text, page_no=page_no, num_of_rows=num_of_rows)


def parse_openapi_payload(
    payload: Any,
    *,
    page_no: int = 1,
    num_of_rows: int = 100,
) -> MoisResponse:
    """이미 JSON으로 디코딩된 OpenAPI payload를 파싱합니다."""

    return _parse_json_payload(payload, page_no=page_no, num_of_rows=num_of_rows)


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
