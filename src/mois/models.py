"""공개 데이터 모델."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any, TypeAlias

ServiceSlug: TypeAlias = str
ManagementNumber: TypeAlias = str
OpenApiItem: TypeAlias = Mapping[str, Any]
LocalDataRow: TypeAlias = Mapping[str, Any]


class CoordinateReferenceSystem(StrEnum):
    """mois가 명시적으로 다루는 좌표계."""

    KATEC = "EPSG:5174"
    WGS84 = "EPSG:4326"


class OpenApiKind(StrEnum):
    """지방행정 인허가정보 OpenAPI 엔드포인트 종류."""

    INFO = "info"
    HISTORY = "history"


class FileDownloadKind(StrEnum):
    """localdata 파일 다운로드 종류."""

    LICENSE = "license"
    LIFE_CONVENIENCE = "life_convenience"


class ConditionOperator(StrEnum):
    """data.go.kr `cond[FIELD::OP]` 조건 연산자."""

    EQ = "EQ"
    NE = "NE"
    LT = "LT"
    LTE = "LTE"
    GT = "GT"
    GTE = "GTE"
    LIKE = "LIKE"


class SyncKind(StrEnum):
    """DB 동기화 작업 종류."""

    INFO = "info"
    HISTORY = "history"
    FILE = "file"


class BusinessStatusCategory(StrEnum):
    """영업상태코드/명에서 추론한 단순 상태 분류."""

    OPEN = "open"
    CLOSED = "closed"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class OpenApiService:
    """지방행정 인허가정보 OpenAPI 업종 명세."""

    index: int
    slug: str
    category: str
    name: str
    title: str
    service_name: str
    application_url: str
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
class IncrementalOpenApiEndpoint:
    """OpenAPI 증분조회 편의 함수와 신청 링크 명세."""

    service_slug: str
    category: str
    name: str
    title: str
    application_url: str
    info_url: str
    condition_field: str
    source_modified_field: str
    condition_operator: str
    get_method: str
    iter_method: str


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
    operator: str | ConditionOperator
    value: Any

    def param_name(self) -> str:
        return f"cond[{self.field}::{str(self.operator)}]"


@dataclass(frozen=True, slots=True)
class MoisResponse:
    """OpenAPI 페이지 응답."""

    items: tuple[Mapping[str, Any], ...]
    page_no: int | None = None
    num_of_rows: int | None = None
    total_count: int | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class KatecPoint:
    """localdata 원본 KATEC/Bessel 중부원점TM 좌표.

    축 순서는 항상 `(x, y)`입니다. EPSG:5174를 사용합니다.
    """

    x: float
    y: float
    crs: CoordinateReferenceSystem = CoordinateReferenceSystem.KATEC

    def __post_init__(self) -> None:
        object.__setattr__(self, "x", float(self.x))
        object.__setattr__(self, "y", float(self.y))
        object.__setattr__(self, "crs", CoordinateReferenceSystem(str(self.crs)))

    @property
    def katec_x(self) -> float:
        """호환성을 위한 KATEC X 좌표 별칭."""

        return self.x

    @property
    def katec_y(self) -> float:
        """호환성을 위한 KATEC Y 좌표 별칭."""

        return self.y

    def as_tuple(self) -> tuple[float, float]:
        """`(x, y)` 순서로 반환합니다."""

        return self.x, self.y

    def to_wgs84(self) -> Wgs84Point:
        """WGS84 `(lon, lat)` 좌표로 변환합니다."""

        from .coords import katec_to_wgs84_point

        return katec_to_wgs84_point(self)


@dataclass(frozen=True, slots=True)
class Wgs84Point:
    """WGS84 경도/위도 좌표.

    축 순서는 항상 `(lon, lat)`입니다. EPSG:4326을 사용합니다.
    """

    lon: float
    lat: float
    crs: CoordinateReferenceSystem = CoordinateReferenceSystem.WGS84

    def __post_init__(self) -> None:
        lon = float(self.lon)
        lat = float(self.lat)
        if not -180 <= lon <= 180:
            raise ValueError("lon must be between -180 and 180")
        if not -90 <= lat <= 90:
            raise ValueError("lat must be between -90 and 90")
        object.__setattr__(self, "lon", lon)
        object.__setattr__(self, "lat", lat)
        object.__setattr__(self, "crs", CoordinateReferenceSystem(str(self.crs)))

    @property
    def longitude(self) -> float:
        """경도 별칭."""

        return self.lon

    @property
    def latitude(self) -> float:
        """위도 별칭."""

        return self.lat

    def as_tuple(self) -> tuple[float, float]:
        """`(lon, lat)` 순서로 반환합니다."""

        return self.lon, self.lat

    def to_wkt(self) -> str:
        """공간 DB 등에 사용할 WKT Point 문자열을 반환합니다."""

        return f"POINT({self.lon} {self.lat})"

    def to_geojson_position(self) -> tuple[float, float]:
        """GeoJSON Position 규칙에 맞춰 `(lon, lat)` 순서로 반환합니다."""

        return self.as_tuple()


@dataclass(frozen=True, slots=True, init=False)
class StationCoordinates:
    """원본 KATEC 좌표와 WGS84 좌표를 함께 담는 좌표 값 객체.

    생성자는 `StationCoordinates(katec_x, katec_y, lon, lat)` 형태를 지원합니다.
    기존 `station.katec_x`, `station.katec_y`, `station.lon`, `station.lat`
    스타일 접근을 유지하면서 `katec_point`, `wgs84_point` 값 객체도 제공합니다.
    """

    katec_point: KatecPoint
    wgs84_point: Wgs84Point

    def __init__(
        self,
        katec_x: float,
        katec_y: float,
        lon: float,
        lat: float,
    ) -> None:
        object.__setattr__(self, "katec_point", KatecPoint(katec_x, katec_y))
        object.__setattr__(self, "wgs84_point", Wgs84Point(lon, lat))

    @classmethod
    def from_points(
        cls,
        katec_point: KatecPoint,
        wgs84_point: Wgs84Point,
    ) -> StationCoordinates:
        """이미 만든 좌표 값 객체에서 복합 좌표를 생성합니다."""

        return cls(katec_point.x, katec_point.y, wgs84_point.lon, wgs84_point.lat)

    @classmethod
    def from_katec(cls, katec_x: float, katec_y: float) -> StationCoordinates:
        """KATEC `(x, y)` 좌표를 WGS84까지 변환해 생성합니다."""

        katec_point = KatecPoint(katec_x, katec_y)
        return cls.from_points(katec_point, katec_point.to_wgs84())

    @property
    def katec_x(self) -> float:
        return self.katec_point.x

    @property
    def katec_y(self) -> float:
        return self.katec_point.y

    @property
    def x(self) -> float:
        """기존 `Coordinate.x` 호환 별칭."""

        return self.katec_x

    @property
    def y(self) -> float:
        """기존 `Coordinate.y` 호환 별칭."""

        return self.katec_y

    @property
    def lon(self) -> float:
        return self.wgs84_point.lon

    @property
    def lat(self) -> float:
        return self.wgs84_point.lat

    @property
    def source_crs(self) -> CoordinateReferenceSystem:
        return self.katec_point.crs

    @property
    def target_crs(self) -> CoordinateReferenceSystem:
        return self.wgs84_point.crs

    def to_wkt(self) -> str:
        """WGS84 좌표의 WKT Point 문자열을 반환합니다."""

        return self.wgs84_point.to_wkt()


@dataclass(frozen=True, slots=True)
class Coordinate:
    """원본 EPSG:5174 좌표와 WGS84 좌표.

    기존 호환성을 위해 `x`, `y`, `lon`, `lat` 필드를 유지합니다.
    새 코드에서는 `katec_point`, `wgs84_point`, `station_coordinates` 값 객체를
    함께 사용하는 것을 권장합니다.
    """

    x: float
    y: float
    lon: float
    lat: float
    source_crs: CoordinateReferenceSystem = CoordinateReferenceSystem.KATEC
    target_crs: CoordinateReferenceSystem = CoordinateReferenceSystem.WGS84

    def __post_init__(self) -> None:
        object.__setattr__(self, "x", float(self.x))
        object.__setattr__(self, "y", float(self.y))
        wgs84 = Wgs84Point(self.lon, self.lat)
        object.__setattr__(self, "lon", wgs84.lon)
        object.__setattr__(self, "lat", wgs84.lat)
        object.__setattr__(
            self,
            "source_crs",
            CoordinateReferenceSystem(str(self.source_crs)),
        )
        object.__setattr__(
            self,
            "target_crs",
            CoordinateReferenceSystem(str(self.target_crs)),
        )

    @classmethod
    def from_katec(cls, x: float, y: float) -> Coordinate:
        """KATEC `(x, y)` 좌표를 WGS84 `(lon, lat)`까지 변환해 생성합니다."""

        station = StationCoordinates.from_katec(x, y)
        return cls(station.katec_x, station.katec_y, station.lon, station.lat)

    @classmethod
    def from_points(cls, katec_point: KatecPoint, wgs84_point: Wgs84Point) -> Coordinate:
        """좌표 값 객체에서 기존 `Coordinate` 객체를 생성합니다."""

        return cls(katec_point.x, katec_point.y, wgs84_point.lon, wgs84_point.lat)

    @property
    def katec_x(self) -> float:
        """KATEC X 좌표 별칭."""

        return self.x

    @property
    def katec_y(self) -> float:
        """KATEC Y 좌표 별칭."""

        return self.y

    @property
    def katec_point(self) -> KatecPoint:
        """KATEC `(x, y)` 값 객체."""

        return KatecPoint(self.x, self.y)

    @property
    def wgs84_point(self) -> Wgs84Point:
        """WGS84 `(lon, lat)` 값 객체."""

        return Wgs84Point(self.lon, self.lat)

    @property
    def station_coordinates(self) -> StationCoordinates:
        """KATEC와 WGS84를 함께 담은 좌표 값 객체."""

        return StationCoordinates.from_points(self.katec_point, self.wgs84_point)

    def to_wkt(self) -> str:
        """WGS84 좌표의 WKT Point 문자열을 반환합니다."""

        return self.wgs84_point.to_wkt()


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

    @property
    def status_category(self) -> BusinessStatusCategory:
        """영업상태를 단순 enum으로 반환합니다."""

        if self.is_open is True:
            return BusinessStatusCategory.OPEN
        if self.is_open is False:
            return BusinessStatusCategory.CLOSED
        return BusinessStatusCategory.UNKNOWN


def _str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
