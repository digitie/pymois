# JSON 필드 컬럼 승격 검토

2026-05-18에 `artifacts/localdata`에 이미 내려받아 둔 195개 파일을 모두 스트리밍으로 다시 훑어
SQLite 적재 스키마를 검토했습니다.

## 분석 결과

- 분석 대상: 195개 localdata 파일
- 분석 행 수: 12,046,780건
- 발견 필드 수: 386개
- 파싱 실패: 0건
- 분석 산출물: `artifacts/json_field_profile.json`

기존 공통 컬럼인 관리번호, 인허가일, 영업상태, 사업장명, 주소, 전화번호, 좌표, 기관 코드 외에도 다음 필드는
JSON에만 두기에는 반복 빈도와 조회 가치가 높았습니다.

| 원천 필드 | 승격 컬럼 | 비어 있지 않은 행 | 등장 업종 수 | 판단 |
|---|---|---:|---:|---|
| `DAT_UPDT_SE` | `data_update_type` | 12,046,780 | 195 | 전체 파일의 I/U 갱신 구분 |
| `DTL_SALS_STTS_CD`, `DTL_SALS_STTS_NM` | `detail_status_code`, `detail_status_name` | 12,046,780 / 12,032,754 | 195 | 영업상태보다 세밀한 상태 필터 |
| `BZSTAT_SE_NM` | `business_type_name` | 8,778,251 | 54 | 음식/의료/생활 업종에서 반복되는 업태명 |
| `LCPMT_RTRCN_YMD` | `license_cancelled_date` | 120,266 | 121 | 인허가 취소일 분석 |
| `TCBIZ_BGNG_YMD`, `TCBIZ_END_YMD`, `ROBIZ_YMD` | 임시영업/재개일 컬럼 | 55,150 / 43,205 / 16,431 | 154 / 150 / 61 | 기간 조건 검색 |
| `MLT_UTZTN_BSNSSP_YN`, `SNTTN_BZSTAT_NM` | 위생/다중이용 컬럼 | 5,643,676 / 5,642,755 | 28 | 식품·위생 대형 업종 필터 |
| `FCLT_TOTAL_SCL`, `WTRSPPL_FCLT_SE_NM` | 시설 규모/급수시설 컬럼 | 4,932,860 / 2,288,279 | 22 | 식품·위생 시설 분석 |
| `NTSL_MTH_NM` | `sales_method_name` | 2,885,107 | 1 | 전자상거래 302만 건에서 핵심 필터 |
| `CULTR_SPTS_TPBIZ_NM` 등 | `subtype_name` | 분야별 상이 | 69+ | 문화·동물·환경 등 세부 업종명 통합 축 |
| `SCKBD_CNT`, `BED_CNT`, `HCWKR_CNT`, `HSPTLZRM_CNT` | 병상/침대/의료인력 컬럼 | 313,731 이하 | 2-5 | 의료·숙박 규모 검색 |

반면 직원 수 세부 항목, 보증금·임차금, 보험 기간, 선박/무대/조명 같은 필드는 특정 도메인 내부 의미가 강해
`specific_data` JSON에 남겼습니다. 필요하면 서비스별 분석 테이블을 별도로 두는 편이 전체 마스터 테이블을
넓히는 것보다 낫습니다.

## 반영 방식

- `mois_place_master`에 반복 조회축 컬럼을 추가했습니다.
- `mois_place_detail.record_data` 저장 컬럼은 제거했습니다.
- API의 `recordData` 응답은 마스터 컬럼과 `specific_data`를 합쳐 재구성합니다.
- `specific_data`와 `raw_data`에는 컬럼으로 승격되지 않은 필드만 저장합니다.
- SQLite JSON 저장은 공백 없는 serializer를 사용합니다.

이 구조는 SQLite 파일 크기를 줄이고, 반복 필터를 JSON 함수 대신 일반 컬럼 인덱스로 처리하게 해 Windows 로컬
운영에 더 적합합니다.
