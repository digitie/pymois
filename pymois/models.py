"""공개 데이터 모델."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True, slots=True)
class OpenApiService:
    """지방행정 인허가정보 OpenAPI 업종 명세."""

    index: int
    slug: str
    category: str
    name: str
    title: str
    service_name: str
    info_url: str
    history_url: str
    info_operation: str
    history_operation: str


@dataclass(frozen=True, slots=True)
class OpenApiEndpoint:
    """OpenAPI의 단일 호출 URL 명세."""

    service_slug: str
    kind: str
    operation_name: str
    url: str


@dataclass(frozen=True, slots=True)
class FileDownload:
    """localdata 파일 다운로드 명세."""

    slug: str
    kind: str
    category: str
    name: str
    title: str
    info_url: str
    download_url: str
    info_path: str
    download_path: str


@dataclass(frozen=True, slots=True)
class ResponseField:
    """붙임3 응답변수 매핑 명세."""

    group: str | None
    local_field: str | None
    local_name: str | None
    field: str | None
    name: str | None
    type: str | None
    length: int | float | str | None
    note: str | None
    deleted: bool


@dataclass(frozen=True, slots=True)
class Condition:
    """data.go.kr cond[FIELD::OP] 조건."""

    field: str
    operator: str
    value: Any

    def param_name(self) -> str:
        return f"cond[{self.field}::{self.operator}]"


@dataclass(frozen=True, slots=True)
class MoisResponse:
    """OpenAPI 페이지 응답."""

    items: tuple[Mapping[str, Any], ...]
    page_no: int | None = None
    num_of_rows: int | None = None
    total_count: int | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Coordinate:
    """원본 EPSG:5174 좌표와 WGS84 좌표."""

    x: float
    y: float
    lon: float
    lat: float
    source_crs: str = "EPSG:5174"
    target_crs: str = "EPSG:4326"


@dataclass(frozen=True, slots=True)
class LocalDataRecord:
    """localdata CSV 한 행을 Python 타입으로 정규화한 객체."""

    service_slug: str | None
    category: str | None
    title: str | None
    data: Mapping[str, Any]
    raw: Mapping[str, str]
    coordinates: Coordinate | None = None
    management_number: str | None = None
    business_name: str | None = None
    license_date: date | None = None
    business_status_code: str | None = None
    business_status_name: str | None = None
    updated_at: datetime | None = None
    modified_at: datetime | None = None

    @classmethod
    def build(
        cls,
        *,
        service_slug: str | None,
        category: str | None,
        title: str | None,
        data: dict[str, Any],
        raw: dict[str, str],
        coordinates: Coordinate | None,
    ) -> LocalDataRecord:
        return cls(
            service_slug=service_slug,
            category=category,
            title=title,
            data=MappingProxyType(dict(data)),
            raw=MappingProxyType(dict(raw)),
            coordinates=coordinates,
            management_number=_str_or_none(data.get("MNG_NO")),
            business_name=_str_or_none(data.get("BPLC_NM")),
            license_date=data.get("LCPMT_YMD") if isinstance(data.get("LCPMT_YMD"), date) else None,
            business_status_code=_str_or_none(data.get("SALS_STTS_CD")),
            business_status_name=_str_or_none(data.get("SALS_STTS_NM")),
            updated_at=(
                data.get("DAT_UPDT_PNT")
                if isinstance(data.get("DAT_UPDT_PNT"), datetime)
                else None
            ),
            modified_at=(
                data.get("LAST_MDFCN_PNT")
                if isinstance(data.get("LAST_MDFCN_PNT"), datetime)
                else None
            ),
        )

    @property
    def is_open(self) -> bool | None:
        """영업/정상 상태이면 True, 폐업/취소 계열이면 False를 반환합니다."""

        if self.business_status_code == "01":
            return True
        if self.business_status_code in {"02", "03", "04"}:
            return False
        if self.business_status_name:
            if "폐업" in self.business_status_name or "취소" in self.business_status_name:
                return False
            if "영업" in self.business_status_name or "정상" in self.business_status_name:
                return True
        return None


def _str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
