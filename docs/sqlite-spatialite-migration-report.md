# SQLite/SpatiaLite 전환 개발 문서

## 요약

이 저장소의 인허가정보 로컬 DB 계층은 SQLite/SpatiaLite 기반으로 전환했습니다. 이전 DB 구현과 운영 문서는 현행 코드와 문서에서 제거했고, 과거 설계 이력은 별도 이력 문서에만 보존합니다.

핵심 판단은 다음과 같습니다.

- 기본 운영 DB는 단일 SQLite 파일입니다.
- SpatiaLite 확장이 로드되면 `mois_place_master.geom` 공간 컬럼을 함께 사용합니다.
- 공간 컬럼 갱신은 대용량 파일에서 메모리가 커지지 않도록 rowid 범위 배치로 커밋합니다.
- SpatiaLite가 없어도 `lon`, `lat`, `geom_wkt`로 조회와 API 응답은 동작합니다.
- 반복 조회와 필터에 쓰이는 JSON 필드는 마스터 컬럼으로 승격했습니다.
- 업종별로만 드문 특수 필드는 `specific_data` JSON에 남겼습니다.
- API의 `recordData` 응답은 마스터 승격 컬럼과 `specific_data`를 합쳐 재구성합니다.

## Windows SpatiaLite 설정

Windows 개발 환경에서는 Gaia-SINS의 SpatiaLite 배포본을 사용합니다.

| 항목 | 값 |
|---|---|
| 설치 경로 | `F:\dev\spatialite\bin` |
| 확장 DLL | `mod_spatialite.dll` |
| PATH | `F:\dev\spatialite\bin`을 선행 추가 |
| PROJ_LIB | `F:\dev\spatialite\bin` |
| 확인 버전 | SpatiaLite 5.1.0, PROJ 9.2.1 |

서버나 적재 스크립트를 실행하기 전에 다음 환경을 설정합니다.

```powershell
$env:PATH = "F:\dev\spatialite\bin;$env:PATH"
$env:PROJ_LIB = "F:\dev\spatialite\bin"
$env:MOIS_SQLITE_PATH = "F:\dev\pykrmois\artifacts\mois.sqlite"
```

## 스키마 구조

`mois_place_master`는 검색과 필터에 필요한 공통 컬럼을 저장합니다. 좌표는 원본 EPSG:5174와 변환된 WGS84를 함께 보존합니다.

| 구분 | 주요 컬럼 |
|---|---|
| 식별 | `place_id`, `service_slug`, `mng_no` |
| 상태 | `status_code`, `status_name`, `detail_status_code`, `detail_status_name`, `is_open` |
| 일자 | `license_date`, `closed_date`, `data_updated_at`, `source_modified_at` |
| 주소 | `road_address`, `lot_address`, `legal_dong_code`, `road_name_code`, `building_management_number` |
| 좌표 | `source_x`, `source_y`, `lon`, `lat`, `geom_wkt`, `geom` |
| 승격 필드 | 업태, 세부업종, 판매 방식, 시설 규모, 의료기관 수치 등 |

`mois_place_detail`은 마스터 컬럼으로 승격하지 않은 필드만 저장합니다.

| 컬럼 | 의미 |
|---|---|
| `specific_data` | 컬럼으로 승격하지 않은 업종별 특수 필드 JSON |
| `raw_data` | 컬럼으로 승격하지 않은 원본 문자열 필드 JSON |

SQLite JSON1의 `json_extract()`로 JSON 조회와 표현식 인덱스 생성은 가능합니다. 다만 현재 데이터처럼 1,200만 행 규모이고 반복 필터가 명확한 경우에는 JSON 표현식 필터보다 일반 컬럼 승격이 운영상 더 단순하고 빠릅니다.

## JSON 필드 승격 결정

실제 다운로드 파일 전체를 프로파일링한 결과는 다음과 같습니다.

| 항목 | 값 |
|---|---:|
| 파일 수 | 195 |
| 행 수 | 12,046,780 |
| JSON 필드 수 | 386 |
| 프로파일 실패 | 0 |

승격한 필드는 반복 조회, 서비스 범위, 데이터 규모, 여행/지도 UI 필터 가능성을 기준으로 정했습니다.

| 원본 필드 | 승격 컬럼 | 비어 있지 않은 행 | 서비스 수 | 이유 |
|---|---|---:|---:|---|
| `DTL_SALS_STTS_CD`, `DTL_SALS_STTS_NM` | `detail_status_code`, `detail_status_name` | 12,046,780 / 12,032,754 | 195 | 세부 영업상태 필터 |
| `DAT_UPDT_SE` | `data_update_type` | 12,046,780 | 195 | 삽입/수정 구분 |
| `BZSTAT_SE_NM` | `business_type_name` | 8,778,251 | 54 | 업태 필터 |
| `SNTTN_BZSTAT_NM`, `CULTR_SPTS_TPBIZ_NM` 등 | `subtype_name` | 9,650,786 | 28 이상 | 분야별 세부업종 대표값 |
| `NTSL_MTH_NM` | `sales_method_name` | 2,885,107 | 1 | 전자상거래 판매 방식 필터 |
| `MLT_UTZTN_BSNSSP_YN` | `multi_use_business_place_yn` | 5,643,676 | 28 | 다중이용업소 여부 |
| `FCLT_TOTAL_SCL`, `WTRSPPL_FCLT_SE_NM` | 시설 규모/급수 유형 | 4,932,860 / 2,288,279 | 22 | 식품·위생 시설 필터 |
| `SCKBD_CNT`, `BED_CNT`, `HCWKR_CNT`, `HSPTLZRM_CNT` | 의료기관 수치 컬럼 | 133,495-313,731 | 2-5 | 의료기관 검색과 통계 |
| `FCAR`, `TOT_AR` | `facility_area`, `total_area` | 5,329,830 이하 | 6 이상 | 면적 조건 |

나머지 필드는 다음 조건에 해당해 JSON에 남겼습니다.

- 특정 업종에만 존재하고 반복 필터 가능성이 낮습니다.
- 설명성 텍스트나 기관명처럼 색인 요구가 아직 분명하지 않습니다.
- 유사 필드가 많아 전체 마스터 테이블 컬럼을 계속 늘리는 것보다 서비스별 분석 테이블을 따로 두는 편이 낫습니다.

## 주요 명령

전체 다운로드 파일을 새 SQLite DB로 다시 적재합니다.

```powershell
python -m tools.load_all_localdata_to_sqlite `
  --output-dir artifacts/localdata `
  --progress-path artifacts/load_all_localdata_sqlite_progress.jsonl `
  --replace-slug `
  --batch-size 10000
```

DB 브라우저 API 서버를 실행합니다.

```powershell
$env:PYTHONPATH = "src"
python -m apps.db_browser.backend
```

기본 검증은 네트워크 없이 실행합니다.

```powershell
python -m pytest
python -m ruff check .
python -m mypy src/mois
```

## 검증 결과

2026-05-18 Windows 환경에서 이미 내려받아 둔 `artifacts/localdata` 파일 전체를 새 SQLite DB로 다시 적재했습니다.

| 검증 항목 | 결과 |
|---|---|
| 전체 파일 재적재 | 195개 파일, 원천 레코드 12,046,780건 처리, 실패 0건 |
| DB 저장 결과 | `mois_place_master` 11,364,852건, `mois_place_detail` 11,364,852건, 서비스 195개 |
| 좌표 저장 결과 | `lon`/`lat` 10,432,736건, SpatiaLite `geom` 10,432,736건 |
| SpatiaLite 확인 | Windows `mod_spatialite.dll` 로드 성공, `spatialite_version()` 5.1.0 |
| promoted 컬럼 확인 | `detail_status_code` 11,364,852건, `data_update_type` 11,364,852건, `subtype_name` 9,650,786건 |
| detail JSON 확인 | `specific_data` 11,364,852건, `raw_data` 11,364,852건, 서비스별 샘플 195개 JSON 파싱 성공 |
| 서버 `/api/health` | `{"ok":true,"databaseConfigured":true,"spatialiteEnabled":true}` |
| 서버 `/api/stats` | 총 11,364,852건, 영업 4,347,656건, 좌표 10,432,736건, 서비스 195개 |
| 서버 조회 API | `/api/places`, `detail_status_code` 필터, `/api/places/{placeId}` 상세 조회 성공 |
| `python -m pytest` | 51 passed, 1 skipped |
| `python -m ruff check .` | 통과 |
| `python -m mypy src/mois` | 통과 |

원천 레코드 수와 DB 저장 건수가 다른 이유는 로더가 `(service_slug, mng_no)`를 기준으로 UPSERT하기 때문입니다. 같은 관리번호가 반복된 레코드는 최신 값으로 정리되어 마스터/상세 테이블에는 unique 장소 단위로 저장됩니다.
