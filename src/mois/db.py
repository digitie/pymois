"""SQLite/SpatiaLite 저장 모델과 변환 도우미."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import (
    JSON,
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
    select,
    text,
    tuple_,
)
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from .convert import field_for_header
from .models import KatecPoint, LocalDataRecord, StationCoordinates, Wgs84Point

PROMOTED_DATA_FIELDS = frozenset(
    {
        "MNG_NO",
        "OPN_ATMY_GRP_CD",
        "LCPMT_YMD",
        "LCPMT_RTRCN_YMD",
        "CLSBIZ_YMD",
        "SALS_STTS_CD",
        "SALS_STTS_NM",
        "DTL_SALS_STTS_CD",
        "DTL_SALS_STTS_NM",
        "BPLC_NM",
        "BZSTAT_SE_NM",
        "TELNO",
        "LCTN_ZIP",
        "LOTNO_ADDR",
        "LCTN_WHOL_ADDR",
        "LCTN",
        "ROAD_NM_ADDR",
        "ROAD_NM_WHOL_ADDR",
        "ROAD_NM_ZIP",
        "LCTN_AREA",
        "LAST_MDFCN_PNT",
        "DAT_UPDT_SE",
        "DAT_UPDT_PNT",
        "CRD_INFO_X",
        "CRD_INFO_Y",
        "WGS84_LON",
        "WGS84_LAT",
        "TCBIZ_BGNG_YMD",
        "TCBIZ_END_YMD",
        "ROBIZ_YMD",
        "MLT_UTZTN_BSNSSP_YN",
        "SNTTN_BZSTAT_NM",
        "FCLT_TOTAL_SCL",
        "WTRSPPL_FCLT_SE_NM",
        "CULTR_SPTS_TPBIZ_NM",
        "TPBIZ_SE_NM",
        "ANMLHSBNDR_TASK_SE_NM",
        "ENVRNMNT_TASK_SE_NM",
        "NTSL_MTH_NM",
        "DSGN_YMD",
        "BLDG_PSN_SE_NM",
        "BLDG_USG_NM",
        "GRND_NOFL",
        "UDGD_NOFL",
        "TOTAL_NOFL",
        "FCAR",
        "TOT_AR",
        "SCKBD_CNT",
        "BED_CNT",
        "HCWKR_CNT",
        "HSPTLZRM_CNT",
        "MDLCR_INST_BTP_NM",
        "MDEXM_SBJCT_CN_NM",
        "LEGAL_DONG_CD",
        "ADM_CD",
        "BJD_CD",
        "LAB_ROAD_NM_ADDR_EMD_CD",
        "RN_MGT_SN",
        "ROAD_NM_CD",
        "LAB_ROAD_NM_ADDR_CD",
        "BD_MGT_SN",
        "BD_MNG_NO",
        "BLD_MNG_NO",
        "BUILDING_MANAGEMENT_NO",
        "ROAD_NM_EMD_NO",
    }
)
COMMON_DATA_FIELDS = PROMOTED_DATA_FIELDS

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
SUBTYPE_FIELD_CANDIDATES = (
    "BZSTAT_SE_NM",
    "SNTTN_BZSTAT_NM",
    "CULTR_SPTS_TPBIZ_NM",
    "TPBIZ_SE_NM",
    "ANMLHSBNDR_TASK_SE_NM",
    "ENVRNMNT_TASK_SE_NM",
    "MDLCR_INST_BTP_NM",
)
SPATIALITE_GEOMETRY_COLUMN = "geom"
PLACE_ID_NAMESPACE = uuid.UUID("147a7b36-e10a-4a4a-9487-c24fc397605f")


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
    detail_status_code: str | None = None
    detail_status_name: str | None = None
    is_open: bool | None = None
    license_date: date | None = None
    license_cancelled_date: date | None = None
    closed_date: date | None = None
    temporary_business_start_date: date | None = None
    temporary_business_end_date: date | None = None
    reopen_date: date | None = None
    data_update_type: str | None = None
    telno: str | None = None
    road_address: str | None = None
    lot_address: str | None = None
    road_zip: str | None = None
    lot_zip: str | None = None
    business_type_name: str | None = None
    subtype_name: str | None = None
    multi_use_business_place_yn: str | None = None
    sanitation_business_status_name: str | None = None
    facility_total_scale: str | None = None
    water_supply_facility_type_name: str | None = None
    culture_sports_business_type_name: str | None = None
    sales_method_name: str | None = None
    designation_date: date | None = None
    building_ownership_type_name: str | None = None
    building_usage_name: str | None = None
    ground_floor_count: int | None = None
    underground_floor_count: int | None = None
    total_floor_count: int | None = None
    facility_area: float | None = None
    total_area: float | None = None
    sickbed_count: int | None = None
    bed_count: int | None = None
    healthcare_worker_count: int | None = None
    hospital_room_count: int | None = None
    medical_institution_type_name: str | None = None
    medical_subject_names: str | None = None
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
            mng_no=_record_management_key(record),
            category=category,
            title=title,
            domain_category=domain_category or infer_domain_category(category, title),
            opn_authority_code=_text(data, "OPN_ATMY_GRP_CD"),
            place_name=name,
            status_code=record.business_status_code,
            status_name=record.business_status_name,
            detail_status_code=_text(data, "DTL_SALS_STTS_CD"),
            detail_status_name=_text(data, "DTL_SALS_STTS_NM"),
            is_open=record.is_open,
            license_date=record.license_date,
            license_cancelled_date=_date_value(data.get("LCPMT_RTRCN_YMD")),
            closed_date=_date_value(data.get("CLSBIZ_YMD")),
            temporary_business_start_date=_date_value(data.get("TCBIZ_BGNG_YMD")),
            temporary_business_end_date=_date_value(data.get("TCBIZ_END_YMD")),
            reopen_date=_date_value(data.get("ROBIZ_YMD")),
            data_update_type=_text(data, "DAT_UPDT_SE"),
            telno=_text(data, "TELNO"),
            road_address=_first_text(data, "ROAD_NM_ADDR", "ROAD_NM_WHOL_ADDR"),
            lot_address=_first_text(data, "LOTNO_ADDR", "LCTN_WHOL_ADDR", "LCTN"),
            road_zip=_text(data, "ROAD_NM_ZIP"),
            lot_zip=_text(data, "LCTN_ZIP"),
            business_type_name=_text(data, "BZSTAT_SE_NM"),
            subtype_name=_first_text(data, *SUBTYPE_FIELD_CANDIDATES),
            multi_use_business_place_yn=_text(data, "MLT_UTZTN_BSNSSP_YN"),
            sanitation_business_status_name=_text(data, "SNTTN_BZSTAT_NM"),
            facility_total_scale=_text(data, "FCLT_TOTAL_SCL"),
            water_supply_facility_type_name=_text(data, "WTRSPPL_FCLT_SE_NM"),
            culture_sports_business_type_name=_text(data, "CULTR_SPTS_TPBIZ_NM"),
            sales_method_name=_text(data, "NTSL_MTH_NM"),
            designation_date=_date_value(data.get("DSGN_YMD")),
            building_ownership_type_name=_text(data, "BLDG_PSN_SE_NM"),
            building_usage_name=_text(data, "BLDG_USG_NM"),
            ground_floor_count=_int_value(data.get("GRND_NOFL")),
            underground_floor_count=_int_value(data.get("UDGD_NOFL")),
            total_floor_count=_int_value(data.get("TOTAL_NOFL")),
            facility_area=_float_value(data.get("FCAR")),
            total_area=_float_value(data.get("TOT_AR") or data.get("LCTN_AREA")),
            sickbed_count=_int_value(data.get("SCKBD_CNT")),
            bed_count=_int_value(data.get("BED_CNT")),
            healthcare_worker_count=_int_value(data.get("HCWKR_CNT")),
            hospital_room_count=_int_value(data.get("HSPTLZRM_CNT")),
            medical_institution_type_name=_text(data, "MDLCR_INST_BTP_NM"),
            medical_subject_names=_text(data, "MDEXM_SBJCT_CN_NM"),
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
        """WGS84 좌표가 있으면 WKT Point 문자열을 반환합니다."""

        if self.wgs84_point is None:
            return None
        return self.wgs84_point.to_wkt()

    @property
    def katec_x(self) -> float | None:
        """호환성을 위한 원본 KATEC X 좌표 별칭."""

        return self.source_x

    @property
    def katec_y(self) -> float | None:
        """호환성을 위한 원본 KATEC Y 좌표 별칭."""

        return self.source_y

    @property
    def katec_point(self) -> KatecPoint | None:
        """원본 EPSG:5174 `(x, y)` 좌표 값 객체."""

        if self.source_x is None or self.source_y is None:
            return None
        return KatecPoint(self.source_x, self.source_y)

    @property
    def wgs84_point(self) -> Wgs84Point | None:
        """WGS84 `(lon, lat)` 좌표 값 객체."""

        if self.lon is None or self.lat is None:
            return None
        return Wgs84Point(self.lon, self.lat)

    @property
    def station_coordinates(self) -> StationCoordinates | None:
        """KATEC와 WGS84를 함께 담은 좌표 값 객체."""

        if self.katec_point is None or self.wgs84_point is None:
            return None
        return StationCoordinates.from_points(self.katec_point, self.wgs84_point)

    def json_data(self) -> dict[str, Any]:
        """SQLite JSON 저장에 사용할 `data`를 JSON 호환 타입으로 변환합니다."""

        dumped = self.model_dump(mode="json")
        return cast(dict[str, Any], dumped["data"])

    def json_raw(self) -> dict[str, str]:
        """SQLite JSON 저장에 사용할 비승격 원본 행을 반환합니다."""

        dumped = self.model_dump(mode="json")
        raw = cast(dict[str, str], dumped["raw"])
        return {
            key: value
            for key, value in raw.items()
            if field_for_header(key) not in PROMOTED_DATA_FIELDS and value
        }

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
        Index("ix_mois_place_master_detail_status", "service_slug", "detail_status_code"),
        Index("ix_mois_place_master_data_update_type", "data_update_type"),
        Index("ix_mois_place_master_authority", "opn_authority_code"),
        Index("ix_mois_place_master_legal_dong", "legal_dong_code"),
        Index("ix_mois_place_master_road_name", "road_name_code"),
        Index("ix_mois_place_master_lon_lat", "lon", "lat"),
        Index("ix_mois_place_master_subtype", "service_slug", "subtype_name"),
        Index("ix_mois_place_master_sales_method", "sales_method_name"),
    )

    place_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    service_slug: Mapped[str] = mapped_column(String(120), nullable=False)
    mng_no: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str | None] = mapped_column(String(80))
    title: Mapped[str | None] = mapped_column(String(160))
    domain_category: Mapped[str | None] = mapped_column(String(80))
    opn_authority_code: Mapped[str | None] = mapped_column(String(20))
    place_name: Mapped[str | None] = mapped_column(String(300))
    status_code: Mapped[str | None] = mapped_column(String(20))
    status_name: Mapped[str | None] = mapped_column(String(80))
    detail_status_code: Mapped[str | None] = mapped_column(String(20))
    detail_status_name: Mapped[str | None] = mapped_column(String(120))
    is_open: Mapped[bool | None] = mapped_column(Boolean)
    license_date: Mapped[date | None] = mapped_column(Date)
    license_cancelled_date: Mapped[date | None] = mapped_column(Date)
    closed_date: Mapped[date | None] = mapped_column(Date)
    temporary_business_start_date: Mapped[date | None] = mapped_column(Date)
    temporary_business_end_date: Mapped[date | None] = mapped_column(Date)
    reopen_date: Mapped[date | None] = mapped_column(Date)
    data_update_type: Mapped[str | None] = mapped_column(String(10))
    telno: Mapped[str | None] = mapped_column(String(40))
    road_address: Mapped[str | None] = mapped_column(Text)
    lot_address: Mapped[str | None] = mapped_column(Text)
    road_zip: Mapped[str | None] = mapped_column(String(10))
    lot_zip: Mapped[str | None] = mapped_column(String(10))
    business_type_name: Mapped[str | None] = mapped_column(String(120))
    subtype_name: Mapped[str | None] = mapped_column(String(160))
    multi_use_business_place_yn: Mapped[str | None] = mapped_column(String(1))
    sanitation_business_status_name: Mapped[str | None] = mapped_column(String(120))
    facility_total_scale: Mapped[str | None] = mapped_column(String(80))
    water_supply_facility_type_name: Mapped[str | None] = mapped_column(String(200))
    culture_sports_business_type_name: Mapped[str | None] = mapped_column(String(160))
    sales_method_name: Mapped[str | None] = mapped_column(String(300))
    designation_date: Mapped[date | None] = mapped_column(Date)
    building_ownership_type_name: Mapped[str | None] = mapped_column(String(80))
    building_usage_name: Mapped[str | None] = mapped_column(String(160))
    ground_floor_count: Mapped[int | None] = mapped_column(Integer)
    underground_floor_count: Mapped[int | None] = mapped_column(Integer)
    total_floor_count: Mapped[int | None] = mapped_column(Integer)
    facility_area: Mapped[float | None]
    total_area: Mapped[float | None]
    sickbed_count: Mapped[int | None] = mapped_column(Integer)
    bed_count: Mapped[int | None] = mapped_column(Integer)
    healthcare_worker_count: Mapped[int | None] = mapped_column(Integer)
    hospital_room_count: Mapped[int | None] = mapped_column(Integer)
    medical_institution_type_name: Mapped[str | None] = mapped_column(String(120))
    medical_subject_names: Mapped[str | None] = mapped_column(Text)
    legal_dong_code: Mapped[str | None] = mapped_column(String(10))
    road_name_code: Mapped[str | None] = mapped_column(String(20))
    building_management_number: Mapped[str | None] = mapped_column(String(30))
    road_name_emd_no: Mapped[str | None] = mapped_column(String(10))
    source_x: Mapped[float | None]
    source_y: Mapped[float | None]
    lon: Mapped[float | None]
    lat: Mapped[float | None]
    geom_wkt: Mapped[str | None] = mapped_column(Text)
    data_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )


class PlaceDetail(Base):
    """업종별 특수 필드와 원본 payload를 SQLite JSON으로 보관하는 상세 테이블."""

    __tablename__ = "mois_place_detail"

    place_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("mois_place_master.place_id", ondelete="CASCADE"),
        primary_key=True,
    )
    specific_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    raw_data: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
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
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
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
        "detail_status_code": place.detail_status_code,
        "detail_status_name": place.detail_status_name,
        "is_open": place.is_open,
        "license_date": place.license_date,
        "license_cancelled_date": place.license_cancelled_date,
        "closed_date": place.closed_date,
        "temporary_business_start_date": place.temporary_business_start_date,
        "temporary_business_end_date": place.temporary_business_end_date,
        "reopen_date": place.reopen_date,
        "data_update_type": place.data_update_type,
        "telno": place.telno,
        "road_address": place.road_address,
        "lot_address": place.lot_address,
        "road_zip": place.road_zip,
        "lot_zip": place.lot_zip,
        "business_type_name": place.business_type_name,
        "subtype_name": place.subtype_name,
        "multi_use_business_place_yn": place.multi_use_business_place_yn,
        "sanitation_business_status_name": place.sanitation_business_status_name,
        "facility_total_scale": place.facility_total_scale,
        "water_supply_facility_type_name": place.water_supply_facility_type_name,
        "culture_sports_business_type_name": place.culture_sports_business_type_name,
        "sales_method_name": place.sales_method_name,
        "designation_date": place.designation_date,
        "building_ownership_type_name": place.building_ownership_type_name,
        "building_usage_name": place.building_usage_name,
        "ground_floor_count": place.ground_floor_count,
        "underground_floor_count": place.underground_floor_count,
        "total_floor_count": place.total_floor_count,
        "facility_area": place.facility_area,
        "total_area": place.total_area,
        "sickbed_count": place.sickbed_count,
        "bed_count": place.bed_count,
        "healthcare_worker_count": place.healthcare_worker_count,
        "hospital_room_count": place.hospital_room_count,
        "medical_institution_type_name": place.medical_institution_type_name,
        "medical_subject_names": place.medical_subject_names,
        "legal_dong_code": place.legal_dong_code,
        "road_name_code": place.road_name_code,
        "building_management_number": place.building_management_number,
        "road_name_emd_no": place.road_name_emd_no,
        "source_x": place.source_x,
        "source_y": place.source_y,
        "lon": place.lon,
        "lat": place.lat,
        "geom_wkt": place.point_wkt,
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


def compact_json_dumps(value: Any) -> str:
    """SQLAlchemy SQLite JSON 저장에 사용할 공백 없는 JSON serializer."""

    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def create_sqlite_schema(engine: Engine, *, load_spatialite: bool = True) -> bool:
    """SQLite 테이블과 선택적 SpatiaLite geometry 컬럼/공간 인덱스를 생성합니다.

    반환값은 현재 연결에서 SpatiaLite 확장을 사용할 수 있는지 여부입니다. 확장을
    로드하지 못해도 `geom_wkt`, `lon`, `lat` 컬럼과 일반 인덱스는 그대로 동작합니다.
    """

    spatialite_enabled = False
    with engine.begin() as connection:
        if engine.dialect.name == "sqlite":
            _set_sqlite_pragmas(connection)
        Base.metadata.create_all(connection)
        if engine.dialect.name == "sqlite":
            _ensure_sqlite_json_indexes(connection)
            if load_spatialite:
                spatialite_enabled = load_spatialite_extension(connection)
                if spatialite_enabled:
                    _ensure_spatialite_geometry(connection)
    return spatialite_enabled


def load_spatialite_extension(connection: Connection) -> bool:
    """SQLAlchemy SQLite 연결에 SpatiaLite 확장을 로드합니다."""

    raw = getattr(connection.connection, "driver_connection", None)
    if raw is None:
        raw = getattr(connection.connection, "connection", None)
    if raw is None:
        return False

    try:
        raw.enable_load_extension(True)
    except Exception:
        return False

    loaded = False
    for candidate in _spatialite_extension_candidates():
        try:
            raw.load_extension(candidate)
            loaded = True
            break
        except Exception:
            continue
    try:
        raw.enable_load_extension(False)
    except Exception:
        pass
    if not loaded:
        return False
    try:
        if not _has_table(connection, "spatial_ref_sys"):
            connection.execute(text("SELECT InitSpatialMetaData(1)"))
    except Exception:
        pass
    return True


def refresh_spatial_geometries(engine: Engine, *, batch_size: int = 100_000) -> None:
    """`lon`/`lat` 기준으로 SpatiaLite `geom` 컬럼을 배치 갱신합니다."""

    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    table_name = PlaceMaster.__tablename__
    with engine.connect() as connection:
        if not _has_column(connection, table_name, SPATIALITE_GEOMETRY_COLUMN):
            return
        if not load_spatialite_extension(connection):
            return
        row_bounds = connection.execute(
            text(
                f"""
                SELECT min(rowid), max(rowid)
                  FROM {table_name}
                 WHERE lon IS NOT NULL
                   AND lat IS NOT NULL
                   AND (
                       {SPATIALITE_GEOMETRY_COLUMN} IS NULL
                       OR geom_wkt IS NOT NULL
                   )
                """
            )
        ).one()
        connection.commit()

        min_rowid = row_bounds[0]
        max_rowid = row_bounds[1]
        if min_rowid is None or max_rowid is None:
            return

        start = int(min_rowid)
        max_rowid = int(max_rowid)
        while start <= max_rowid:
            end = start + batch_size - 1
            with connection.begin():
                connection.execute(
                    text(
                        f"""
                        UPDATE {table_name}
                           SET {SPATIALITE_GEOMETRY_COLUMN} = MakePoint(lon, lat, 4326)
                         WHERE rowid BETWEEN :start AND :end
                           AND lon IS NOT NULL
                           AND lat IS NOT NULL
                           AND (
                               {SPATIALITE_GEOMETRY_COLUMN} IS NULL
                               OR geom_wkt IS NOT NULL
                           )
                        """
                    ),
                    {"start": start, "end": end},
                )
            start = end + 1


def upsert_place(
    session: Session,
    record: LocalDataRecord | PlaceRecord,
    *,
    commit: bool = False,
) -> uuid.UUID:
    """단일 인허가 레코드를 `(service_slug, mng_no)` 기준으로 UPSERT합니다."""

    place = record if isinstance(record, PlaceRecord) else record_to_place_record(record)
    place_id = bulk_upsert_places(session, [place])[0]
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

    count = len(bulk_upsert_places(session, records))
    if commit:
        session.commit()
    return count


def bulk_upsert_places(
    session: Session,
    records: Iterable[LocalDataRecord | PlaceRecord],
) -> list[uuid.UUID]:
    """레코드 묶음을 SQLite UPSERT하고 `place_id` 목록을 반환합니다."""

    places = [
        record if isinstance(record, PlaceRecord) else record_to_place_record(record)
        for record in records
    ]
    deduped_places = _dedupe_places(places)
    if not deduped_places:
        return []

    master_rows = [
        place_master_values(place, place_id=_stable_place_id(place))
        for place in deduped_places
    ]
    master_insert = sqlite_insert(cast(Any, PlaceMaster.__table__))
    master_statement = master_insert.on_conflict_do_update(
        index_elements=[PlaceMaster.service_slug, PlaceMaster.mng_no],
        set_=_excluded_update_values(
            master_insert,
            master_rows[0],
            skip={"place_id", "service_slug", "mng_no", "created_at"},
        ),
    )
    session.execute(master_statement, master_rows)
    place_ids_by_key = _fetch_place_ids(session, deduped_places)

    detail_rows = [
        place_detail_values(place, place_ids_by_key[(place.service_slug, place.mng_no or "")])
        for place in deduped_places
    ]
    detail_insert = sqlite_insert(cast(Any, PlaceDetail.__table__))
    detail_statement = detail_insert.on_conflict_do_update(
        index_elements=[PlaceDetail.place_id],
        set_=_excluded_update_values(
            detail_insert,
            detail_rows[0],
            skip={"place_id"},
        ),
    )
    session.execute(detail_statement, detail_rows)
    return [place_ids_by_key[(place.service_slug, place.mng_no or "")] for place in deduped_places]


def _stable_place_id(place: PlaceRecord) -> uuid.UUID:
    return uuid.uuid5(PLACE_ID_NAMESPACE, f"{place.service_slug}\x1f{place.mng_no or ''}")


def _fetch_place_ids(
    session: Session,
    places: Sequence[PlaceRecord],
) -> dict[tuple[str, str], uuid.UUID]:
    keys = [(place.service_slug, place.mng_no or "") for place in places]
    rows = session.execute(
        select(PlaceMaster.service_slug, PlaceMaster.mng_no, PlaceMaster.place_id).where(
            tuple_(PlaceMaster.service_slug, PlaceMaster.mng_no).in_(keys)
        )
    ).all()
    return {
        (str(row.service_slug), str(row.mng_no)): cast(uuid.UUID, row.place_id)
        for row in rows
    }


def _excluded_update_values(
    insert_statement: Any,
    values: Mapping[str, Any],
    *,
    skip: set[str],
) -> dict[str, Any]:
    update_values = {
        key: getattr(insert_statement.excluded, key)
        for key in values
        if key not in skip
    }
    if "updated_at" not in update_values:
        update_values["updated_at"] = func.current_timestamp()
    return update_values


def _set_sqlite_pragmas(connection: Connection) -> None:
    for sql in (
        "PRAGMA foreign_keys = ON",
        "PRAGMA journal_mode = WAL",
        "PRAGMA synchronous = NORMAL",
        "PRAGMA temp_store = MEMORY",
        "PRAGMA cache_size = -200000",
    ):
        try:
            connection.execute(text(sql))
        except Exception:
            continue


def _ensure_sqlite_json_indexes(connection: Connection) -> None:
    for sql in (
        """
        CREATE INDEX IF NOT EXISTS ix_mois_place_detail_specific_valid
        ON mois_place_detail(json_valid(specific_data))
        """,
    ):
        connection.execute(text(sql))


def _ensure_spatialite_geometry(connection: Connection) -> None:
    _add_geometry_column(connection, PlaceMaster.__tablename__, SPATIALITE_GEOMETRY_COLUMN)
    try:
        connection.execute(
            text(f"SELECT CreateSpatialIndex('{PlaceMaster.__tablename__}', 'geom')")
        )
    except Exception:
        pass


def _add_geometry_column(connection: Connection, table_name: str, column_name: str) -> None:
    if _has_column(connection, table_name, column_name):
        return
    connection.execute(
        text("SELECT AddGeometryColumn(:table_name, :column_name, 4326, 'POINT', 'XY')"),
        {"table_name": table_name, "column_name": column_name},
    )


def _has_column(connection: Connection, table_name: str, column_name: str) -> bool:
    return bool(
        connection.execute(
            text(f"SELECT 1 FROM pragma_table_info('{table_name}') WHERE name = :name"),
            {"name": column_name},
        ).first()
    )


def _has_table(connection: Connection, table_name: str) -> bool:
    return bool(
        connection.execute(
            text(
                """
                SELECT 1
                  FROM sqlite_master
                 WHERE type = 'table'
                   AND name = :name
                """
            ),
            {"name": table_name},
        ).first()
    )


def _spatialite_extension_candidates() -> Sequence[str]:
    candidates: list[str] = []
    for env_name in ("MOIS_SPATIALITE_PATH", "SPATIALITE_PATH"):
        value = os.getenv(env_name)
        if not value:
            continue
        path = Path(value)
        if path.is_dir():
            _add_dll_directory(path)
            candidates.append(str(path / "mod_spatialite.dll"))
        else:
            _add_dll_directory(path.parent)
            candidates.append(str(path))
    for env_name in ("MOIS_SPATIALITE_DIR", "SPATIALITE_DIR", "PROJ_LIB"):
        value = os.getenv(env_name)
        if value:
            _add_dll_directory(Path(value))
    candidates.extend(("mod_spatialite", "mod_spatialite.dll", "libspatialite"))
    return tuple(dict.fromkeys(candidates))


def _add_dll_directory(path: Path) -> None:
    if not path.exists() or not hasattr(os, "add_dll_directory"):
        return
    try:
        os.add_dll_directory(str(path))
    except OSError:
        pass


def _dedupe_places(places: Iterable[PlaceRecord]) -> list[PlaceRecord]:
    deduped: dict[tuple[str, str], PlaceRecord] = {}
    for place in places:
        deduped[(place.service_slug, place.mng_no or "")] = place
    return list(deduped.values())


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


def _int_value(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if value is None:
        return None
    text_value = str(value).strip().replace(",", "")
    if not text_value:
        return None
    try:
        return int(text_value)
    except ValueError:
        return None


def _record_management_key(record: LocalDataRecord) -> str:
    if record.management_number:
        return record.management_number
    payload = {
        "service_slug": record.service_slug,
        "category": record.category,
        "title": record.title,
        "raw": dict(record.raw),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:32]
    return f"missing-mng-no-{digest}"
