# SQLite/SpatiaLite DB 적재

`mois`는 localdata CSV 또는 OpenAPI 응답을 공통 검색용 마스터 테이블과 업종별 JSON 상세 테이블로 저장할 수 있는 SQLAlchemy 2 모델을 제공합니다. 좌표는 EPSG:5174 원본 `(x, y)`를 보존하고, WGS84 `(lon, lat)`와 WKT를 함께 저장합니다. SpatiaLite 확장을 로드할 수 있으면 `geom` 컬럼과 공간 인덱스를 추가로 사용합니다.

## 의존성과 환경

기본 설치에 DB 적재에 필요한 패키지가 포함됩니다.

```bash
pip install python-mois-api
```

개발 저장소에서는 다음처럼 설치합니다.

```bash
pip install -e ".[dev,web]"
```

Windows에서 SpatiaLite를 사용할 때는 `mod_spatialite.dll`과 의존 DLL이 있는 폴더를 PATH에 추가합니다. 이 저장소의 로컬 검증 환경은 다음 경로를 사용합니다.

```powershell
$env:PATH = "F:\dev\spatialite\bin;$env:PATH"
$env:PROJ_LIB = "F:\dev\spatialite\bin"
```

확장을 로드하지 못해도 `geom_wkt`, `lon`, `lat`와 일반 인덱스는 그대로 동작합니다.

## 테이블 구조

### `mois_place_master`

공간 검색, 상태 필터, 주소/코드 연계에 자주 쓰는 공통 필드만 저장합니다.

| 칼럼 | 설명 |
|---|---|
| `place_id` | 내부 UUID 기본키 |
| `service_slug`, `mng_no` | 원천 업종과 관리번호. UPSERT 기준 |
| `category`, `title`, `domain_category` | 원천 분류와 여행/상권 분석용 분류 |
| `opn_authority_code` | 개방자치단체코드 |
| `place_name` | 사업장명 |
| `status_code`, `status_name`, `is_open` | 영업 상태 |
| `detail_status_code`, `detail_status_name` | 상세 영업 상태 |
| `license_date`, `license_cancelled_date`, `closed_date` | 인허가일자, 인허가취소일자, 폐업일자 |
| `temporary_business_start_date`, `temporary_business_end_date`, `reopen_date` | 임시영업 시작/종료일, 재개업일 |
| `data_update_type` | 원천 파일의 데이터 갱신 구분 |
| `road_address`, `lot_address`, `road_zip`, `lot_zip` | 도로명/지번 주소와 우편번호 |
| `business_type_name`, `subtype_name` | 업태명과 도메인별 세부 업종명 |
| `sales_method_name` | 전자상거래 등 판매 방식 |
| `facility_total_scale`, `total_area`, `facility_area` | 반복 등장하는 시설 규모/면적 |
| `sickbed_count`, `bed_count`, `healthcare_worker_count`, `hospital_room_count` | 의료·숙박 규모 필드 |
| `legal_dong_code`, `road_name_code`, `building_management_number` | 외부 주소 데이터 보강용 코드 |
| `source_x`, `source_y` | 원본 EPSG:5174 좌표 |
| `lon`, `lat`, `geom_wkt` | WGS84 좌표와 WKT 포인트 |
| `geom` | SpatiaLite가 활성화된 경우 추가되는 WGS84 포인트 |
| `data_updated_at`, `source_modified_at` | 데이터갱신시점, 최종수정시점 |

일부 원천 CSV에는 `관리번호(MNG_NO)`가 공백인 행이 실제로 존재합니다. 이 경우 `LocalDataRecord.management_number`는 `None`으로 보존하고, DB 적재용 `PlaceRecord.mng_no`에는 `missing-mng-no-<sha256>` 형식의 안정적인 대체 키를 생성합니다.

주요 인덱스:

```sql
create unique index uq_mois_place_master_source
    on mois_place_master (service_slug, mng_no);

create index ix_mois_place_master_lon_lat
    on mois_place_master (lon, lat);

create index ix_mois_place_master_legal_dong
    on mois_place_master (legal_dong_code);

create index ix_mois_place_master_detail_status
    on mois_place_master (service_slug, detail_status_code);

create index ix_mois_place_master_subtype
    on mois_place_master (service_slug, subtype_name);
```

SpatiaLite가 활성화되면 `CreateSpatialIndex('mois_place_master', 'geom')`으로 공간 인덱스를 만듭니다.

### `mois_place_detail`

컬럼으로 승격하지 않은 업종별 특수 필드와 원본 CSV/API 필드만 SQLite JSON으로 저장합니다.
API의 `recordData` 응답은 마스터 컬럼과 `specific_data`를 합쳐 재구성합니다.

| 칼럼 | 설명 |
|---|---|
| `place_id` | `mois_place_master.place_id` 외래키 |
| `specific_data` | 컬럼으로 승격하지 않은 업종별 특수 필드 JSON |
| `raw_data` | 컬럼으로 승격하지 않은 원본 문자열 필드 JSON |

SQLite JSON1 함수로 JSON 검색과 필터링을 할 수 있습니다.

```sql
select m.place_name, m.sickbed_count, d.specific_data
from mois_place_master m
join mois_place_detail d on d.place_id = m.place_id
where m.sickbed_count >= 50;
```

반복 필터가 되는 JSON 경로는 마스터 컬럼 승격을 우선 검토합니다. 2026-05-18 기준 195개 파일
12,046,780건을 다시 훑어 승격한 필드는 [JSON 필드 컬럼 승격 검토](json-field-promotion.md)에 정리했습니다.

```sql
create index ix_detail_bed_count
on mois_place_detail(json_extract(specific_data, '$.SERVICE_ONLY_FIELD'));
```

### `mois_batch_sync_log`

증분 동기화 기준 시각과 실패 상태를 저장합니다. `DAT_UPDT_PNT` 기준 동기화와 `LAST_MDFCN_PNT` 기준 동기화를 분리하려면 `condition_field`를 함께 저장합니다.

## 기본 사용

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from mois import LocalDataFileClient, create_sqlite_schema, upsert_place

engine = create_engine("sqlite:///artifacts/mois.sqlite")
create_sqlite_schema(engine)

with Session(engine) as session:
    for record in LocalDataFileClient().iter_hospitals():
        upsert_place(session, record)
    session.commit()
```

대용량 업종은 `load_hospitals()`처럼 전체 목록을 만드는 방식보다 `iter_hospitals()`로 순회하며 배치 적재하는 방식을 권장합니다. 전체 파일 적재는 운영 스크립트를 사용합니다.

```powershell
$env:MOIS_SQLITE_PATH = "F:\dev\pykrmois\artifacts\mois.sqlite"
python -m tools.load_all_localdata_to_sqlite --output-dir artifacts/localdata --replace-slug
```

## 외부 자료 연계 후보

인허가 데이터의 공통 필드만으로 법정동코드나 도로명주소코드가 항상 직접 제공되지는 않습니다. 안정적인 연계를 위해서는 주소 문자열, 좌표, 우편번호를 함께 사용해 보강하는 방식이 좋습니다.

| 연계 대상 | 공식 자료 | mois 기준 필드 | 연계 방식 |
|---|---|---|---|
| 법정동코드 | 행정표준코드 계열 | `legal_dong_code`, `road_address`, `lot_address`, `lon/lat` | 원본 코드 우선, 없으면 주소 DB 또는 법정구역 공간조인 |
| 도로명코드 | 도로명주소 개발자센터 | `road_name_code`, `road_address`, `road_zip` | 도로명주소 검색 결과로 보강 |
| 건물관리번호 | 도로명주소 개발자센터 | `building_management_number`, `road_address`, `lot_address` | 주소 기반 보강, 동일 건물 내 여러 사업장은 사업장명 보조 |
| 개방자치단체/기관 코드 | 행정표준코드 계열 | `opn_authority_code` | 개방자치단체 단위 집계와 담당 기관 분석 |

주의할 점:

- `OPN_ATMY_GRP_CD`는 개방자치단체코드이므로 법정동코드와 같은 값으로 취급하지 않습니다.
- 일반 인허가 공통 필드에는 도로명코드와 건물관리번호가 항상 들어 있지 않습니다.
- 좌표 기반 공간조인은 주소 문자열이 오래되었거나 표기가 흔들리는 경우의 보조 수단으로 사용합니다.

## 추천 적재 흐름

1. localdata 파일을 `LocalDataFileClient.iter()` 또는 업종별 스트리밍 함수로 읽습니다.
2. `record_to_place_record()`로 공통 필드를 추출합니다.
3. 필요하면 주소 DB로 `legal_dong_code`, `road_name_code`, `building_management_number`를 보강합니다.
4. `upsert_places()` 또는 배치 적재 CLI로 SQLite DB에 저장합니다.
5. SpatiaLite가 활성화된 환경에서는 `refresh_spatial_geometries()`로 `geom` 컬럼을 갱신합니다.
6. 반복 검색 필드는 마스터 컬럼 또는 JSON 표현식 인덱스로 승격합니다.
