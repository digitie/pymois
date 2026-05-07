# PostgreSQL/PostGIS DB 적재

`pymois`는 localdata CSV 또는 OpenAPI 응답을 공통 검색용 마스터 테이블과 업종별 JSONB 상세 테이블로 저장할 수 있는 SQLAlchemy 2 모델을 제공합니다. 좌표는 로더에서 EPSG:5174 원본 `(x, y)` 좌표를 WGS84 `(lon, lat)`로 변환한 뒤 PostGIS `geometry(Point, 4326)`으로 저장합니다.

## 의존성

기본 설치에 DB 적재에 필요한 패키지가 포함됩니다.

```bash
pip install pymois
```

개발 저장소에서는 다음처럼 설치합니다.

```bash
pip install -e ".[dev]"
```

사용 DB에는 PostGIS 확장이 필요합니다. `create_postgis_schema()`는 `CREATE EXTENSION IF NOT EXISTS postgis`를 먼저 실행한 뒤 테이블을 생성합니다.

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
| `license_date`, `closed_date` | 인허가일자, 폐업일자 |
| `road_address`, `lot_address`, `road_zip`, `lot_zip` | 도로명/지번 주소와 우편번호 |
| `legal_dong_code`, `road_name_code`, `building_management_number` | 외부 주소 데이터 보강용 코드 |
| `source_x`, `source_y` | 원본 EPSG:5174 좌표 |
| `lon`, `lat`, `geom` | WGS84 좌표와 PostGIS 포인트 |
| `data_updated_at`, `source_modified_at` | 데이터갱신시점, 최종수정시점 |

일부 원천 CSV에는 `관리번호(MNG_NO)`가 공백인 행이 실제로 존재합니다. 이 경우 `LocalDataRecord.management_number`는 `None`으로 보존하고, DB 적재용 `PlaceRecord.mng_no`에는 `missing-mng-no-<sha256>` 형식의 안정적인 대체 키를 생성합니다. 대체 키는 원천 업종과 원본 행 값으로 계산하므로 원본 값이 같으면 같은 키가 만들어집니다.

주요 인덱스:

```sql
create unique index uq_mois_place_master_source
    on mois_place_master (service_slug, mng_no);

create index ix_mois_place_master_geom
    on mois_place_master using gist (geom);

create index ix_mois_place_master_legal_dong
    on mois_place_master (legal_dong_code);

create index ix_mois_place_master_road_name
    on mois_place_master (road_name_code);
```

### `mois_place_detail`

공통 필드를 제외한 업종별 특수 필드, 정규화된 전체 데이터, 원본 CSV/API 행을 JSONB로 저장합니다.

| 칼럼 | 설명 |
|---|---|
| `place_id` | `mois_place_master.place_id` 외래키 |
| `specific_data` | 업종별 특수 필드 JSONB |
| `record_data` | 타입 변환된 전체 필드 JSONB |
| `raw_data` | 원본 문자열 행 JSONB |

### `mois_batch_sync_log`

증분 동기화 기준 시각과 실패 상태를 저장합니다. `DAT_UPDT_PNT` 기준 동기화와 `LAST_MDFCN_PNT` 기준 동기화를 분리하려면 `condition_field`를 함께 저장합니다.

## 기본 사용

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from pymois import LocalDataFileClient, create_postgis_schema, upsert_place

engine = create_engine("postgresql+psycopg://user:password@localhost:5432/mois")
create_postgis_schema(engine)

with Session(engine) as session:
    for record in LocalDataFileClient().iter_hospitals():
        upsert_place(session, record)
    session.commit()
```

대용량 업종은 `load_hospitals()`처럼 전체 목록을 만드는 방식보다 `iter_hospitals()`로 순회하며 배치 적재하는 방식을 권장합니다. 단일 레코드를 직접 변환할 수도 있습니다.

```python
from pymois import LocalDataFileClient, build_place_models, record_to_place_record

records = LocalDataFileClient().iter_hospitals()
place = record_to_place_record(next(records))
master, detail = build_place_models(place)

print(place.point_wkt)
print(place.wgs84_point.as_tuple())  # (lon, lat)
print(master.service_slug, master.mng_no)
print(detail.specific_data)
```

## OpenAPI 증분 적재 예시

```python
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from pymois import MoisClient

client = MoisClient.from_env()
since = datetime(2026, 5, 5, tzinfo=ZoneInfo("Asia/Seoul"))

rows = client.get_updated_hospitals(since)

# OpenAPI 응답을 바로 DB에 넣을 때는 응답 dict를 LocalDataRecord로 바꾸는 어댑터를
# 서비스 요구사항에 맞게 두는 것을 권장합니다. 파일 다운로드 경로는 이미
# LocalDataRecord를 반환하므로 `upsert_places()`에 바로 전달할 수 있습니다.
```

현재 `upsert_places()`는 `LocalDataRecord` 또는 `PlaceRecord`를 받습니다. OpenAPI 응답을 직접 적재하려면 응답 dict를 `PlaceRecord`로 변환하거나, 파일 로더와 동일한 정규화 규칙을 거치는 어댑터를 추가합니다.

## 외부 자료 연계 후보

인허가 데이터의 공통 필드만으로 법정동코드나 도로명주소코드가 항상 직접 제공되지는 않습니다. 안정적인 연계를 위해서는 주소 문자열, 좌표, 우편번호를 함께 사용해 보강하는 방식이 좋습니다.

| 연계 대상 | 공식 자료 | pymois 기준 필드 | 연계 방식 | 판단 |
|---|---|---|---|---|
| 법정동코드 | [행정안전부_행정표준코드_법정동코드](https://www.data.go.kr/data/15077871/openapi.do?recommendDataYn=Y) | `legal_dong_code`, `road_address`, `lot_address`, `lon/lat` | 이미 `ADM_CD`/`LEGAL_DONG_CD`가 있으면 직접 조인. 없으면 도로명주소 API 결과의 행정구역코드 또는 법정구역 경계 공간조인으로 보강 | 높음 |
| 도로명코드 | [도로명주소 개발자센터 API신청](https://www.juso.go.kr/addrlink/openApi/apiExprn.do?cPath=99MA) | `road_name_code`, `road_address`, `road_zip` | 도로명주소 검색 API의 `도로명코드`를 주소 기반으로 보강 | 높음 |
| 건물관리번호 | [도로명주소 개발자센터 API신청](https://www.juso.go.kr/addrlink/openApi/apiExprn.do?cPath=99MA) | `building_management_number`, `road_address`, `lot_address` | 도로명주소 검색 API의 `건물관리번호`를 주소 기반으로 보강. 동일 건물 내 여러 사업장은 `(건물관리번호, 사업장명)` 보조키 사용 | 중간~높음 |
| 도로명주소 전자지도 | [제공하는 주소](https://www.juso.go.kr/addrlink/adresInfoProvd/guidance/provdAdresInfo.do) | `geom`, `road_address` | 건물, 도로구간, 출입구, 법정구역 경계와 공간조인 | 높음 |
| 개방자치단체/기관 코드 | 행정표준코드 계열 자료 | `opn_authority_code` | 개방자치단체 단위 집계와 담당 기관 분석에 사용. 법정동코드로 직접 해석하지 않습니다 | 중간 |
| 민간 지도/POI | 카카오, 네이버, Google 등 | `place_name`, `road_address`, `lon/lat` | 상호명+주소+좌표 fuzzy matching. 영업시간/리뷰/카테고리 보강 | 중간 |

주의할 점:

- `OPN_ATMY_GRP_CD`는 개방자치단체코드이므로 법정동코드와 같은 값으로 취급하지 않습니다.
- 일반 인허가 공통 필드에는 도로명코드와 건물관리번호가 항상 들어 있지 않습니다.
- 도로명주소 API의 주소 검색 결과는 `행정구역코드`, `도로명코드`, `건물관리번호`, `우편번호`, `지번 주소`를 함께 제공하므로, 주소 보정/정제 배치를 별도로 두는 것이 좋습니다.
- 좌표 기반 공간조인은 주소 문자열이 오래되었거나 표기가 흔들리는 경우의 보조 수단으로 사용합니다.
- 도로명주소 전자지도는 좌표/도형을 포함한 자료이므로, 대량 공간조인에는 API보다 전자지도 다운로드 자료가 더 적합합니다.

## 추천 적재 흐름

1. localdata 파일을 `LocalDataFileClient.iter()` 또는 `iter_hospitals()` 같은 스트리밍 함수로 읽어 Python 타입으로 정규화합니다.
2. `record_to_place_record()`로 공통 필드를 추출합니다.
3. `road_address`, `lot_address`, `road_zip`으로 도로명주소 API 또는 주소 DB 보강 배치를 실행합니다.
4. 보강된 `ADM_CD`, `RN_MGT_SN`, `BD_MGT_SN` 값을 `legal_dong_code`, `road_name_code`, `building_management_number`에 저장합니다.
5. `upsert_places()`로 PostGIS DB에 저장합니다.
6. 분석 쿼리는 `mois_place_master.geom`의 GiST 인덱스와 JSONB GIN 인덱스를 조합합니다.

예시 공간 검색:

```sql
select place_name, road_address
from mois_place_master
where service_slug = 'hospitals'
  and is_open is true
  and ST_DWithin(
      geom::geography,
      ST_SetSRID(ST_MakePoint(126.9780, 37.5665), 4326)::geography,
      1000
  );
```
