# python-mois-api

`python-mois-api`는 행정안전부 지방행정 인허가정보를 Python에서 다루기 위한 라이브러리입니다. 설치 패키지 이름은 `python-mois-api`, import 패키지 이름은 `mois`입니다.

공공데이터포털 공지 `[행정안전부] 지방행정 인허가정보 Open API 호출 관련 참고자료 제공 (수정)`의 붙임1, 붙임2, 붙임3을 기준으로 195개 업종의 조회/이력조회 OpenAPI를 카탈로그화했고, `file.localdata.go.kr`의 인허가정보 파일 다운로드 195종도 같은 slug로 사용할 수 있게 했습니다.

## 주요 기능

- 195개 업종 OpenAPI 조회와 이력조회 호출
- httpx 기반 동기/asyncio 클라이언트(`MoisClient`, `MoisClient.aio()`)
- 195개 업종 증분조회 편의 함수와 공공데이터포털 활용신청 링크 제공
- `cond[필드::연산자]` 조건 파라미터 지원
- API, 파일 다운로드, 응답변수 목록을 코드에서 조회
- localdata CSV 다운로드와 Python 객체 스트리밍 로드
- CP949 CSV, 날짜/시각, 숫자, EPSG:5174 좌표 자동 변환
- EPSG:5174 좌표를 WGS84 `(lon, lat)`로 변환하고 좌표 값 객체 제공
- SQLite/SpatiaLite 기반 로컬 DB 적재 모델과 DB 브라우저 서버 제공
- 디버그 fixture JSON을 외부 호출 없이 replay하는 pytest runner 구조 제공
- 네트워크 없는 단위 테스트와 실제 호출용 live 테스트 분리

## 설치

```bash
pip install python-mois-api
```

개발 중인 저장소에서는 다음처럼 설치합니다.

```bash
pip install -e ".[dev,web]"
```

## OpenAPI 사용

공공데이터포털에서 지방행정 인허가정보 API 활용신청 후 받은 디코딩 서비스키를 사용합니다.

```python
from mois import MoisClient, PROVIDER_NAME

print(PROVIDER_NAME)  # python-krmois-api

with MoisClient(api_key="공공데이터포털_서비스키") as client:
    items = client.get(
        "hospitals",
        conditions={"DAT_UPDT_PNT": ("GTE", "20260301000000")},
    )

for item in items:
    print(item["MNG_NO"], item.get("BPLC_NM"))
```

비동기 호출은 `python-krheritage-api`와 같은 형태로 `aio()`를 사용합니다.

```python
import asyncio

from mois import MoisClient


async def main():
    async with MoisClient.aio(api_key="공공데이터포털_서비스키") as client:
        items = await client.get_hospitals(num_of_rows=10)
        print(items[0].get("BPLC_NM"))


asyncio.run(main())
```

증분 동기화와 특정 시점 이력조회는 별도 편의 메서드를 사용할 수 있습니다.

```python
from datetime import datetime
from zoneinfo import ZoneInfo

with MoisClient.from_env() as client:
    changed = client.get_updated(
        "hospitals",
        datetime(2026, 5, 5, 0, 0, 0, tzinfo=ZoneInfo("Asia/Seoul")),
    )
    source_changed = client.get_updated("hospitals", "20260505000000", source_modified=True)
    history_at = client.get_history_at("hospitals", "20260101", org_code="3000000")
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
from mois import LocalDataFileClient

with LocalDataFileClient() as files:
    records = files.load("hospitals")

first = records[0]
print(first.business_name)
print(first.license_date)
print(first.updated_at)
print(first.coordinates.lon, first.coordinates.lat)
```

대용량 업종은 전체 목록을 만들지 않는 스트리밍 API를 사용합니다.

```python
with LocalDataFileClient() as files:
    for record in files.iter_hospitals():
        print(record.management_number, record.business_name)
```

파일 다운로드도 async 클라이언트를 제공합니다.

```python
import asyncio

from mois import LocalDataFileClient


async def main():
    async with LocalDataFileClient.aio() as files:
        async for record in files.iter_hospitals():
            print(record.management_number, record.business_name)
            break


asyncio.run(main())
```

CSV 원본의 `좌표정보(X)`, `좌표정보(Y)`는 EPSG:5174로 보존하고, `WGS84_LON`, `WGS84_LAT`와 `Coordinate` 객체를 추가합니다. 좌표 순서는 KATEC가 `(x, y)`, WGS84가 `(lon, lat)`입니다.

## SQLite/SpatiaLite DB 적재

공통 검색 필드와 반복 필터가 되는 JSON 필드는 `mois_place_master`에, 나머지 업종별 특수 필드는 `mois_place_detail`의 SQLite JSON 컬럼에 저장합니다. 195개 다운로드 파일 12,046,780건을 다시 훑어 상세 영업상태, 업태/세부업종, 판매 방식, 의료·숙박 규모 필드를 컬럼으로 승격했습니다.

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from mois import LocalDataFileClient, create_sqlite_schema, upsert_places

engine = create_engine("sqlite:///artifacts/mois.sqlite")
create_sqlite_schema(engine)

with LocalDataFileClient() as files:
    records = files.load_hospitals()

with Session(engine) as session:
    upsert_places(session, records, commit=True)
```

이미 내려받은 195개 파일을 모두 적재하려면 운영 스크립트를 사용합니다.

```powershell
$env:MOIS_SQLITE_PATH = "F:\dev\pykrmois\artifacts\mois.sqlite"
python -m tools.load_all_localdata_to_sqlite --output-dir artifacts/localdata --replace-slug
```

## DB 브라우저

```powershell
$env:MOIS_SQLITE_PATH = "F:\dev\pykrmois\artifacts\mois.sqlite"
$env:MOIS_WEB_PORT = "8000"
$env:PYTHONPATH = "src"
python -m apps.db_browser.backend
```

기본 API는 `http://127.0.0.1:8000/api`입니다. 프론트엔드는 `apps/db_browser/frontend`의 Vite 앱입니다.

## 문서 목록

- [API 및 파일 다운로드 목록](docs/api-list.md)
- [증분 OpenAPI 목록과 신청 링크](docs/incremental-openapi.md)
- [파일 다운로드와 로드 API](docs/file-downloads.md)
- [타입과 좌표 값 객체](docs/types-and-coordinates.md)
- [SQLite/SpatiaLite DB 적재](docs/database.md)
- [DB 구조 정리](docs/db-structure.md)
- [DB 브라우저 웹앱](docs/db-browser.md)
- [응답변수 매핑표](docs/response-fields.md)
- [관광 관련 인허가 데이터 선별 목록](docs/tourism-license-data.md)
- [여행 플래너 활용 아키텍처](docs/travel-planner-architecture.md)
- [구현 메모](mois-api.md)
- [반복 실수 방지](docs/repeated-mistakes.md)
- [테스트 기준](docs/testing.md)
- [문제 해결](docs/troubleshooting.md)

## 검증

```bash
python -m pytest
python -m ruff check .
python -m mypy src/mois
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
