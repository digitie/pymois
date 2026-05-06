# 지방행정 인허가정보 구현 메모

이 문서는 `pymois`가 행정안전부 지방행정 인허가정보를 어떤 규칙으로 구현하는지 정리합니다. 사용자용 요약은 `README.md`, 전체 목록은 `docs/api-list.md`와 `docs/response-fields.md`를 봅니다.

## 출처

- 공공데이터포털 공지 `NOTICE_0000000004566`, 등록일 2026-03-24
- 붙임1: API 호출 예시
- 붙임2: OpenAPI 호출 URL 목록
- 붙임3: 응답변수 매핑테이블, 2026-04-07 수정본
- localdata 파일 다운로드 페이지: `https://file.localdata.go.kr/file/hospitals/info`

## OpenAPI 호출 규칙

모든 업종은 같은 호출 형태를 사용합니다.

```text
http://apis.data.go.kr/1741000/{slug}/info
http://apis.data.go.kr/1741000/{slug}/history
```

기본 파라미터:

- `serviceKey`: 공공데이터포털 인증키
- `pageNo`: 1부터 시작
- `numOfRows`: 최대 100

조건 파라미터는 붙임1의 형식을 그대로 사용합니다.

```text
cond[DAT_UPDT_PNT::GTE]=20260301000000
cond[BASE_DATE::EQ]=20260101
cond[OPN_ATMY_GRP_CD::EQ]=3000000
```

`MoisClient.request()`는 `conditions={"DAT_UPDT_PNT": ("GTE", "...")}` 또는 `Condition("DAT_UPDT_PNT", "GTE", "...")`를 받아 위 파라미터로 변환합니다.

## 이력조회 규칙

이력조회는 `{slug}/history`를 호출합니다. 붙임1의 특정 시점 이력조회 예시는 다음 조건 조합을 사용합니다.

- `BASE_DATE::EQ`: 데이터 기준일자
- `OPN_ATMY_GRP_CD::EQ`: 개방자치단체코드

## 증분조회 규칙

붙임1은 변동분 조회에 `DAT_UPDT_PNT::GTE`를 사용합니다. 단, 이 값은 원천데이터 수정뿐 아니라 개방데이터 보강 정보의 수정도 포함합니다. 원천데이터의 수정 시점 기준으로만 조회하려면 `LAST_MDFCN_PNT::GTE`를 사용합니다.

`pymois`는 이를 위해 다음 편의 메서드를 제공합니다.

```python
client.iter_updated("hospitals", "20260505000000")
client.iter_updated("hospitals", "20260505000000", source_modified=True)
client.get_updated("hospitals", "20260505")
```

특정 기준일자의 이력 데이터는 다음처럼 호출합니다.

```python
client.iter_history_at("hospitals", "20260101", org_code="3000000")
client.get_history_at("hospitals", "20260101", org_code="3000000")
```

운영 배치에서는 `(service_slug, MNG_NO)`를 UPSERT 키로 사용하고, 폐업/취소 상태는 물리 삭제가 아니라 soft delete 상태 갱신으로 처리하는 것을 권장합니다.

## 파일 다운로드 규칙

localdata 페이지의 다운로드 버튼은 다음 흐름을 사용합니다.

1. 업종 안내 페이지 GET으로 세션 쿠키를 받습니다.
2. `/file/validate/download-count`를 호출해 다운로드 제한 상태를 확인합니다.
3. `/file/download/{slug}/info`를 iframe으로 호출합니다.
4. 지역별 다운로드는 `orgCode` 쿼리 파라미터를 추가합니다.

`LocalDataFileClient`는 이 흐름을 그대로 구현합니다.

## 파일 로드 변환 규칙

localdata 파일은 CP949 CSV입니다. 로더는 다음 변환을 수행합니다.

- 빈 문자열과 공백은 `None`
- `*_YMD` 및 한글명 `일자` 필드는 `datetime.date`
- `*_PNT` 및 한글명 `시점` 필드는 KST timezone-aware `datetime.datetime`
- 붙임3 유형이 `NUMBER`인 필드는 `int` 또는 `float`
- `좌표정보(X/Y)`는 EPSG:5174 float로 보존
- EPSG:5174 좌표가 있으면 WGS84 `lon`, `lat`를 계산해 `Coordinate`와 `WGS84_LON`, `WGS84_LAT`로 추가

## 카탈로그 생성

`pymois/catalog.py`는 공식 첨부자료와 localdata 카탈로그를 바탕으로 생성된 정적 데이터입니다.

- `OPENAPI_SERVICES`: 195개 업종
- `OPENAPI_ENDPOINTS`: 조회 195개 + 이력조회 195개
- `FILE_DOWNLOADS`: 인허가정보 195개 + 생활편의정보 13개
- `RESPONSE_FIELDS`: 응답변수 매핑 1,011행

문서 목록은 `tools/generate_docs.py`로 다시 만들 수 있습니다.

## 여행 플래너 활용 설계

사용자가 제공한 `행안부 인허가 정보 API 활용 방안.pdf`는 인허가/생활편의 데이터를 여행 플래너의 POI, 안전 경로, 장기 체류 인프라 분석에 활용하는 방안을 제안합니다. 핵심 설계는 다음 문서에 반영했습니다.

- [여행 플래너 활용 아키텍처](docs/travel-planner-architecture.md)
- [반복 실수 방지](docs/repeated-mistakes.md)

특히 단일 flat table 대신 공통 검색 필드는 `tb_place_master`, 업종별 특수 필드와 이력은 JSONB 기반 `tb_place_detail`에 저장하는 하이브리드 구조를 권장합니다.
