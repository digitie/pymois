# pymois

`pymois`는 행정안전부 지방행정 인허가정보를 Python에서 다루기 위한 라이브러리입니다.

공공데이터포털 공지 `[행정안전부] 지방행정 인허가정보 Open API 호출 관련 참고자료 제공 (수정)`의 붙임1, 붙임2, 붙임3을 기준으로 195개 업종의 조회/이력조회 OpenAPI를 모두 카탈로그화했고, `file.localdata.go.kr`의 인허가정보 파일 다운로드 195종도 같은 slug로 사용할 수 있게 했습니다.

## 주요 기능

- 195개 업종 OpenAPI 조회와 이력조회 호출
- 195개 업종 증분조회 편의 함수와 공공데이터포털 활용신청 링크 제공
- `cond[필드::연산자]` 조건 파라미터 지원
- API, 파일 다운로드, 응답변수 목록을 코드에서 조회
- localdata CSV 다운로드와 Python 객체 리스트 로드
- CP949 CSV, 날짜/시각, 숫자, EPSG:5174 좌표를 자동 변환
- EPSG:5174 좌표를 WGS84 `(lon, lat)`로 변환하고 좌표 값 객체 제공
- OpenAPI/파일/조건/좌표계 enum과 타입 별칭 제공
- Pydantic, SQLAlchemy 2, GeoAlchemy2 기반 PostgreSQL/PostGIS 적재 모델 제공
- 네트워크 없는 단위 테스트와 실제 호출용 live 테스트 분리 가능

## 설치

```bash
pip install pymois
```

개발 중인 저장소에서는 다음처럼 설치합니다.

```bash
pip install -e ".[dev]"
```

## OpenAPI 사용

공공데이터포털에서 지방행정 인허가정보 API 활용신청 후 받은 디코딩 서비스키를 사용합니다.

```python
from pymois import MoisClient

client = MoisClient("공공데이터포털_서비스키")

items = client.get(
    "hospitals",
    conditions={"DAT_UPDT_PNT": ("GTE", "20260301000000")},
)

for item in items:
    print(item["MNG_NO"], item.get("BPLC_NM"))
```

동적 편의 함수도 제공합니다.

```python
items = client.get_hospitals()
history = client.get_hospitals_history(
    conditions={
        "BASE_DATE": "20260101",
        "OPN_ATMY_GRP_CD": "3000000",
    }
)
```

증분 동기화와 특정 시점 이력조회는 별도 편의 메서드를 사용할 수 있습니다.

```python
from datetime import datetime
from zoneinfo import ZoneInfo

changed = client.get_updated(
    "hospitals",
    datetime(2026, 5, 5, 0, 0, 0, tzinfo=ZoneInfo("Asia/Seoul")),
)

source_changed = client.get_updated(
    "hospitals",
    "20260505000000",
    source_modified=True,
)

history_at = client.get_history_at(
    "hospitals",
    "20260101",
    org_code="3000000",
)
```

업종별 증분 편의 함수도 동적으로 제공합니다.

```python
changed = client.get_updated_hospitals("20260505000000")
source_changed = client.get_updated_hospitals(
    "20260505000000",
    source_modified=True,
)
```

환경변수도 사용할 수 있습니다.

```bash
export MOIS_SERVICE_KEY="공공데이터포털_서비스키"
```

```python
client = MoisClient.from_env()
```

## 파일 다운로드와 로드

```python
from pymois import LocalDataFileClient

files = LocalDataFileClient()
records = files.load("hospitals")

first = records[0]
print(first.business_name)
print(first.license_date)
print(first.updated_at)
print(first.coordinates.lon, first.coordinates.lat)
print(first.coordinates.wgs84_point.as_tuple())  # (lon, lat)
```

대용량 업종은 전체 목록을 만들지 않는 스트리밍 API를 사용합니다.

```python
for record in files.iter_hospitals():
    print(record.management_number, record.business_name)
```

CSV 원본의 `좌표정보(X)`, `좌표정보(Y)`는 EPSG:5174로 보존하고, `WGS84_LON`, `WGS84_LAT`와 `Coordinate` 객체를 추가합니다. 좌표 순서는 KATEC가 `(x, y)`, WGS84가 `(lon, lat)`입니다.

```python
from pymois import KatecPoint, Wgs84Point

katec = KatecPoint(first.coordinates.katec_x, first.coordinates.katec_y)
wgs84 = Wgs84Point(first.coordinates.lon, first.coordinates.lat)
```

지역별 파일은 localdata의 `orgCode`를 그대로 전달합니다.

```python
records = files.load("hospitals", org_code="3000000")  # 서울종로구
```

## DB 적재

PostgreSQL/PostGIS에 저장할 때는 공통 검색 필드를 마스터 테이블에, 업종별 특수 필드를 JSONB 상세 테이블에 분리합니다.

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from pymois import LocalDataFileClient, create_postgis_schema, upsert_places

engine = create_engine("postgresql+psycopg://user:password@localhost:5432/mois")
create_postgis_schema(engine)

records = LocalDataFileClient().load_hospitals()

with Session(engine) as session:
    upsert_places(session, records, commit=True)
```

## 목록 확인

API 종류가 많기 때문에 목록 확인 함수를 별도로 제공합니다. `application_url`은 공공데이터포털 활용신청 페이지입니다.

```python
from pymois import (
    list_file_downloads,
    list_incremental_openapi_endpoints,
    list_openapi_endpoints,
    list_openapi_services,
)

services = list_openapi_services()
incremental = list_incremental_openapi_endpoints()
history_urls = list_openapi_endpoints(kind="history")
downloads = list_file_downloads()
```

문서 목록:

- [API 및 파일 다운로드 목록](docs/api-list.md)
- [증분 OpenAPI 목록과 신청 링크](docs/incremental-openapi.md)
- [파일 다운로드와 로드 API](docs/file-downloads.md)
- [타입과 좌표 값 객체](docs/types-and-coordinates.md)
- [PostgreSQL/PostGIS DB 적재](docs/database.md)
- [응답변수 매핑표](docs/response-fields.md)
- [여행 플래너 활용 아키텍처](docs/travel-planner-architecture.md)
- [구현 메모](mois-api.md)
- [반복 실수 방지](docs/repeated-mistakes.md)
- [테스트 기준](docs/testing.md)
- [문제 해결](docs/troubleshooting.md)

## 검증

```bash
python -m pytest
python -m ruff check .
python -m mypy pymois
```

기본 테스트는 실제 API를 호출하지 않습니다. 실제 호출 테스트를 추가할 때는 `@pytest.mark.live`를 붙이고 `MOIS_SERVICE_KEY`가 있을 때만 실행되게 합니다.

## 참고 출처

- [공공데이터포털 공지 `NOTICE_0000000004566`](https://www.data.go.kr/bbs/ntc/selectNotice.do?pageIndex=1&originId=NOTICE_0000000004566&atchFileId=FILE_000000003615156&nttApiYn=Y&searchCondition2=2&searchKeyword1=%EC%9D%B8%ED%97%88%EA%B0%80)
- 붙임1. 공공데이터포털 지방행정 인허가정보 API 호출 예시.pdf
- 붙임2. 공공데이터포털 지방행정 인허가정보 API 호출 URL 목록.xlsx
- 붙임3. 지방행정 인허가정보의 제공항목(응답변수) 매핑테이블_20260407수정.xlsx
- https://file.localdata.go.kr/file/hospitals/info

## 라이선스

MIT
