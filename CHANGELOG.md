# 변경 이력

## 0.1.0

- 지방행정 인허가정보 OpenAPI 195개 업종과 이력조회 195개 URL 카탈로그 추가
- `MoisClient` 공통 호출, 조건 파라미터, JSON/XML 응답 파서 추가
- `get_updated`, `iter_updated`, `get_history_at`, `iter_history_at` 증분/이력 조회 편의 메서드 추가
- localdata 인허가정보 파일 다운로드 195개 카탈로그 추가
- `LocalDataFileClient` 다운로드/로드 API 추가
- CP949 CSV, 날짜/시각, 숫자, EPSG:5174 좌표를 Python 타입과 WGS84로 변환
- 여행 플래너 활용 아키텍처, DB 스키마, UPSERT 기반 증분 동기화 문서 추가
- API/파일/응답변수 목록 문서화
- 네트워크 없는 단위 테스트 추가
