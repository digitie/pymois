# 테스트 기준

기본 테스트는 네트워크를 사용하지 않습니다. 공공데이터포털과 localdata는 인증키, 호출 제한, 파일 크기, 세션 쿠키의 영향을 받기 때문에 기본 단위 테스트에서는 가짜 세션과 fixture CSV만 사용합니다.

## 기본 실행

```bash
python -m pytest
python -m ruff check .
python -m mypy pymois
```

## 테스트 범위

- 카탈로그 개수: OpenAPI 195개, 조회/이력조회 URL 390개, 인허가 파일 다운로드 195개
- 응답변수 매핑: 삭제 항목 제외/포함 동작
- OpenAPI 요청 파라미터: `cond[FIELD::OP]` 생성
- 증분/이력 편의 메서드: `DAT_UPDT_PNT`, `LAST_MDFCN_PNT`, `BASE_DATE`, `OPN_ATMY_GRP_CD`
- JSON/XML 응답 파싱과 resultCode 예외 매핑
- localdata CSV 로드: CP949, 날짜, KST 시각, 숫자, 좌표 변환
- 동적 편의 함수: `get_hospitals()`, `load_hospitals()` 계열

## 실제 호출 테스트를 추가할 때

실제 API를 호출하는 테스트는 반드시 `@pytest.mark.live`를 붙입니다.

```python
import os
import pytest
from pymois import MoisClient

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
