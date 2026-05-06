"""PostgreSQL/PostGIS 저장 모델과 변환 도우미."""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping
from datetime import date, datetime
from typing import Any, cast

from geoalchemy2 import Geometry, WKTElement
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from .models import LocalDataRecord

COMMON_DATA_FIELDS = frozenset(
    {
        "MNG_NO",
        "OPN_ATMY_GRP_CD",
        "LCPMT_YMD",
        "CLSBIZ_YMD",
        "SALS_STTS_CD",
        "SALS_STTS_NM",
        "BPLC_NM",
        "TELNO",
        "LCTN_ZIP",
        "LOTNO_ADDR",
        "ROAD_NM_ADDR",
        "ROAD_NM_ZIP",
        "LCTN_AREA",
        "LAST_MDFCN_PNT",
        "DAT_UPDT_PNT",
        "CRD_INFO_X",
        "CRD_INFO_Y",
        "WGS84_LON",
        "WGS84_LAT",
        "LEGAL_DONG_CD",
        "ADM_CD",
        "BJD_CD",
        "RN_MGT_SN",
        "ROAD_NM_CD",
        "BD_MGT_SN",
        "BUILDING_MANAGEMENT_NO",
        "ROAD_NM_EMD_NO",
    }
)

LEGAL_DONG_FIELD_CANDIDATES = (
    "LEGAL_DONG_CD",
    "ADM_CD",
    "BJD_CD",
    "LAB_ROAD_NM_ADDR_EMD_CD",
)
ROAD_NAME_CODE_FIELD_CANDIDATES = (
    "RN_MGT_SN",
    "ROAD_NM_CD",
    "LAB_ROAD_NM_ADDR_CD",
)
BUILDING_MANAGEMENT_FIELD_CANDIDATES = (
    "BD_MGT_SN",
    "BD_MNG_NO",
    "BLD_MNG_NO",
    "BUILDING_MANAGEMENT_NO",
)


class Base(DeclarativeBase):
    """SQLAlchemy 2 Declarative Base."""


class PlaceRecord(BaseModel):
    """인허가 원천 레코드를 DB 적재용으로 정규화한 Pydantic 모델."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    service_slug: str
    mng_no: str | None = None
    category: str | None = None
    title: str | None = None
    domain_category: str | None = None
    opn_authority_code: str | None = None
    place_name: str | None = None
    status_code: str | None = None
    status_name: str | None = None
    is_open: bool | None = None
    license_date: date | None = None
    closed_date: date | None = None
    telno: str | None = None
    road_address: str | None = None
    lot_address: str | None = None
    road_zip: str | None = None
    lot_zip: str | None = None
    legal_dong_code: str | None = None
    road_name_code: str | None = None
    building_management_number: str | None = None
    road_name_emd_no: str | None = None
    source_x: float | None = None
    source_y: float | None = None
    lon: float | None = None
    lat: float | None = None
    data_updated_at: datetime | None = None
    source_modified_at: datetime | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    raw: dict[str, str] = Field(default_factory=dict)

    @field_validator("*", mode="before")
    @classmethod
    def _blank_string_to_none(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @classmethod
    def from_local_data_record(
        cls,
        record: LocalDataRecord,
        *,
        domain_category: str | None = None,
    ) -> PlaceRecord:
        """`LocalDataRecord`에서 공통 검색/연계 필드를 추출합니다."""

        data = dict(record.data)
        category = record.category
        title = record.title
        name = _text(data, "BPLC_NM") or record.business_name
        coords = record.coordinates
        return cls(
            service_slug=record.service_slug or "",
            mng_no=record.management_number,
            category=category,
            title=title,
            domain_category=domain_category or infer_domain_category(category, title),
            opn_authority_code=_text(data, "OPN_ATMY_GRP_CD"),
            place_name=name,
            status_code=record.business_status_code,
            status_name=record.business_status_name,
            is_open=record.is_open,
            license_date=record.license_date,
            closed_date=_date_value(data.get("CLSBIZ_YMD")),
            telno=_text(data, "TELNO"),
            road_address=_first_text(data, "ROAD_NM_ADDR", "ROAD_NM_WHOL_ADDR"),
            lot_address=_first_text(data, "LOTNO_ADDR", "LCTN_WHOL_ADDR", "LCTN"),
            road_zip=_text(data, "ROAD_NM_ZIP"),
            lot_zip=_text(data, "LCTN_ZIP"),
            legal_dong_code=_first_text(data, *LEGAL_DONG_FIELD_CANDIDATES),
            road_name_code=_first_text(data, *ROAD_NAME_CODE_FIELD_CANDIDATES),
            building_management_number=_first_text(data, *BUILDING_MANAGEMENT_FIELD_CANDIDATES),
            road_name_emd_no=_text(data, "ROAD_NM_EMD_NO"),
            source_x=coords.x if coords else None,
            source_y=coords.y if coords else None,
            lon=coords.lon if coords else _float_value(data.get("WGS84_LON")),
            lat=coords.lat if coords else _float_value(data.get("WGS84_LAT")),
            data_updated_at=record.updated_at,
            source_modified_at=record.modified_at,
            data=data,
            raw=dict(record.raw),
        )

    @property
    def point_wkt(self) -> str | None:
        """WGS84 좌표가 있으면 PostGIS WKT 문자열을 반환합니다."""

        if self.lon is None or self.lat is None:
            return None
        return f"POINT({self.lon} {self.lat})"

    def point_element(self) -> Any | None:
        """SQLAlchemy/GeoAlchemy2에 전달할 WKTElement를 반환합니다."""

        if self.point_wkt is None:
            return None
        return WKTElement(self.point_wkt, srid=4326)

    def json_data(self) -> dict[str, Any]:
        """JSONB 저장에 사용할 `data`를 JSON 호환 타입으로 변환합니다."""

        dumped = self.model_dump(mode="json")
        return cast(dict[str, Any], dumped["data"])

    def json_raw(self) -> dict[str, str]:
        """JSONB 저장에 사용할 원본 행을 반환합니다."""

        dumped = self.model_dump(mode="json")
        return cast(dict[str, str], dumped["raw"])

    def specific_data(self) -> dict[str, Any]:
        """마스터 테이블에 분리한 공통 필드를 제외한 업종별 필드를 반환합니다."""

        return {
            key: value
            for key, value in self.json_data().items()
            if key not in COMMON_DATA_FIELDS and value is not None
        }


class PlaceMaster(Base):
    """공간 검색과 공통 필터링을 담당하는 인허가 마스터 테이블."""

    __tablename__ = "mois_place_master"
    __table_args__ = (
        UniqueConstraint("service_slug", "mng_no", name="uq_mois_place_master_source"),
        Index("ix_mois_place_master_status", "service_slug", "status_code"),
        Index("ix_mois_place_master_authority", "opn_authority_code"),
        Index("ix_mois_place_master_legal_dong", "legal_dong_code"),
        Index("ix_mois_place_master_road_name", "road_name_code"),
        Index("ix_mois_place_master_geom", "geom", postgresql_using="gist"),
    )

    place_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    service_slug: Mapped[str] = mapped_column(String(120), nullable=False)
    mng_no: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[str | None] = mapped_column(String(80))
    title: Mapped[str | None] = mapped_column(String(160))
    domain_category: Mapped[str | None] = mapped_column(String(80))
    opn_authority_code: Mapped[str | None] = mapped_column(String(20))
    place_name: Mapped[str | None] = mapped_column(String(300))
    status_code: Mapped[str | None] = mapped_column(String(20))
    status_name: Mapped[str | None] = mapped_column(String(80))
    is_open: Mapped[bool | None] = mapped_column(Boolean)
    license_date: Mapped[date | None] = mapped_column(Date)
    closed_date: Mapped[date | None] = mapped_column(Date)
    telno: Mapped[str | None] = mapped_column(String(40))
    road_address: Mapped[str | None] = mapped_column(Text)
    lot_address: Mapped[str | None] = mapped_column(Text)
    road_zip: Mapped[str | None] = mapped_column(String(10))
    lot_zip: Mapped[str | None] = mapped_column(String(10))
    legal_dong_code: Mapped[str | None] = mapped_column(String(10))
    road_name_code: Mapped[str | None] = mapped_column(String(20))
    building_management_number: Mapped[str | None] = mapped_column(String(30))
    road_name_emd_no: Mapped[str | None] = mapped_column(String(10))
    source_x: Mapped[float | None]
    source_y: Mapped[float | None]
    lon: Mapped[float | None]
    lat: Mapped[float | None]
    geom: Mapped[Any | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
    )
    data_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class PlaceDetail(Base):
    """업종별 특수 필드와 원본 payload를 JSONB로 보관하는 상세 테이블."""

    __tablename__ = "mois_place_detail"
    __table_args__ = (
        Index("ix_mois_place_detail_specific_gin", "specific_data", postgresql_using="gin"),
    )

    place_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("mois_place_master.place_id", ondelete="CASCADE"),
        primary_key=True,
    )
    specific_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    record_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    raw_data: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class BatchSyncLog(Base):
    """증분/파일 동기화 실행 상태를 저장하는 로그 테이블."""

    __tablename__ = "mois_batch_sync_log"

    service_slug: Mapped[str] = mapped_column(String(120), primary_key=True)
    sync_kind: Mapped[str] = mapped_column(String(40), primary_key=True)
    condition_field: Mapped[str | None] = mapped_column(String(80))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_page_no: Mapped[int | None] = mapped_column(Integer)
    fetched_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


def infer_domain_category(category: str | None, title: str | None = None) -> str | None:
    """인허가 분류와 업종명으로 여행/상권 분석용 도메인을 추정합니다."""

    text_value = f"{category or ''} {title or ''}"
    if any(word in text_value for word in ("음식", "식품", "제과", "급식", "주점")):
        return "식음료"
    if any(word in text_value for word in ("숙박", "민박", "펜션", "야영", "관광숙박")):
        return "숙박/체류"
    if any(word in text_value for word in ("병원", "약국", "의료", "안전상비", "응급")):
        return "안전/보건"
    if any(word in text_value for word in ("공연", "관광", "영화", "게임", "체육", "박물관")):
        return "문화/여가"
    if category == "생활":
        return "생활편의/상권"
    if category == "자원환경":
        return "환경/안전"
    if category == "동물":
        return "반려/동물"
    return category


def record_to_place_record(
    record: LocalDataRecord,
    *,
    domain_category: str | None = None,
) -> PlaceRecord:
    """`LocalDataRecord`를 DB 적재용 Pydantic 모델로 변환합니다."""

    return PlaceRecord.from_local_data_record(record, domain_category=domain_category)


def place_master_values(
    place: PlaceRecord,
    *,
    place_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """`mois_place_master` UPSERT에 사용할 값을 만듭니다."""

    if not place.mng_no:
        raise ValueError("mng_no is required for database upsert")
    values: dict[str, Any] = {
        "service_slug": place.service_slug,
        "mng_no": place.mng_no,
        "category": place.category,
        "title": place.title,
        "domain_category": place.domain_category,
        "opn_authority_code": place.opn_authority_code,
        "place_name": place.place_name,
        "status_code": place.status_code,
        "status_name": place.status_name,
        "is_open": place.is_open,
        "license_date": place.license_date,
        "closed_date": place.closed_date,
        "telno": place.telno,
        "road_address": place.road_address,
        "lot_address": place.lot_address,
        "road_zip": place.road_zip,
        "lot_zip": place.lot_zip,
        "legal_dong_code": place.legal_dong_code,
        "road_name_code": place.road_name_code,
        "building_management_number": place.building_management_number,
        "road_name_emd_no": place.road_name_emd_no,
        "source_x": place.source_x,
        "source_y": place.source_y,
        "lon": place.lon,
        "lat": place.lat,
        "geom": place.point_element(),
        "data_updated_at": place.data_updated_at,
        "source_modified_at": place.source_modified_at,
    }
    if place_id is not None:
        values["place_id"] = place_id
    return values


def place_detail_values(place: PlaceRecord, place_id: uuid.UUID) -> dict[str, Any]:
    """`mois_place_detail` UPSERT에 사용할 값을 만듭니다."""

    return {
        "place_id": place_id,
        "specific_data": place.specific_data(),
        "record_data": place.json_data(),
        "raw_data": place.json_raw(),
    }


def build_place_models(
    place: PlaceRecord,
    *,
    place_id: uuid.UUID | None = None,
) -> tuple[PlaceMaster, PlaceDetail]:
    """DB 세션에 직접 add할 수 있는 ORM 객체 쌍을 만듭니다."""

    actual_place_id = place_id or uuid.uuid4()
    master = PlaceMaster(**place_master_values(place, place_id=actual_place_id))
    detail = PlaceDetail(**place_detail_values(place, actual_place_id))
    return master, detail


def create_postgis_schema(engine: Engine, *, create_extension: bool = True) -> None:
    """PostGIS 확장과 `pymois` 테이블을 생성합니다."""

    with engine.begin() as connection:
        if create_extension:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        Base.metadata.create_all(connection)


def upsert_place(
    session: Session,
    record: LocalDataRecord | PlaceRecord,
    *,
    commit: bool = False,
) -> uuid.UUID:
    """단일 인허가 레코드를 `(service_slug, mng_no)` 기준으로 UPSERT합니다."""

    place = record if isinstance(record, PlaceRecord) else record_to_place_record(record)
    master_values = place_master_values(place)
    master_insert = insert(PlaceMaster).values(**master_values)
    master_update_values = _excluded_update_values(
        master_insert,
        master_values,
        skip={"place_id", "service_slug", "mng_no"},
    )
    master_update_values["updated_at"] = func.now()
    master_statement = (
        master_insert.on_conflict_do_update(
            constraint="uq_mois_place_master_source",
            set_=master_update_values,
        )
        .returning(PlaceMaster.place_id)
    )
    place_id = session.execute(master_statement).scalar_one()

    detail_values = place_detail_values(place, place_id)
    detail_insert = insert(PlaceDetail).values(**detail_values)
    detail_update_values = _excluded_update_values(detail_insert, detail_values, skip={"place_id"})
    detail_update_values["updated_at"] = func.now()
    detail_statement = detail_insert.on_conflict_do_update(
        index_elements=[PlaceDetail.place_id],
        set_=detail_update_values,
    )
    session.execute(detail_statement)
    if commit:
        session.commit()
    return place_id


def upsert_places(
    session: Session,
    records: Iterable[LocalDataRecord | PlaceRecord],
    *,
    commit: bool = False,
) -> int:
    """여러 인허가 레코드를 순차 UPSERT하고 처리 건수를 반환합니다."""

    count = 0
    for record in records:
        upsert_place(session, record)
        count += 1
    if commit:
        session.commit()
    return count


def _excluded_update_values(
    insert_statement: Any,
    values: Mapping[str, Any],
    *,
    skip: set[str],
) -> dict[str, Any]:
    return {
        key: getattr(insert_statement.excluded, key)
        for key in values
        if key not in skip
    }


def _first_text(data: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = _text(data, key)
        if value is not None:
            return value
    return None


def _text(data: Mapping[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    text_value = str(value).strip()
    return text_value or None


def _date_value(value: object) -> date | None:
    return value if isinstance(value, date) and not isinstance(value, datetime) else None


def _float_value(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None
