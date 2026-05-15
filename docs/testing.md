# 테스트 기준

기본 테스트는 네트워크를 사용하지 않습니다. 공공데이터포털과 localdata는 인증키, 호출 제한, 파일 크기, 세션 쿠키의 영향을 받기 때문에 기본 단위 테스트에서는 가짜 세션과 fixture CSV만 사용합니다.

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
- 디버그 UI fixture replay: `tests/fixtures/**/*.json`을 공통 runner로 읽어 파싱/가공 결과 비교
- localdata CSV 로드: CP949, 날짜, KST 시각, 숫자, 좌표 변환
- 좌표 값 객체: `KatecPoint(x, y)`, `Wgs84Point(lon, lat)`, `StationCoordinates` 호환 별칭
- 동적 편의 함수: `get_hospitals()`, `get_updated_hospitals()`, `load_hospitals()` 계열
- DB 적재 모델: Pydantic 변환, SQLAlchemy 2 메타데이터, PostGIS geometry 컬럼, JSONB 상세 데이터
- 전체 인허가 다운로드/DB 준비 경로: 195개 파일 다운로드 카탈로그 전체를 가짜 세션으로 다운로드, 파싱, `PlaceRecord`, ORM 객체까지 생성

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

## 디버그 UI fixture replay

React/FastAPI 디버그 UI는 테스트 코드를 직접 생성하지 않고 fixture JSON을 저장하는 흐름을 사용합니다. 저장 위치는 기본적으로 `tests/fixtures/{function}/{case}.json`이며, 기본 테스트의 `tests/test_generated_fixtures.py`가 이 파일들을 자동으로 읽어 외부 API 호출 없이 replay합니다.

라이브러리 쪽 구조는 다음 역할로 나뉩니다.

- `mois.parser`: raw OpenAPI JSON/XML 응답을 `MoisResponse`로 파싱
- `mois.processor`: 파싱 결과를 라이브러리 반환 형태로 가공
- `mois.debug`: `DebugRun`, JSON 변환, 민감정보 마스킹
- `mois.fixtures`: 디버그 실행 결과를 pytest replay fixture로 저장

fixture에는 API key, Authorization header, access token 같은 민감정보를 저장하지 않습니다. 기본 assertion mode는 `snapshot`, `schema_only`, `required_fields`를 지원하며, 변동 필드는 `assertion.exclude_fields`로 제외합니다.

## 195개 인허가 파일 실제 다운로드 검증

`tests/test_all_license_downloads_db.py`는 기본 실행에서는 195개 전체를 네트워크 없이 검증합니다. 실제 `file.localdata.go.kr`에서 195개 인허가 파일을 모두 내려받아 확인하려면 다음처럼 명시적으로 실행합니다. live 경로는 대용량 업종을 위해 `LocalDataFileClient.iter()` 스트리밍 API를 사용하며, 진행 상황은 기본적으로 `artifacts/live_all_license_downloads_progress.txt`에 남깁니다. 범위를 나누어 여러 번 실행할 때는 `MOIS_LIVE_PROGRESS_PATH`로 진행 파일을 분리할 수 있습니다.

```powershell
$env:MOIS_RUN_ALL_DOWNLOAD_LIVE = "1"
python -m pytest tests\test_all_license_downloads_db.py -m live
```

PostGIS 적재까지 함께 확인하려면 `MOIS_DATABASE_URL`을 추가합니다.

```powershell
$env:MOIS_RUN_ALL_DOWNLOAD_LIVE = "1"
$env:MOIS_DATABASE_URL = "postgresql+psycopg://user:password@localhost:5432/mois"
python -m pytest tests\test_all_license_downloads_db.py -m live
```

이 테스트는 195개 파일을 실제로 다운로드하고, `MOIS_DATABASE_URL`이 있으면 `create_postgis_schema()` 후 레코드를 순회하며 `upsert_place()`로 적재합니다. `MOIS_DATABASE_URL`이 없을 때도 모든 레코드를 `PlaceRecord`와 ORM 객체로 변환해 DB 적재 준비 상태를 검증합니다. 실행 시간이 길고 다운로드 제한의 영향을 받을 수 있으므로 기본 테스트에서는 skip됩니다.

실제 CSV에는 관리번호가 공백인 행이 포함될 수 있습니다. 이 경우 테스트는 원본 `LocalDataRecord.management_number`를 강제로 채우지 않고, DB 적재용 `PlaceRecord.mng_no`의 대체 키 생성까지 확인합니다.

중간에 외부 요인으로 중단되면 인덱스 범위를 지정해 이어서 확인할 수 있습니다.

```powershell
$env:MOIS_RUN_ALL_DOWNLOAD_LIVE = "1"
$env:MOIS_LIVE_START_INDEX = "32"
$env:MOIS_LIVE_PROGRESS_PATH = "artifacts/live_32_195_progress.txt"
python -m pytest tests\test_all_license_downloads_db.py -m live -s
```
