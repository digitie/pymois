# 반복 실수 방지

이 저장소에서 다시 반복하지 말아야 할 실수를 기록합니다.

## 문서 인코딩

- PowerShell here-string으로 한국어 문서를 바로 생성하면 입력 인코딩 때문에 `??`로 깨질 수 있습니다.
- 한국어 문서는 UTF-8 파일을 `apply_patch`로 만들거나, 저장소의 UTF-8 Python 스크립트에서 생성합니다.
- 생성 문서는 `python -c "Path(...).read_text(encoding='utf-8')"`로 앞부분을 확인합니다.
- PowerShell 기본 출력 인코딩 때문에 UTF-8 문서가 깨져 보일 수 있습니다. 문서를 읽을 때는 `Get-Content -Encoding UTF8`처럼 인코딩을 명시합니다.

## 문서 작성

- 사용자-facing 문서와 Python 내부 문서(docstring, 공개 API 설명)는 한국어로 작성합니다.
- 문서의 파일 위치 정보는 절대 경로가 아니라 프로젝트 기준 상대 경로로 적습니다.

## 파일 탐색

- `rg`가 실행 권한 문제로 막히는 환경에서는 실패를 반복하지 말고 PowerShell 파일 목록 명령으로 우회합니다.
- 파일 목록은 `Get-ChildItem -Recurse -File`을 우선 사용하고, 내용 검색이 필요하면 `Select-String`을 사용합니다.

## API 목록

- OpenAPI는 업종 195개이고, 각 업종마다 `info`와 `history`가 있습니다. 총 호출 URL은 390개입니다.
- 목록을 손으로 옮기지 않습니다. `pymois/catalog.py`와 `tools/generate_docs.py`를 기준으로 관리합니다.
- 활용신청 링크는 공지 페이지의 `api-list` 링크에서 추출한 `application_url`을 사용합니다.
- 증분 OpenAPI 목록을 바꾸면 `INCREMENTAL_OPENAPI_ENDPOINTS`와 `docs/incremental-openapi.md`도 함께 갱신합니다.
- localdata 파일 다운로드는 인허가정보 195개를 기본 대상으로 합니다. 생활편의정보는 별도 kind로 남겨 둡니다.
- live 전체 다운로드 검증을 범위별로 나누어 실행하면 기본 진행 파일이 덮어써집니다. 분할 실행 때는 `MOIS_LIVE_PROGRESS_PATH`를 범위별로 다르게 지정합니다.

## 조건 파라미터

- 붙임1의 조건 형식은 `cond[FIELD::OP]=value`입니다.
- `DAT_UPDT_PNT`는 개방데이터 보강 수정도 포함합니다.
- 원천데이터 수정 시점 기준 증분조회는 `LAST_MDFCN_PNT`를 사용합니다.
- 배치 동기화에서는 마지막 성공 시각을 별도 로그 테이블에 저장하고 다음 실행의 `GTE` 조건으로 사용합니다.
- UPSERT 키는 관리번호 단독보다 `(service_slug, MNG_NO)` 조합이 안전합니다.
- 실제 CSV에는 `MNG_NO`가 공백인 행이 있으므로 원본 `management_number`는 `None`으로 보존하고, DB 적재용 `PlaceRecord.mng_no`에만 `missing-mng-no-<sha256>` 대체 키를 사용합니다.
- 폐업/취소 데이터는 삭제하지 말고 영업상태와 폐업일자를 갱신하는 soft delete로 처리합니다.

## 파일 다운로드

- localdata 다운로드 URL만 바로 호출하면 403으로 떨어질 수 있습니다.
- 안내 페이지 GET, 다운로드 제한 확인, 실제 다운로드 순서를 지켜야 합니다.
- 지역별 다운로드는 `orgCode`를 쿼리 파라미터로 붙입니다.

## CSV 로드

- localdata 파일은 UTF-8이 아니라 CP949인 경우가 기본입니다.
- 빈 문자열을 숫자 0으로 바꾸지 않습니다. 의미 없는 빈 값은 `None`입니다.
- 좌표는 원본 EPSG:5174 값을 보존하면서 WGS84를 추가합니다. 원본 좌표를 덮어쓰지 않습니다.
- 좌표 순서는 KATEC/EPSG:5174가 `(x, y)`, WGS84/EPSG:4326이 `(lon, lat)`입니다. helper 이름과 문서에서 순서를 항상 명시합니다.
- 좌표를 새로 노출할 때 float 네 개만 추가하지 말고 `KatecPoint`, `Wgs84Point`, `StationCoordinates` 값 객체를 함께 제공합니다.
- 날짜와 시각은 문자열로 방치하지 않습니다. `date`와 KST `datetime`으로 변환합니다.

## 여행 플래너 설계

- 195개 업종의 특수 칼럼을 하나의 flat table에 모두 펼치지 않습니다.
- 공간 검색과 상태 필터링에 필요한 공통 필드는 마스터 테이블로 분리합니다.
- 업종별 특수 필드와 과거 이력은 JSONB 같은 스키마리스 구조에 보관합니다.
- PostGIS 좌표는 WGS84 `geometry(Point, 4326)`로 저장하고, 원본 EPSG:5174 좌표는 별도 칼럼에 보존합니다.
- 법정동코드와 도로명코드는 공통 인허가 필드에 항상 있는 값이 아닙니다. 주소 API/전자지도/공간조인 보강값과 원본값을 구분합니다.
- PDF는 생활편의정보 14종/전체 209종을 언급하지만, 현재 파일 다운로드 카탈로그는 생활편의정보 13종/전체 208종입니다. 확인되지 않은 항목을 코드 카탈로그에 추정으로 넣지 않습니다.

## 응답변수

- 붙임3의 삭제 항목은 기본 목록에서 제외합니다.
- 삭제 항목까지 확인해야 할 때만 `list_response_fields(include_deleted=True)`를 사용합니다.
