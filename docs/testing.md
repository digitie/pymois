# 테스트 기준

기본 테스트는 네트워크를 사용하지 않습니다. 공공데이터포털과 localdata는 인증키, 호출 제한, 파일 크기, 세션 쿠키의 영향을 받기 때문에 기본 단위 테스트에서는 가짜 httpx transport와 fixture CSV만 사용합니다.

## 기본 실행

```bash
python -m pytest
python -m ruff check .
python -m mypy src/mois
```

## 테스트 범위

- 카탈로그 개수: OpenAPI 195개, 조회/이력조회 URL 390개, 증분조회 195개, 인허가 파일 다운로드 195개
- 공공데이터포털 활용신청 링크: 195개 업종별 `application_url` 중복/누락 방지
- 응답변수 매핑: 삭제 항목 제외/포함 동작
- OpenAPI 요청 파라미터: `cond[FIELD::OP]` 생성
- 증분/이력 편의 메서드: `DAT_UPDT_PNT`, `LAST_MDFCN_PNT`, `BASE_DATE`, `OPN_ATMY_GRP_CD`
- JSON/XML 응답 파싱과 resultCode 예외 매핑
- httpx 기반 동기/asyncio 클라이언트와 `MoisClient.aio()`, `LocalDataFileClient.aio()` 흐름
- 디버그 UI fixture replay: `tests/fixtures/**/*.json`을 공통 runner로 읽어 파싱/가공 결과 비교
- localdata CSV 로드: CP949, 날짜, KST 시각, 숫자, 좌표 변환
- 좌표 값 객체: `KatecPoint(x, y)`, `Wgs84Point(lon, lat)`, `StationCoordinates` 호환 별칭
- 동적 편의 함수: `get_hospitals()`, `get_updated_hospitals()`, `load_hospitals()` 계열
- DB 적재 모델: Pydantic 변환, SQLAlchemy 2 메타데이터, SQLite JSON 상세 데이터, WKT 좌표 저장
- 전체 인허가 다운로드/DB 준비 경로: 195개 파일 다운로드 카탈로그 전체를 가짜 transport로 다운로드, 파싱, `PlaceRecord`, ORM 객체까지 생성

## 실제 호출 테스트를 추가할 때

실제 API를 호출하는 테스트는 반드시 `@pytest.mark.live`를 붙입니다.

```python
import os
import pytest
from mois import MoisClient

@pytest.mark.live
def test_live_hospitals_first_page():
    key = os.getenv("MOIS_SERVICE_KEY")
    if not key:
        pytest.skip("MOIS_SERVICE_KEY가 없습니다")
    client = MoisClient(key)
    rows = client.get_hospitals(num_of_rows=1)
    assert isinstance(rows, list)
```

live 테스트는 CI 기본 경로에 넣지 않습니다. 호출 제한과 인증키 상태가 테스트 결과를 흔들 수 있기 때문입니다.

비동기 live 테스트도 같은 기준을 적용합니다.

```python
import asyncio
import os
import pytest
from mois import MoisClient

@pytest.mark.live
def test_live_hospitals_first_page_async():
    key = os.getenv("MOIS_SERVICE_KEY")
    if not key:
        pytest.skip("MOIS_SERVICE_KEY가 없습니다")

    async def run():
        async with MoisClient.aio(key) as client:
            rows = await client.get_hospitals(num_of_rows=1)
            assert isinstance(rows, list)

    asyncio.run(run())
```

## 디버그 UI fixture replay

React/FastAPI 디버그 UI는 테스트 코드를 직접 생성하지 않고 fixture JSON을 저장하는 흐름을 사용합니다. 저장 위치는 기본적으로 `tests/fixtures/{function}/{case}.json`이며, 기본 테스트의 `tests/test_generated_fixtures.py`가 이 파일들을 자동으로 읽어 외부 API 호출 없이 replay합니다.

fixture에는 API key, Authorization header, access token 같은 민감정보를 저장하지 않습니다. 기본 assertion mode는 `snapshot`, `schema_only`, `required_fields`를 지원하며, 변동 필드는 `assertion.exclude_fields`로 제외합니다.

## 195개 인허가 파일 실제 다운로드 검증

`tests/test_all_license_downloads_db.py`는 기본 실행에서는 195개 전체를 네트워크 없이 검증합니다. 실제 `file.localdata.go.kr`에서 195개 인허가 파일을 모두 내려받아 확인하려면 다음처럼 명시적으로 실행합니다. live 경로는 대용량 업종을 위해 `LocalDataFileClient.iter()` 스트리밍 API를 사용하며, 진행 상황은 기본적으로 `artifacts/live_all_license_downloads_progress.txt`에 남깁니다.

```powershell
$env:MOIS_RUN_ALL_DOWNLOAD_LIVE = "1"
python -m pytest tests\test_all_license_downloads_db.py -m live
```

SQLite 적재까지 함께 확인하려면 `MOIS_SQLITE_PATH`를 추가합니다.

```powershell
$env:MOIS_RUN_ALL_DOWNLOAD_LIVE = "1"
$env:MOIS_SQLITE_PATH = "F:\dev\pykrmois\artifacts\live-test.sqlite"
python -m pytest tests\test_all_license_downloads_db.py -m live
```

이 테스트는 195개 파일을 실제로 다운로드하고, `MOIS_SQLITE_PATH`가 있으면 `create_sqlite_schema()` 후 레코드를 순회하며 `upsert_place()`로 적재합니다. `MOIS_SQLITE_PATH`가 없을 때도 모든 레코드를 `PlaceRecord`와 ORM 객체로 변환해 DB 적재 준비 상태를 검증합니다. 실행 시간이 길고 다운로드 제한의 영향을 받을 수 있으므로 기본 테스트에서는 skip됩니다.

이미 내려받은 파일을 기준으로 전체 재적재를 검증할 때는 운영 스크립트를 사용합니다.

```powershell
$env:MOIS_SQLITE_PATH = "F:\dev\pykrmois\artifacts\mois.sqlite"
python -m tools.load_all_localdata_to_sqlite --output-dir artifacts/localdata --replace-slug
```

실제 CSV에는 관리번호가 공백인 행이 포함될 수 있습니다. 이 경우 테스트는 원본 `LocalDataRecord.management_number`를 강제로 채우지 않고, DB 적재용 `PlaceRecord.mng_no`의 대체 키 생성까지 확인합니다.

중간에 외부 요인으로 중단되면 인덱스 범위를 지정해 이어서 확인할 수 있습니다.

```powershell
$env:MOIS_RUN_ALL_DOWNLOAD_LIVE = "1"
$env:MOIS_LIVE_START_INDEX = "32"
$env:MOIS_LIVE_PROGRESS_PATH = "artifacts/live_32_195_progress.txt"
python -m pytest tests\test_all_license_downloads_db.py -m live -s
```
