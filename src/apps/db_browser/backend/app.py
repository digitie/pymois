"""mois SQLite/SpatiaLite DB를 조회하는 FastAPI 백엔드."""

from __future__ import annotations

import os
import uuid
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import case, create_engine, func, or_, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from mois import (
    PlaceDetail,
    PlaceMaster,
    compact_json_dumps,
    create_sqlite_schema,
    list_file_downloads,
    list_openapi_services,
)

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


class DatabaseNotConfiguredError(RuntimeError):
    """SQLite DB 경로가 설정되지 않았거나 저장소가 없는 경우."""


def create_app(
    *,
    database_path: str | os.PathLike[str] | None = None,
    repository: Any | None = None,
    frontend_dist: str | os.PathLike[str] | None = None,
) -> FastAPI:
    """FastAPI 앱을 생성합니다.

    `repository`는 테스트에서 가짜 저장소를 주입할 때 사용합니다.
    운영/개발 실행에서는 `MOIS_SQLITE_PATH` 또는 `database_path`를 사용합니다.
    """

    app = FastAPI(
        title="mois DB 브라우저",
        description="행정안전부 인허가정보 SQLite/SpatiaLite 적재 결과를 조회합니다.",
        version="0.1.0",
    )
    _configure_cors(app)
    repo = repository or _repository_from_database_path(database_path)

    def get_repository() -> Any:
        if repo is None:
            raise DatabaseNotConfiguredError
        return repo

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        configured = repo is not None
        return {
            "ok": True,
            "databaseConfigured": configured,
            "spatialiteEnabled": bool(getattr(repo, "spatialite_enabled", False)),
        }

    @app.get("/api/stats")
    def stats() -> dict[str, Any]:
        try:
            return get_repository().stats()
        except DatabaseNotConfiguredError as exc:
            raise _db_not_configured() from exc

    @app.get("/api/services")
    def services() -> dict[str, Any]:
        try:
            return {"items": _with_service_application_urls(get_repository().services())}
        except DatabaseNotConfiguredError as exc:
            raise _db_not_configured() from exc

    @app.get("/api/places")
    def places(
        q: Annotated[
            str | None,
            Query(description="사업장명, 주소, 관리번호 검색어"),
        ] = None,
        service_slug: Annotated[str | None, Query()] = None,
        category: Annotated[str | None, Query()] = None,
        is_open: Annotated[bool | None, Query()] = None,
        detail_status_code: Annotated[str | None, Query()] = None,
        business_type_name: Annotated[str | None, Query()] = None,
        subtype_name: Annotated[str | None, Query()] = None,
        sales_method_name: Annotated[str | None, Query()] = None,
        limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
        offset: Annotated[int, Query(ge=0)] = 0,
    ) -> dict[str, Any]:
        try:
            return get_repository().places(
                q=q,
                service_slug=service_slug,
                category=category,
                is_open=is_open,
                detail_status_code=detail_status_code,
                business_type_name=business_type_name,
                subtype_name=subtype_name,
                sales_method_name=sales_method_name,
                limit=limit,
                offset=offset,
            )
        except DatabaseNotConfiguredError as exc:
            raise _db_not_configured() from exc

    @app.get("/api/places/{place_id}")
    def place_detail(place_id: str) -> dict[str, Any]:
        try:
            detail = get_repository().place_detail(place_id)
        except DatabaseNotConfiguredError as exc:
            raise _db_not_configured() from exc
        if detail is None:
            raise HTTPException(status_code=404, detail="인허가 레코드를 찾을 수 없습니다")
        return detail

    dist = Path(frontend_dist) if frontend_dist else _default_frontend_dist()
    if dist.exists():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
    return app


class SQLAlchemyPlaceRepository:
    """SQLAlchemy 세션으로 mois 적재 테이블을 조회합니다."""

    def __init__(self, engine: Engine, *, spatialite_enabled: bool = False) -> None:
        self._session_factory: Callable[[], Session] = sessionmaker(bind=engine)
        self._catalog = {download.slug: download for download in list_file_downloads()}
        self.spatialite_enabled = spatialite_enabled

    def stats(self) -> dict[str, Any]:
        with self._session_factory() as session:
            total = _scalar_int(session, select(func.count()).select_from(PlaceMaster))
            open_count = _scalar_int(
                session,
                select(func.count()).select_from(PlaceMaster).where(PlaceMaster.is_open.is_(True)),
            )
            with_coordinates = _scalar_int(
                session,
                select(func.count())
                .select_from(PlaceMaster)
                .where(PlaceMaster.lon.is_not(None), PlaceMaster.lat.is_not(None)),
            )
            service_count = _scalar_int(
                session,
                select(func.count(func.distinct(PlaceMaster.service_slug))),
            )
            category_rows = session.execute(
                select(PlaceMaster.category, func.count())
                .group_by(PlaceMaster.category)
                .order_by(func.count().desc())
            ).all()
            service_rows = session.execute(
                select(PlaceMaster.service_slug, func.count())
                .group_by(PlaceMaster.service_slug)
                .order_by(func.count().desc())
                .limit(12)
            ).all()
        return {
            "total": total,
            "open": open_count,
            "closedOrUnknown": max(total - open_count, 0),
            "withCoordinates": with_coordinates,
            "serviceCount": service_count,
            "categories": [
                {"category": category or "미분류", "count": int(count)}
                for category, count in category_rows
            ],
            "topServices": [
                self._service_count_item(str(slug), int(count)) for slug, count in service_rows
            ],
        }

    def services(self) -> list[dict[str, Any]]:
        open_case = case((PlaceMaster.is_open.is_(True), 1), else_=0)
        with self._session_factory() as session:
            rows = session.execute(
                select(
                    PlaceMaster.service_slug,
                    PlaceMaster.category,
                    PlaceMaster.title,
                    PlaceMaster.domain_category,
                    func.count(PlaceMaster.place_id),
                    func.sum(open_case),
                )
                .group_by(
                    PlaceMaster.service_slug,
                    PlaceMaster.category,
                    PlaceMaster.title,
                    PlaceMaster.domain_category,
                )
                .order_by(PlaceMaster.category, PlaceMaster.title)
            ).all()
        return [
            self._service_item(
                service_slug=str(slug),
                category=_optional_str(category),
                title=_optional_str(title),
                domain_category=_optional_str(domain_category),
                total=int(total),
                open_count=int(open_count or 0),
            )
            for slug, category, title, domain_category, total, open_count in rows
        ]

    def places(
        self,
        *,
        q: str | None,
        service_slug: str | None,
        category: str | None,
        is_open: bool | None,
        detail_status_code: str | None,
        business_type_name: str | None,
        subtype_name: str | None,
        sales_method_name: str | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        filters = _place_filters(
            q=q,
            service_slug=service_slug,
            category=category,
            is_open=is_open,
            detail_status_code=detail_status_code,
            business_type_name=business_type_name,
            subtype_name=subtype_name,
            sales_method_name=sales_method_name,
        )
        with self._session_factory() as session:
            total = _scalar_int(
                session,
                select(func.count()).select_from(PlaceMaster).where(*filters),
            )
            rows = session.scalars(
                select(PlaceMaster)
                .where(*filters)
                .order_by(PlaceMaster.updated_at.desc(), PlaceMaster.place_name)
                .limit(limit)
                .offset(offset)
            ).all()
        return {
            "items": [_place_summary(row) for row in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def place_detail(self, place_id: str) -> dict[str, Any] | None:
        try:
            actual_place_id = uuid.UUID(place_id)
        except ValueError:
            return None
        with self._session_factory() as session:
            master = session.get(PlaceMaster, actual_place_id)
            if master is None:
                return None
            detail = session.get(PlaceDetail, actual_place_id)
        payload = _place_summary(master)
        payload["detail"] = {
            "specificData": detail.specific_data if detail else {},
            "recordData": _record_data(master, detail),
            "rawData": detail.raw_data if detail else {},
        }
        return payload

    def _service_count_item(self, slug: str, count: int) -> dict[str, Any]:
        meta = self._catalog.get(slug)
        return {
            "serviceSlug": slug,
            "name": meta.name if meta else slug,
            "category": meta.category if meta else None,
            "count": count,
        }

    def _service_item(
        self,
        *,
        service_slug: str,
        category: str | None,
        title: str | None,
        domain_category: str | None,
        total: int,
        open_count: int,
    ) -> dict[str, Any]:
        meta = self._catalog.get(service_slug)
        return {
            "serviceSlug": service_slug,
            "category": category or (meta.category if meta else None),
            "name": meta.name if meta else _name_from_title(title, service_slug),
            "title": title,
            "domainCategory": domain_category,
            "total": total,
            "open": open_count,
            "downloadFunction": f"files.iter_{service_slug}()",
        }


def _repository_from_database_path(
    database_path: str | os.PathLike[str] | None,
) -> SQLAlchemyPlaceRepository | None:
    raw_path = database_path or os.getenv("MOIS_SQLITE_PATH")
    if not raw_path:
        return None
    actual_path = Path(raw_path)
    actual_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{actual_path.resolve().as_posix()}"
    engine = create_engine(url, pool_pre_ping=True, json_serializer=compact_json_dumps)
    spatialite_enabled = create_sqlite_schema(engine)
    return SQLAlchemyPlaceRepository(engine, spatialite_enabled=spatialite_enabled)


def _with_service_application_urls(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    catalog = {service.slug: service for service in list_openapi_services()}
    enriched: list[dict[str, Any]] = []
    for item in items:
        service = catalog.get(str(item.get("serviceSlug") or ""))
        enriched_item = dict(item)
        enriched_item["applicationUrl"] = service.application_url if service else None
        enriched.append(enriched_item)
    return enriched


def _place_filters(
    *,
    q: str | None,
    service_slug: str | None,
    category: str | None,
    is_open: bool | None,
    detail_status_code: str | None,
    business_type_name: str | None,
    subtype_name: str | None,
    sales_method_name: str | None,
) -> list[Any]:
    filters: list[Any] = []
    if service_slug:
        filters.append(PlaceMaster.service_slug == service_slug)
    if category:
        filters.append(PlaceMaster.category == category)
    if is_open is not None:
        filters.append(PlaceMaster.is_open.is_(is_open))
    if detail_status_code:
        filters.append(PlaceMaster.detail_status_code == detail_status_code)
    if business_type_name:
        filters.append(PlaceMaster.business_type_name == business_type_name)
    if subtype_name:
        filters.append(PlaceMaster.subtype_name == subtype_name)
    if sales_method_name:
        filters.append(PlaceMaster.sales_method_name == sales_method_name)
    if q:
        pattern = f"%{q.strip()}%"
        filters.append(
            or_(
                PlaceMaster.place_name.ilike(pattern),
                PlaceMaster.road_address.ilike(pattern),
                PlaceMaster.lot_address.ilike(pattern),
                PlaceMaster.mng_no.ilike(pattern),
                PlaceMaster.subtype_name.ilike(pattern),
                PlaceMaster.business_type_name.ilike(pattern),
            )
        )
    return filters


def _place_summary(place: PlaceMaster) -> dict[str, Any]:
    return {
        "placeId": str(place.place_id),
        "serviceSlug": place.service_slug,
        "mngNo": place.mng_no,
        "category": place.category,
        "title": place.title,
        "domainCategory": place.domain_category,
        "opnAuthorityCode": place.opn_authority_code,
        "placeName": place.place_name,
        "statusCode": place.status_code,
        "statusName": place.status_name,
        "detailStatusCode": place.detail_status_code,
        "detailStatusName": place.detail_status_name,
        "isOpen": place.is_open,
        "licenseDate": _json_value(place.license_date),
        "licenseCancelledDate": _json_value(place.license_cancelled_date),
        "closedDate": _json_value(place.closed_date),
        "temporaryBusinessStartDate": _json_value(place.temporary_business_start_date),
        "temporaryBusinessEndDate": _json_value(place.temporary_business_end_date),
        "reopenDate": _json_value(place.reopen_date),
        "dataUpdateType": place.data_update_type,
        "telno": place.telno,
        "roadAddress": place.road_address,
        "lotAddress": place.lot_address,
        "roadZip": place.road_zip,
        "lotZip": place.lot_zip,
        "businessTypeName": place.business_type_name,
        "subtypeName": place.subtype_name,
        "multiUseBusinessPlaceYn": place.multi_use_business_place_yn,
        "sanitationBusinessStatusName": place.sanitation_business_status_name,
        "facilityTotalScale": place.facility_total_scale,
        "waterSupplyFacilityTypeName": place.water_supply_facility_type_name,
        "cultureSportsBusinessTypeName": place.culture_sports_business_type_name,
        "salesMethodName": place.sales_method_name,
        "designationDate": _json_value(place.designation_date),
        "buildingOwnershipTypeName": place.building_ownership_type_name,
        "buildingUsageName": place.building_usage_name,
        "groundFloorCount": place.ground_floor_count,
        "undergroundFloorCount": place.underground_floor_count,
        "totalFloorCount": place.total_floor_count,
        "facilityArea": place.facility_area,
        "totalArea": place.total_area,
        "sickbedCount": place.sickbed_count,
        "bedCount": place.bed_count,
        "healthcareWorkerCount": place.healthcare_worker_count,
        "hospitalRoomCount": place.hospital_room_count,
        "medicalInstitutionTypeName": place.medical_institution_type_name,
        "medicalSubjectNames": place.medical_subject_names,
        "legalDongCode": place.legal_dong_code,
        "roadNameCode": place.road_name_code,
        "buildingManagementNumber": place.building_management_number,
        "sourceX": place.source_x,
        "sourceY": place.source_y,
        "lon": place.lon,
        "lat": place.lat,
        "dataUpdatedAt": _json_value(place.data_updated_at),
        "sourceModifiedAt": _json_value(place.source_modified_at),
        "updatedAt": _json_value(place.updated_at),
    }


def _record_data(place: PlaceMaster, detail: PlaceDetail | None) -> dict[str, Any]:
    promoted = {
        "MNG_NO": place.mng_no,
        "OPN_ATMY_GRP_CD": place.opn_authority_code,
        "LCPMT_YMD": _json_value(place.license_date),
        "LCPMT_RTRCN_YMD": _json_value(place.license_cancelled_date),
        "CLSBIZ_YMD": _json_value(place.closed_date),
        "SALS_STTS_CD": place.status_code,
        "SALS_STTS_NM": place.status_name,
        "DTL_SALS_STTS_CD": place.detail_status_code,
        "DTL_SALS_STTS_NM": place.detail_status_name,
        "BPLC_NM": place.place_name,
        "BZSTAT_SE_NM": place.business_type_name,
        "TELNO": place.telno,
        "LOTNO_ADDR": place.lot_address,
        "ROAD_NM_ADDR": place.road_address,
        "ROAD_NM_ZIP": place.road_zip,
        "LCTN_ZIP": place.lot_zip,
        "LCTN_AREA": place.total_area,
        "LAST_MDFCN_PNT": _json_value(place.source_modified_at),
        "DAT_UPDT_SE": place.data_update_type,
        "DAT_UPDT_PNT": _json_value(place.data_updated_at),
        "CRD_INFO_X": place.source_x,
        "CRD_INFO_Y": place.source_y,
        "WGS84_LON": place.lon,
        "WGS84_LAT": place.lat,
        "TCBIZ_BGNG_YMD": _json_value(place.temporary_business_start_date),
        "TCBIZ_END_YMD": _json_value(place.temporary_business_end_date),
        "ROBIZ_YMD": _json_value(place.reopen_date),
        "MLT_UTZTN_BSNSSP_YN": place.multi_use_business_place_yn,
        "SNTTN_BZSTAT_NM": place.sanitation_business_status_name,
        "FCLT_TOTAL_SCL": place.facility_total_scale,
        "WTRSPPL_FCLT_SE_NM": place.water_supply_facility_type_name,
        "CULTR_SPTS_TPBIZ_NM": place.culture_sports_business_type_name,
        "NTSL_MTH_NM": place.sales_method_name,
        "DSGN_YMD": _json_value(place.designation_date),
        "BLDG_PSN_SE_NM": place.building_ownership_type_name,
        "BLDG_USG_NM": place.building_usage_name,
        "GRND_NOFL": place.ground_floor_count,
        "UDGD_NOFL": place.underground_floor_count,
        "TOTAL_NOFL": place.total_floor_count,
        "FCAR": place.facility_area,
        "TOT_AR": place.total_area,
        "SCKBD_CNT": place.sickbed_count,
        "BED_CNT": place.bed_count,
        "HCWKR_CNT": place.healthcare_worker_count,
        "HSPTLZRM_CNT": place.hospital_room_count,
        "MDLCR_INST_BTP_NM": place.medical_institution_type_name,
        "MDEXM_SBJCT_CN_NM": place.medical_subject_names,
        "LEGAL_DONG_CD": place.legal_dong_code,
        "RN_MGT_SN": place.road_name_code,
        "BD_MGT_SN": place.building_management_number,
        "ROAD_NM_EMD_NO": place.road_name_emd_no,
    }
    compact_promoted = {key: value for key, value in promoted.items() if value is not None}
    if detail is None:
        return compact_promoted
    return {**compact_promoted, **detail.specific_data}


def _scalar_int(session: Session, statement: Any) -> int:
    return int(session.scalar(statement) or 0)


def _json_value(value: date | datetime | None) -> str | None:
    return value.isoformat() if value else None


def _optional_str(value: object) -> str | None:
    return str(value) if value is not None else None


def _name_from_title(title: str | None, fallback: str) -> str:
    if not title:
        return fallback
    return title.split("_", 1)[-1]


def _db_not_configured() -> HTTPException:
    return HTTPException(
        status_code=503,
        detail="MOIS_SQLITE_PATH가 설정되지 않았습니다.",
    )


def _configure_cors(app: FastAPI) -> None:
    origins = [
        origin.strip()
        for origin in os.getenv(
            "MOIS_WEB_CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _default_frontend_dist() -> Path:
    return Path(__file__).resolve().parents[1] / "frontend" / "dist"
