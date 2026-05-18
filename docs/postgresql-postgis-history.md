# PostgreSQL/PostGIS 과거 이력

이 문서는 2026년 5월까지 검토·구현했던 PostgreSQL/PostGIS 기반 DB 적재 설계를 과거 이력으로 보존합니다. 현행 코드는 SQLite/SpatiaLite 기반이며, 이 문서의 내용은 새 구현 지침이 아닙니다.

## 당시 설계

- 공통 검색 필드는 `mois_place_master`에 저장했습니다.
- 업종별 특수 필드와 원본 행은 `mois_place_detail`의 JSONB 컬럼에 저장했습니다.
- WGS84 좌표는 PostGIS `geometry(Point, 4326)`에 저장하고, 원본 EPSG:5174 좌표는 별도 칼럼으로 보존했습니다.
- 공간 인덱스는 GiST, JSONB 탐색 인덱스는 GIN을 검토했습니다.
- UPSERT는 `(service_slug, mng_no)` 조합을 기준으로 삼았습니다.

## 전환 사유

현재 저장소의 주요 사용 흐름은 이미 내려받은 localdata 파일을 로컬에서 재적재하고, Windows에서 바로 조회 서버를 띄우는 read-heavy 워크플로입니다. 이 성격에는 단일 파일 DB, 쉬운 백업/교체, 로컬 실행성이 더 중요합니다.

SQLite/SpatiaLite 전환 후에도 다음 원칙은 유지합니다.

- 공통 검색 필드는 마스터 테이블에 둡니다.
- 업종별 다양한 필드는 JSON으로 보존합니다.
- 반복 필터가 되는 JSON 경로는 별도 칼럼 또는 표현식 인덱스로 승격합니다.
- 원본 EPSG:5174 좌표와 WGS84 좌표를 모두 보존합니다.

## 참고

이 문서는 과거 설계 판단을 추적하기 위한 기록입니다. 현행 사용법은 `docs/database.md`, `docs/db-structure.md`, `docs/db-browser.md`를 기준으로 합니다.
