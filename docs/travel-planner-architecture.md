# 여행 플래너 활용 아키텍처

이 문서는 `C:\Users\digit\Downloads\행안부 인허가 정보 API 활용 방안.pdf`의 내용을 바탕으로, `mois`로 수집한 행정안전부 인허가/생활편의 데이터를 여행 플래너 서비스에 적용할 때의 설계 기준을 정리합니다.

## 데이터 범위 해석

PDF는 인허가정보 195종과 생활편의정보 14종, 총 209종을 여행 플래너의 원천 데이터로 봅니다. 다만 2026년 5월 6일 현재 `https://file.localdata.go.kr/file/hospitals/info` 파일 다운로드 카탈로그에서 확인되는 항목은 인허가정보 195종과 생활편의정보 13종, 총 208종입니다.

따라서 `mois`의 현재 카탈로그는 실제 확인 가능한 파일 다운로드 목록을 우선합니다. 문서/서비스 설계에서는 다음처럼 구분합니다.

- `list_file_downloads()`: 실제 확인된 인허가정보 195종
- `list_file_downloads(kind=None)`: 실제 확인된 전체 파일 다운로드 208종
- PDF의 209종 언급: 여행 플래너 설계 범위의 목표 상태로 기록하되, 구현 카탈로그에는 확인된 항목만 포함

## 여행 도메인 분류

행정 데이터는 행정 목적의 업종 분류를 따르므로, 여행 서비스에서는 사용자 여정 기준으로 다시 묶는 것이 좋습니다.

| 여행 도메인 | 관련 데이터 예 | 활용 목적 |
|---|---|---|
| 식음료 | 일반음식점, 휴게음식점, 제과점영업, 유흥주점영업 | 식당/카페 추천, 예산 산출, 동선 내 식사 지점 배치 |
| 숙박/체류 | 관광숙박업, 숙박업, 농어촌민박업, 외국인관광도시민박업 | 여행 거점 설정, 체류 테마별 추천 |
| 문화/여가 | 관광사업자, 박물관 및 미술관, 영화상영관, 체육시설업 | 일정표 구성, 날씨/시즌별 대체 장소 추천 |
| 안전/보건 | 병원, 약국, 안전상비의약품 판매업소 | 응급 상황 대비, 가족 여행 안전성 평가 |
| 생활편의 | 공중화장실, CCTV, 민방위 대피시설, 무료와이파이 | 편의시설 검색, 야간/재난 상황 경로 가중치 |
| 장기 체류/상권 | 미용업, 통신판매업, 담배소매업, 목욕장업 | 워케이션/한 달 살기 인프라 평가, 상권 활성도 분석 |

## 권장 DB 구조

195개 업종은 공통 필드와 업종별 특수 필드가 섞여 있습니다. 모든 필드를 하나의 고정 테이블에 넣으면 대부분의 칼럼이 비거나, 업종이 늘 때마다 스키마 변경이 필요해집니다.

현재 구현은 SQLite/SpatiaLite 기반의 마스터-디테일 구조입니다.

### `mois_place_master`

검색, 필터링, 공간 인덱싱에 필요한 공통 속성만 둡니다.

| 칼럼 | 설명 |
|---|---|
| `place_id` | 내부 식별자 |
| `service_slug` | `hospitals`, `general_restaurants` 같은 mois slug |
| `mng_no` | 관리번호. 업종 내 UPSERT 기준 |
| `domain_category` | 여행 도메인 분류 |
| `place_name` | 사업장명 또는 시설명 |
| `status_code`, `status_name`, `is_open` | 영업 상태 |
| `license_date`, `closed_date` | 인허가일자, 폐업일자 |
| `detail_status_code`, `detail_status_name` | 상세 영업 상태 |
| `license_cancelled_date`, `temporary_business_start_date`, `temporary_business_end_date`, `reopen_date` | 취소/임시영업/재개업 날짜 |
| `business_type_name`, `subtype_name`, `sales_method_name` | 업태, 세부업종, 판매 방식 |
| `sickbed_count`, `bed_count`, `healthcare_worker_count`, `hospital_room_count` | 의료·숙박 규모 |
| `road_address`, `lot_address` | 도로명주소, 지번주소 |
| `source_x`, `source_y` | 원본 EPSG:5174 좌표 |
| `lon`, `lat`, `geom_wkt` | WGS84 좌표와 WKT |
| `geom` | SpatiaLite가 활성화된 경우의 공간 컬럼 |

### `mois_place_detail`

컬럼으로 승격하지 않은 업종별 특수 속성과 원본 필드를 SQLite JSON으로 저장합니다.

| 칼럼 | 설명 |
|---|---|
| `place_id` | 마스터와 1:1 |
| `specific_data` | 업종별 특수 필드 |
| `raw_data` | 컬럼으로 승격하지 않은 원본 문자열 필드 |

JSON 필드는 “보관과 상세 확인”이 기본 역할입니다. 반복 필터 조건이 되는 값은 표현식 인덱스 또는 별도 칼럼으로 승격합니다.
현재 API의 `recordData` 응답은 마스터 컬럼과 `specific_data`를 합쳐 재구성합니다. 승격 기준과 실제
195개 파일 분석 결과는 `docs/json-field-promotion.md`에 정리했습니다.

## 증분 업데이트 파이프라인

PDF의 권장 운영 방식은 일 1회 야간 배치입니다. 초 단위 스트리밍보다 안정성과 호출 제한 관리가 중요합니다.

1. `mois_batch_sync_log`에서 대상 slug의 마지막 성공 시각을 읽습니다.
2. `client.iter_updated(slug, since)`로 `DAT_UPDT_PNT::GTE` 조건을 호출합니다.
3. 원천데이터 수정 시점만 보고 싶으면 `client.iter_updated(slug, since, source_modified=True)`를 사용합니다.
4. `totalCount`, `pageNo`, `numOfRows` 기준으로 모든 페이지를 순회합니다.
5. `(service_slug, MNG_NO)` 기준으로 UPSERT합니다.
6. `SALS_STTS_CD` 또는 `SALS_STTS_NM`이 폐업/취소 계열이면 물리 삭제하지 않고 soft delete 상태로 갱신합니다.
7. 이력조회는 `client.iter_history_at(slug, base_date, org_code=...)`로 별도 적재합니다.
8. 실패한 행은 원본 payload와 예외를 로그에 격리합니다.

예시:

```python
from datetime import datetime
from zoneinfo import ZoneInfo

from mois import MoisClient

client = MoisClient.from_env()
since = datetime(2026, 5, 5, 0, 0, 0, tzinfo=ZoneInfo("Asia/Seoul"))

for row in client.iter_updated("hospitals", since):
    # (service_slug, row["MNG_NO"]) 기준 UPSERT
    ...
```

## 운영 안정성

- 공공 API 호출은 타임아웃과 호출 제한을 전제로 설계합니다.
- 실패 시 지수 백오프를 적용합니다.
- 파싱 실패 행은 전체 배치를 중단시키지 말고 로그로 분리합니다.
- `DAT_UPDT_PNT`는 좌표 보강 등 개방데이터 측 수정도 포함하므로, 원천 수정 기준 증분이 필요하면 `LAST_MDFCN_PNT`를 사용합니다.
- 관리번호는 전역 단독 PK로 단정하지 말고 `service_slug`와 함께 unique key로 잡는 것이 안전합니다.

## 서비스 고도화 아이디어

- 인허가일자와 이력 데이터를 활용해 오래 영업한 장소를 “지역 노포” 후보로 태깅합니다.
- 폐업/개업이 잦은 장소는 추천 점수에서 페널티를 줍니다.
- 야간 도보 경로는 CCTV, 민방위 대피시설, 안전비상벨 등 생활편의 데이터를 공간 가중치로 활용합니다.
- 가족 여행 경로는 병원, 약국, 공중화장실, 안전상비의약품 판매업소 접근성을 제약 조건으로 둡니다.
- 행정 데이터에는 영업시간/메뉴/리뷰가 부족하므로 민간 지도 API와 상호명+주소 기반 cross-reference를 별도 배치로 수행합니다.
