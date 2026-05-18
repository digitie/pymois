# 작업 지침

이 저장소는 행정안전부 지방행정 인허가정보 OpenAPI와 localdata 파일 다운로드를 다룹니다.

## 기본 원칙

- 사용자-facing 문서는 한국어로 작성합니다.
- API/파일/응답변수 목록은 손으로 복사하지 않고 공식 자료에서 생성된 카탈로그를 기준으로 합니다.
- 외부 API 관련 작업은 다른 구현보다 먼저 wrapper/adapter/gateway 지양 원칙을 확인하고 문서/코드에 반영한 뒤 진행합니다.
- downstream이 직접 사용할 안정된 public client, typed model, enum, helper를 제공합니다.
- 단순 전달용 wrapper, 장기 호환 alias, 임시 facade를 만들지 않습니다.
- TripMate나 `python-krtour-map`에서 필요한 endpoint, pagination, cursor, exception, raw payload 계약이 부족하면 이 저장소의 public API를 먼저 안정화합니다.
- 검증된 다른 라이브러리의 구현이 더 적합하면 wrapper로 감싸지 말고 라이선스와 출처를 확인한 뒤 프로젝트 코드에 직접 반영합니다.
- 기본 테스트는 네트워크를 사용하지 않습니다.
- live 테스트는 `MOIS_SERVICE_KEY`가 있을 때만 실행되게 분리합니다.
- 인허가정보 CSV는 CP949, 좌표계는 EPSG:5174라는 전제를 잊지 않습니다.

## 변경 전 확인

- `docs/repeated-mistakes.md`를 먼저 확인합니다.
- OpenAPI 목록 변경은 `src/mois/catalog.py`, `docs/api-list.md`, `docs/response-fields.md`가 함께 갱신되어야 합니다.
- 파일 로더 변경은 좌표 변환, 날짜/시각 변환, 빈 값 보존 테스트를 함께 확인합니다.

## 검증

```bash
python -m pytest
python -m ruff check .
python -m mypy src/mois
```
