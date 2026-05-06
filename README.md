# pymois

`pymois`는 행정안전부 지방행정 인허가정보를 Python에서 다루기 위한 라이브러리입니다.

공공데이터포털 공지 `[행정안전부] 지방행정 인허가정보 Open API 호출 관련 참고자료 제공 (수정)`의 붙임1, 붙임2, 붙임3을 기준으로 195개 업종의 조회/이력조회 OpenAPI를 모두 카탈로그화했고, `file.localdata.go.kr`의 인허가정보 파일 다운로드 195종도 같은 slug로 사용할 수 있게 했습니다.

## 주요 기능

- 195개 업종 OpenAPI 조회와 이력조회 호출
- `cond[필드::연산자]` 조건 파라미터 지원
- API, 파일 다운로드, 응답변수 목록을 코드에서 조회
- localdata CSV 다운로드와 Python 객체 리스트 로드
- CP949 CSV, 날짜/시각, 숫자, EPSG:5174 좌표를 자동 변환
- EPSG:5174 좌표를 WGS84 경도/위도로 추가 제공
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
```

CSV 원본의 `좌표정보(X)`, `좌표정보(Y)`는 EPSG:5174로 보존하고, `WGS84_LON`, `WGS84_LAT`와 `Coordinate` 객체를 추가합니다.

지역별 파일은 localdata의 `orgCode`를 그대로 전달합니다.

```python
records = files.load("hospitals", org_code="3000000")  # 서울종로구
```

## 목록 확인

API 종류가 많기 때문에 목록 확인 함수를 별도로 제공합니다.

```python
from pymois import list_openapi_services, list_openapi_endpoints, list_file_downloads

services = list_openapi_services()
history_urls = list_openapi_endpoints(kind="history")
downloads = list_file_downloads()
```

문서 목록:

- [API 및 파일 다운로드 목록](docs/api-list.md)
- [파일 다운로드와 로드 API](docs/file-downloads.md)
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

- 공공데이터포털 공지 `NOTICE_0000000004566`
- 붙임1. 공공데이터포털 지방행정 인허가정보 API 호출 예시.pdf
- 붙임2. 공공데이터포털 지방행정 인허가정보 API 호출 URL 목록.xlsx
- 붙임3. 지방행정 인허가정보의 제공항목(응답변수) 매핑테이블_20260407수정.xlsx
- https://file.localdata.go.kr/file/hospitals/info

## 라이선스

MIT
