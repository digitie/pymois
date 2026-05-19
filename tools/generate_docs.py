"""카탈로그 기반 한국어 목록 문서를 생성합니다."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mois.catalog import (  # noqa: E402
    FILE_DOWNLOADS,
    INCREMENTAL_OPENAPI_ENDPOINTS,
    OPENAPI_SERVICES,
    RESPONSE_FIELDS,
)

TOURISM_LICENSE_SELECTION = (
    {
        "slug": "hospitals",
        "group": "의료/안전",
        "relation": "편의",
        "priority": "상",
        "use_case": "여행 중 응급/외래 진료 거점",
    },
    {
        "slug": "clinics",
        "group": "의료/안전",
        "relation": "편의",
        "priority": "상",
        "use_case": "가벼운 질환과 지역 의원 접근성 분석",
    },
    {
        "slug": "pharmacies",
        "group": "의료/안전",
        "relation": "편의",
        "priority": "상",
        "use_case": "상비약·처방약 구매 편의",
    },
    {
        "slug": "over_the_counter_medicine_stores",
        "group": "의료/안전",
        "relation": "편의",
        "priority": "중",
        "use_case": "야간·휴일 안전상비의약품 구매 편의",
    },
    {
        "slug": "emergency_patient_transport",
        "group": "의료/안전",
        "relation": "편의",
        "priority": "중",
        "use_case": "응급 이송 인프라 확인",
    },
    {
        "slug": "optical_shops",
        "group": "의료/안전",
        "relation": "편의",
        "priority": "보조",
        "use_case": "안경·렌즈 파손 등 여행 중 생활 불편 대응",
    },
    {
        "slug": "tourist_restaurants",
        "group": "식음",
        "relation": "직접",
        "priority": "상",
        "use_case": "관광식당 후보와 관광권역 식음 밀도 분석",
    },
    {
        "slug": "general_restaurants",
        "group": "식음",
        "relation": "직접",
        "priority": "상",
        "use_case": "일반 음식점 POI와 상권 분석",
    },
    {
        "slug": "rest_cafes",
        "group": "식음",
        "relation": "직접",
        "priority": "상",
        "use_case": "카페·휴게음식점 접근성 분석",
    },
    {
        "slug": "bakeries",
        "group": "식음",
        "relation": "직접",
        "priority": "중",
        "use_case": "제과점·간식 구매 지점",
    },
    {
        "slug": "instant_food_processors",
        "group": "식음",
        "relation": "간접",
        "priority": "중",
        "use_case": "즉석 제조 음식과 지역 먹거리 밀도",
    },
    {
        "slug": "singing_bars",
        "group": "야간/유흥",
        "relation": "간접",
        "priority": "보조",
        "use_case": "야간 상권과 유흥 밀집도 참고",
    },
    {
        "slug": "entertainment_bars",
        "group": "야간/유흥",
        "relation": "간접",
        "priority": "보조",
        "use_case": "유흥주점 밀집 구역과 야간 관광 상권 참고",
    },
    {
        "slug": "tourist_entertainment_restaurants",
        "group": "야간/유흥",
        "relation": "직접",
        "priority": "중",
        "use_case": "관광유흥음식점 분포",
    },
    {
        "slug": "foreigners_entertainment_restaurants",
        "group": "야간/유흥",
        "relation": "직접",
        "priority": "중",
        "use_case": "외국인 전용 유흥음식점 분포",
    },
    {
        "slug": "tourist_accommodations",
        "group": "숙박",
        "relation": "직접",
        "priority": "상",
        "use_case": "관광숙박업 핵심 숙박 POI",
    },
    {
        "slug": "lodgings",
        "group": "숙박",
        "relation": "직접",
        "priority": "상",
        "use_case": "일반 숙박업 분포와 숙박 수용력 추정",
    },
    {
        "slug": "tourist_pensions",
        "group": "숙박",
        "relation": "직접",
        "priority": "상",
        "use_case": "관광펜션 분포와 체류형 관광 분석",
    },
    {
        "slug": "rural_homestays",
        "group": "숙박",
        "relation": "직접",
        "priority": "상",
        "use_case": "농어촌민박과 로컬 체류 관광 분석",
    },
    {
        "slug": "foreigner_city_homestays",
        "group": "숙박",
        "relation": "직접",
        "priority": "상",
        "use_case": "외국인관광도시민박 분포",
    },
    {
        "slug": "general_campgrounds",
        "group": "숙박",
        "relation": "직접",
        "priority": "상",
        "use_case": "일반야영장과 캠핑 여행지 분석",
    },
    {
        "slug": "auto_campgrounds",
        "group": "숙박",
        "relation": "직접",
        "priority": "상",
        "use_case": "자동차야영장과 차박·캠핑 동선 분석",
    },
    {
        "slug": "hanok_experience",
        "group": "숙박",
        "relation": "직접",
        "priority": "상",
        "use_case": "한옥체험 숙박과 전통 체험 콘텐츠",
    },
    {
        "slug": "domestic_travel_agencies",
        "group": "여행업",
        "relation": "직접",
        "priority": "중",
        "use_case": "국내여행 상품 공급자 분석",
    },
    {
        "slug": "domestic_international_travel_agencies",
        "group": "여행업",
        "relation": "직접",
        "priority": "중",
        "use_case": "국내외 여행업 사업자 분포",
    },
    {
        "slug": "comprehensive_travel_agencies",
        "group": "여행업",
        "relation": "직접",
        "priority": "중",
        "use_case": "종합여행업 사업자 분포",
    },
    {
        "slug": "tourism_businesses",
        "group": "관광/문화",
        "relation": "직접",
        "priority": "상",
        "use_case": "관광사업자 핵심 카탈로그",
    },
    {
        "slug": "tourist_cruises",
        "group": "관광/문화",
        "relation": "직접",
        "priority": "상",
        "use_case": "관광유람선과 수변 관광 동선",
    },
    {
        "slug": "city_tour_businesses",
        "group": "관광/문화",
        "relation": "직접",
        "priority": "상",
        "use_case": "시내순환관광업과 도시 관광 교통",
    },
    {
        "slug": "tourist_railways",
        "group": "관광/문화",
        "relation": "직접",
        "priority": "상",
        "use_case": "관광궤도업과 관광 이동 시설",
    },
    {
        "slug": "museums_and_art_galleries",
        "group": "관광/문화",
        "relation": "직접",
        "priority": "상",
        "use_case": "박물관·미술관 관광 POI",
    },
    {
        "slug": "performance_halls",
        "group": "관광/문화",
        "relation": "직접",
        "priority": "상",
        "use_case": "공연장과 문화관광 콘텐츠 분석",
    },
    {
        "slug": "tourist_performance_halls",
        "group": "관광/문화",
        "relation": "직접",
        "priority": "상",
        "use_case": "관광공연장업 분포",
    },
    {
        "slug": "tourist_theater_entertainment",
        "group": "관광/문화",
        "relation": "직접",
        "priority": "중",
        "use_case": "관광극장유흥업과 공연·야간 콘텐츠 참고",
    },
    {
        "slug": "international_convention_facilities",
        "group": "MICE",
        "relation": "직접",
        "priority": "상",
        "use_case": "국제회의시설과 MICE 관광 인프라",
    },
    {
        "slug": "international_convention_planners",
        "group": "MICE",
        "relation": "직접",
        "priority": "중",
        "use_case": "국제회의기획업 사업자 분포",
    },
    {
        "slug": "amusement_facilities_other",
        "group": "레저/놀이",
        "relation": "직접",
        "priority": "상",
        "use_case": "기타 테마파크·유원시설 분포",
    },
    {
        "slug": "general_amusement_facilities",
        "group": "레저/놀이",
        "relation": "직접",
        "priority": "상",
        "use_case": "일반 테마파크·유원시설 분포",
    },
    {
        "slug": "comprehensive_amusement_facilities",
        "group": "레저/놀이",
        "relation": "직접",
        "priority": "상",
        "use_case": "종합테마파크업 분포",
    },
    {
        "slug": "special_resorts",
        "group": "레저/놀이",
        "relation": "직접",
        "priority": "상",
        "use_case": "전문휴양업과 리조트형 관광 분석",
    },
    {
        "slug": "comprehensive_resorts",
        "group": "레저/놀이",
        "relation": "직접",
        "priority": "상",
        "use_case": "종합휴양업과 복합 휴양지 분석",
    },
    {
        "slug": "traditional_temples",
        "group": "관광/문화",
        "relation": "직접",
        "priority": "중",
        "use_case": "전통사찰과 역사·문화 관광지",
    },
    {
        "slug": "local_culture_centers",
        "group": "관광/문화",
        "relation": "간접",
        "priority": "중",
        "use_case": "지방문화원과 지역 문화 콘텐츠 거점",
    },
    {
        "slug": "pop_culture_art_planners",
        "group": "관광/문화",
        "relation": "간접",
        "priority": "보조",
        "use_case": "공연·행사 기획자와 지역 이벤트 공급자",
    },
    {
        "slug": "cultural_art_corporations",
        "group": "관광/문화",
        "relation": "간접",
        "priority": "보조",
        "use_case": "문화예술법인 기반 지역 문화 인프라",
    },
    {
        "slug": "movie_theaters",
        "group": "도시여가",
        "relation": "간접",
        "priority": "중",
        "use_case": "영화상영관과 실내 여가 POI",
    },
    {
        "slug": "film_screenings",
        "group": "도시여가",
        "relation": "간접",
        "priority": "보조",
        "use_case": "영화상영업 시설 참고",
    },
    {
        "slug": "pc_bangs",
        "group": "도시여가",
        "relation": "간접",
        "priority": "보조",
        "use_case": "도시형 실내 여가와 야간 체류 편의",
    },
    {
        "slug": "mixed_game_providers",
        "group": "도시여가",
        "relation": "간접",
        "priority": "보조",
        "use_case": "복합유통게임제공업과 실내 여가 시설",
    },
    {
        "slug": "general_game_providers",
        "group": "도시여가",
        "relation": "간접",
        "priority": "보조",
        "use_case": "일반게임제공업과 오락 시설",
    },
    {
        "slug": "youth_game_providers",
        "group": "도시여가",
        "relation": "간접",
        "priority": "보조",
        "use_case": "청소년게임제공업과 가족 동반 여가 참고",
    },
    {
        "slug": "karaoke_rooms",
        "group": "도시여가",
        "relation": "간접",
        "priority": "보조",
        "use_case": "노래연습장과 야간 여가 상권",
    },
    {
        "slug": "video_viewing_rooms",
        "group": "도시여가",
        "relation": "간접",
        "priority": "보조",
        "use_case": "비디오물감상실업과 실내 여가 참고",
    },
    {
        "slug": "golf_courses",
        "group": "스포츠/레저",
        "relation": "직접",
        "priority": "상",
        "use_case": "골프 관광과 체류형 레저 분석",
    },
    {
        "slug": "golf_practice_ranges",
        "group": "스포츠/레저",
        "relation": "간접",
        "priority": "중",
        "use_case": "골프 연습장과 레저 상권",
    },
    {
        "slug": "ski_resorts",
        "group": "스포츠/레저",
        "relation": "직접",
        "priority": "상",
        "use_case": "스키 관광 목적지",
    },
    {
        "slug": "horse_riding",
        "group": "스포츠/레저",
        "relation": "직접",
        "priority": "중",
        "use_case": "승마 체험형 관광",
    },
    {
        "slug": "sledding",
        "group": "스포츠/레저",
        "relation": "직접",
        "priority": "중",
        "use_case": "가족형 겨울 레저 목적지",
    },
    {
        "slug": "yacht_marinas",
        "group": "스포츠/레저",
        "relation": "직접",
        "priority": "상",
        "use_case": "요트장과 해양 레저 관광",
    },
    {
        "slug": "swimming_pools",
        "group": "스포츠/레저",
        "relation": "간접",
        "priority": "중",
        "use_case": "수영장과 가족·실내 레저",
    },
    {
        "slug": "ice_rinks",
        "group": "스포츠/레저",
        "relation": "간접",
        "priority": "중",
        "use_case": "빙상장과 계절형 실내 레저",
    },
    {
        "slug": "billiard_halls",
        "group": "스포츠/레저",
        "relation": "간접",
        "priority": "보조",
        "use_case": "당구장과 도시형 실내 여가",
    },
    {
        "slug": "registered_sports_facilities",
        "group": "스포츠/레저",
        "relation": "간접",
        "priority": "중",
        "use_case": "등록체육시설과 스포츠 관광 기반",
    },
    {
        "slug": "dance_halls",
        "group": "스포츠/레저",
        "relation": "간접",
        "priority": "보조",
        "use_case": "무도장과 야간·실내 여가 참고",
    },
    {
        "slug": "comprehensive_sports_facilities",
        "group": "스포츠/레저",
        "relation": "간접",
        "priority": "중",
        "use_case": "종합체육시설과 스포츠 이벤트 입지",
    },
    {
        "slug": "fitness_centers",
        "group": "생활편의",
        "relation": "편의",
        "priority": "보조",
        "use_case": "장기 체류 여행자의 운동 편의",
    },
    {
        "slug": "public_baths",
        "group": "생활편의",
        "relation": "편의",
        "priority": "중",
        "use_case": "목욕장·사우나와 여행 중 휴식 편의",
    },
    {
        "slug": "large_scale_retail_stores",
        "group": "쇼핑/생활",
        "relation": "간접",
        "priority": "상",
        "use_case": "대규모점포와 쇼핑 관광·생활 편의",
    },
    {
        "slug": "beauty_salons",
        "group": "쇼핑/생활",
        "relation": "편의",
        "priority": "보조",
        "use_case": "미용 서비스와 장기 체류 편의",
    },
    {
        "slug": "barber_shops",
        "group": "쇼핑/생활",
        "relation": "편의",
        "priority": "보조",
        "use_case": "이용업과 장기 체류 생활 편의",
    },
    {
        "slug": "laundries",
        "group": "쇼핑/생활",
        "relation": "편의",
        "priority": "중",
        "use_case": "세탁업과 장기 체류·캠핑 여행 편의",
    },
    {
        "slug": "oil_retailers",
        "group": "이동/주유",
        "relation": "편의",
        "priority": "중",
        "use_case": "렌터카·자차 여행 주유 편의",
    },
    {
        "slug": "petroleum_alt_fuel_retailers",
        "group": "이동/주유",
        "relation": "편의",
        "priority": "보조",
        "use_case": "대체연료 판매 지점과 차량 이동 편의",
    },
    {
        "slug": "animal_hospitals",
        "group": "동반동물",
        "relation": "편의",
        "priority": "중",
        "use_case": "반려동물 동반 여행 중 진료 거점",
    },
    {
        "slug": "animal_pharmacies",
        "group": "동반동물",
        "relation": "편의",
        "priority": "보조",
        "use_case": "반려동물 약품 구매 편의",
    },
    {
        "slug": "animal_boarding",
        "group": "동반동물",
        "relation": "편의",
        "priority": "보조",
        "use_case": "반려동물 위탁관리와 여행 활동 보조",
    },
    {
        "slug": "pet_grooming",
        "group": "동반동물",
        "relation": "편의",
        "priority": "보조",
        "use_case": "반려동물 미용과 장기 체류 편의",
    },
)


def esc(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def write_api_list(root: Path) -> None:
    lines: list[str] = []
    lines.append("# API 및 파일 다운로드 목록")
    lines.append("")
    lines.append(
        "이 문서는 data.go.kr 공지 `NOTICE_0000000004566`의 붙임2와 "
        "OpenAPI 활용신청 링크, file.localdata.go.kr 카탈로그에서 생성했습니다."
    )
    lines.append("")
    lines.append("## OpenAPI 목록")
    lines.append("")
    lines.append(f"- OpenAPI 업종: {len(OPENAPI_SERVICES)}개")
    lines.append(f"- 호출 URL: 조회 {len(OPENAPI_SERVICES)}개, 이력조회 {len(OPENAPI_SERVICES)}개")
    lines.append("")
    lines.append("| 번호 | 분류 | 업종 | slug | 활용신청 | 조회 URL | 이력 URL | 편의 함수 |")
    lines.append("|---:|---|---|---|---|---|---|---|")
    for row in OPENAPI_SERVICES:
        slug = row["slug"]
        lines.append(
            f"| {row['index']} | {esc(row['category'])} | {esc(row['name'])} | `{slug}` | "
            f"[신청]({esc(row['application_url'])}) | "
            f"`{esc(row['info_url'])}` | `{esc(row['history_url'])}` | "
            f"`client.get_{slug}()`, `client.get_{slug}_history()` |"
        )

    lines.append("")
    lines.append("## 파일 다운로드 목록")
    lines.append("")
    license_downloads = [row for row in FILE_DOWNLOADS if row["kind"] == "license"]
    life_downloads = [row for row in FILE_DOWNLOADS if row["kind"] == "life_convenience"]
    lines.append(f"- 인허가정보 파일 다운로드: {len(license_downloads)}개")
    lines.append(
        f"- 생활편의정보 파일 다운로드: {len(life_downloads)}개 "
        "(`list_file_downloads(kind=None)`에서 함께 확인 가능)"
    )
    lines.append("")
    lines.append("| 분류 | 업종 | slug | 다운로드 URL | 편의 함수 |")
    lines.append("|---|---|---|---|---|")
    for row in license_downloads:
        slug = row["slug"]
        lines.append(
            f"| {esc(row['category'])} | {esc(row['name'])} | `{slug}` | "
            f"`{esc(row['download_url'])}` | "
            f"`files.download_{slug}(path)`, `files.load_{slug}()`, `files.iter_{slug}()` |"
        )

    lines.append("")
    lines.append("## 코드에서 목록 확인")
    lines.append("")
    lines.append("```python")
    lines.append(
        "from mois import ("
    )
    lines.append(
        "    list_file_downloads,"
    )
    lines.append(
        "    list_incremental_openapi_endpoints,"
    )
    lines.append(
        "    list_openapi_endpoints,"
    )
    lines.append(
        "    list_openapi_services,"
    )
    lines.append(
        ")"
    )
    lines.append("")
    lines.append("services = list_openapi_services()")
    lines.append("incremental = list_incremental_openapi_endpoints()")
    lines.append('endpoints = list_openapi_endpoints(kind="history")')
    lines.append("downloads = list_file_downloads()")
    lines.append("```")
    (root / "api-list.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_incremental_openapi(root: Path) -> None:
    lines: list[str] = []
    lines.append("# 증분 OpenAPI 목록과 신청 링크")
    lines.append("")
    lines.append(
        "이 문서는 data.go.kr 공지 `NOTICE_0000000004566`의 OpenAPI 활용신청 링크와 "
        "붙임1의 변동분 조회 규칙을 기준으로 생성했습니다."
    )
    lines.append("")
    lines.append("## 신청 방법")
    lines.append("")
    lines.append("1. 아래 목록에서 필요한 업종의 `신청` 링크를 엽니다.")
    lines.append("2. 공공데이터포털에 로그인한 뒤 `활용신청`을 진행합니다.")
    lines.append(
        "3. 승인 후 발급된 디코딩 서비스키를 `MOIS_SERVICE_KEY` 또는 "
        "`MoisClient`에 전달합니다."
    )
    lines.append("4. 여러 업종을 호출해야 하면 각 업종 OpenAPI의 활용 권한을 확인합니다.")
    lines.append("")
    lines.append("## 증분 조회 규칙")
    lines.append("")
    lines.append("- 기본 증분 조건은 `cond[DAT_UPDT_PNT::GTE]=YYYYMMDDHHMMSS`입니다.")
    lines.append(
        "- `DAT_UPDT_PNT`는 원천데이터 수정과 개방데이터 보강 수정 시점을 "
        "함께 반영합니다."
    )
    lines.append(
        "- 원천데이터 최종수정시점만 기준으로 삼을 때는 "
        "`source_modified=True`를 사용해 `LAST_MDFCN_PNT::GTE`로 조회합니다."
    )
    lines.append(
        "- `numOfRows`는 최대 100이며, 전체 동기화는 `totalCount`와 "
        "`pageNo` 기반으로 페이지를 넘깁니다."
    )
    lines.append("")
    lines.append("```python")
    lines.append("from mois import MoisClient, list_incremental_openapi_endpoints")
    lines.append("")
    lines.append("with MoisClient.from_env() as client:")
    lines.append('    changed = client.get_updated_hospitals("20260505000000")')
    lines.append("    source_changed = client.get_updated_hospitals(")
    lines.append('        "20260505000000",')
    lines.append("        source_modified=True,")
    lines.append("    )")
    lines.append("")
    lines.append("for api in list_incremental_openapi_endpoints():")
    lines.append("    print(api.service_slug, api.application_url, api.get_method)")
    lines.append("```")
    lines.append("")
    lines.append("비동기 배치에서는 `MoisClient.aio()`를 사용합니다.")
    lines.append("")
    lines.append("```python")
    lines.append("import asyncio")
    lines.append("")
    lines.append("from mois import MoisClient")
    lines.append("")
    lines.append("")
    lines.append("async def main():")
    lines.append("    async with MoisClient.aio() as client:")
    lines.append('        changed = await client.get_updated_hospitals("20260505000000")')
    lines.append("        print(len(changed))")
    lines.append("")
    lines.append("")
    lines.append("asyncio.run(main())")
    lines.append("```")
    lines.append("")
    lines.append("## 전체 증분 API 목록")
    lines.append("")
    lines.append(f"- 증분 조회 대상 OpenAPI: {len(INCREMENTAL_OPENAPI_ENDPOINTS)}개")
    lines.append(
        "- 모든 항목은 같은 호출 URL의 `info` 엔드포인트에 조건 파라미터를 "
        "붙여 사용합니다."
    )
    lines.append("")
    lines.append(
        "| 번호 | 분류 | 업종 | slug | 신청 링크 | 증분 호출 URL | 기본 증분 함수 | 원천수정 증분 |"
    )
    lines.append("|---:|---|---|---|---|---|---|---|")
    for number, row in enumerate(INCREMENTAL_OPENAPI_ENDPOINTS, start=1):
        slug = row["service_slug"]
        get_method = row["get_method"]
        lines.append(
            f"| {number} | {esc(row['category'])} | {esc(row['name'])} | `{slug}` | "
            f"[신청]({esc(row['application_url'])}) | `{esc(row['info_url'])}` | "
            f"`client.{get_method}(since)` | "
            f"`client.{get_method}(since, source_modified=True)` |"
        )
    (root / "incremental-openapi.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_response_fields(root: Path) -> None:
    lines: list[str] = []
    lines.append("# 응답변수 매핑표")
    lines.append("")
    lines.append(
        "이 문서는 붙임3 `지방행정 인허가정보의 제공항목(응답변수) "
        "매핑테이블_20260407수정.xlsx`에서 생성했습니다."
    )
    lines.append(
        "삭제로 표시된 항목은 기본 API 응답 필드가 아니므로 `list_response_fields()`에서는 "
        "제외되고, `include_deleted=True`일 때만 반환됩니다."
    )
    lines.append("")
    lines.append(f"- 전체 매핑 행: {len(RESPONSE_FIELDS)}개")
    lines.append(f"- 기본 반환 필드: {sum(1 for row in RESPONSE_FIELDS if not row['deleted'])}개")
    lines.append("")
    lines.append(
        "| 그룹 | LOCALDATA 영문명 | LOCALDATA 한글명 | 응답변수 | "
        "응답변수 한글명 | 유형 | 길이 | 비고 |"
    )
    lines.append("|---|---|---|---|---|---|---:|---|")
    for row in RESPONSE_FIELDS:
        field = f"`{row['field']}`" if row["field"] else ""
        local_field = f"`{row['local_field']}`" if row["local_field"] else ""
        note = row["note"] or ("삭제" if row["deleted"] else "")
        lines.append(
            f"| {esc(row['group'])} | {local_field} | {esc(row['local_name'])} | {field} | "
            f"{esc(row['name'])} | {esc(row['type'])} | {esc(row['length'])} | {esc(note)} |"
        )
    (root / "response-fields.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_file_downloads(root: Path) -> None:
    lines: list[str] = []
    license_downloads = [row for row in FILE_DOWNLOADS if row["kind"] == "license"]
    lines.append("# 파일 다운로드와 로드 API")
    lines.append("")
    lines.append(
        "localdata 파일 다운로드는 인허가정보 195개 업종을 대상으로 제공합니다. "
        "파일은 CP949 CSV로 내려오며, 로더는 날짜, 시각, 숫자, EPSG:5174 좌표를 "
        "Python 타입과 WGS84 좌표로 변환합니다."
    )
    lines.append("")
    lines.append(
        "참고 PDF는 인허가정보 195종과 생활편의정보 14종, 총 209종을 언급합니다. "
        "다만 2026년 5월 6일 현재 `file.localdata.go.kr`의 파일 다운로드 카탈로그에서 "
        "확인되는 생활편의정보는 13종이므로, `mois`는 실제 확인된 208종만 "
        "카탈로그에 포함합니다."
    )
    lines.append("")
    lines.append("## 기본 사용")
    lines.append("")
    lines.append("```python")
    lines.append("from mois import LocalDataFileClient")
    lines.append("")
    lines.append("with LocalDataFileClient() as files:")
    lines.append('    records = files.load("hospitals")')
    lines.append("")
    lines.append("first = records[0]")
    lines.append("print(first.business_name)")
    lines.append("print(first.license_date)")
    lines.append("print(first.coordinates.lon, first.coordinates.lat)")
    lines.append("print(first.coordinates.wgs84_point.as_tuple())  # (lon, lat)")
    lines.append("```")
    lines.append("")
    lines.append(
        "대용량 업종은 전체 목록을 메모리에 올리는 `load()`보다 스트리밍 API를 사용합니다."
    )
    lines.append("")
    lines.append("```python")
    lines.append("with LocalDataFileClient() as files:")
    lines.append("    for record in files.iter_hospitals():")
    lines.append("        print(record.management_number, record.business_name)")
    lines.append("```")
    lines.append("")
    lines.append("asyncio 환경에서는 `aio()`를 사용합니다.")
    lines.append("")
    lines.append("```python")
    lines.append("import asyncio")
    lines.append("")
    lines.append("from mois import LocalDataFileClient")
    lines.append("")
    lines.append("")
    lines.append("async def main():")
    lines.append("    async with LocalDataFileClient.aio() as files:")
    lines.append('        records = await files.load("hospitals")')
    lines.append("        print(records[0].business_name)")
    lines.append("")
    lines.append("        async for record in files.iter_hospitals():")
    lines.append("            print(record.management_number, record.business_name)")
    lines.append("            break")
    lines.append("")
    lines.append("")
    lines.append("asyncio.run(main())")
    lines.append("```")
    lines.append("")
    lines.append("## 지역별 다운로드")
    lines.append("")
    lines.append(
        "지역별 파일은 localdata의 `orgCode`를 그대로 전달합니다. "
        "예: 서울종로구 `3000000`."
    )
    lines.append("")
    lines.append("```python")
    lines.append("with LocalDataFileClient() as files:")
    lines.append('    records = files.load("hospitals", org_code="3000000")')
    lines.append("```")
    lines.append("")
    lines.append("## 변환 규칙")
    lines.append("")
    lines.append("| 원본 | 변환 |")
    lines.append("|---|---|")
    lines.append("| `인허가일자`, `폐업일자` 등 일자 | `datetime.date` |")
    lines.append("| `데이터갱신시점`, `최종수정시점` | KST timezone-aware `datetime.datetime` |")
    lines.append("| `NUMBER` 필드와 면적/수량 계열 | `int` 또는 `float` |")
    lines.append(
        "| `좌표정보(X/Y)` | 원본 `CRD_INFO_X/Y` float + "
        "`WGS84_LON/LAT` + `Coordinate`, `KatecPoint`, `Wgs84Point` 값 객체 |"
    )
    lines.append("| 빈 문자열/공백 | `None` |")
    lines.append("")
    lines.append(
        "좌표 순서는 KATEC/EPSG:5174가 `(x, y)`, WGS84/EPSG:4326이 `(lon, lat)`입니다. "
        "자세한 타입은 [타입과 좌표 값 객체](types-and-coordinates.md)를 봅니다."
    )
    lines.append("")
    lines.append("## 전체 다운로드 함수 목록")
    lines.append("")
    lines.append("| 분류 | 업종 | slug | 로드 함수 | 스트리밍 함수 | 다운로드 함수 |")
    lines.append("|---|---|---|---|---|---|")
    for row in license_downloads:
        slug = row["slug"]
        lines.append(
            f"| {esc(row['category'])} | {esc(row['name'])} | `{slug}` | "
            f"`files.load_{slug}()` | `files.iter_{slug}()` | `files.download_{slug}(path)` |"
        )
    (root / "file-downloads.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tourism_license_data(root: Path) -> None:
    service_by_slug = {row["slug"]: row for row in OPENAPI_SERVICES}
    download_by_slug = {row["slug"]: row for row in FILE_DOWNLOADS}
    missing = [
        str(row["slug"])
        for row in TOURISM_LICENSE_SELECTION
        if row["slug"] not in service_by_slug or row["slug"] not in download_by_slug
    ]
    if missing:
        raise ValueError(f"관광 인허가 선별 목록에 없는 slug가 있습니다: {', '.join(missing)}")

    group_counts: dict[str, int] = {}
    for row in TOURISM_LICENSE_SELECTION:
        group = str(row["group"])
        group_counts[group] = group_counts.get(group, 0) + 1

    lines: list[str] = []
    lines.append("# 관광 관련 인허가 데이터 선별 목록")
    lines.append("")
    lines.append(
        "이 문서는 `mois.catalog`의 공식 인허가 OpenAPI/파일 다운로드 카탈로그에서 "
        "관광과 직간접적으로 연결되는 업종만 선별해 생성했습니다."
    )
    lines.append("")
    lines.append("## 선별 기준")
    lines.append("")
    lines.append(
        "- `직접`: 숙박, 여행업, 관광시설, 공연·문화시설, 레저처럼 관광 목적지나 "
        "관광 상품을 직접 구성하는 업종"
    )
    lines.append(
        "- `간접`: 식음, 쇼핑, 도시 여가, 야간 상권처럼 여행 경험과 관광권역 "
        "분석에 자주 쓰이는 업종"
    )
    lines.append(
        "- `편의`: 병원, 약국, 주유, 세탁처럼 여행 중 편의·안전·장기 체류를 "
        "보조하는 업종"
    )
    lines.append("")
    lines.append(
        "공급망, 제조, 도매, 백오피스 성격이 강하고 여행자 POI로 바로 쓰기 어려운 "
        "업종은 제외했습니다. 전체 카탈로그는 [API 및 파일 다운로드 목록](api-list.md)을 "
        "확인합니다."
    )
    lines.append("")
    lines.append("## 요약")
    lines.append("")
    lines.append(f"- 선별 업종: {len(TOURISM_LICENSE_SELECTION)}개")
    lines.append("- 좌표가 있는 행은 로더에서 WGS84 `(lon, lat)` 좌표로 함께 변환됩니다.")
    lines.append("- 기본 적재와 분석은 `files.iter_<slug>()` 스트리밍 함수를 권장합니다.")
    lines.append("")
    lines.append("| 묶음 | 업종 수 |")
    lines.append("|---|---:|")
    for group, count in group_counts.items():
        lines.append(f"| {esc(group)} | {count} |")
    lines.append("")
    lines.append("## 전체 선별 목록")
    lines.append("")
    lines.append("| 묶음 | 관련성 | 우선 | 업종 | slug | 활용 예 | 신청 링크 | 파일 로드 |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for selection in TOURISM_LICENSE_SELECTION:
        slug = str(selection["slug"])
        service = service_by_slug[slug]
        lines.append(
            f"| {esc(selection['group'])} | {esc(selection['relation'])} | "
            f"{esc(selection['priority'])} | {esc(service['name'])} | `{slug}` | "
            f"{esc(selection['use_case'])} | [신청]({esc(service['application_url'])}) | "
            f"`files.iter_{slug}()` |"
        )
    lines.append("")
    lines.append("## 사용 예")
    lines.append("")
    lines.append("```python")
    lines.append("from mois import LocalDataFileClient")
    lines.append("")
    lines.append("with LocalDataFileClient() as files:")
    lines.append("    for record in files.iter_tourist_accommodations():")
    lines.append("        point = record.coordinates.wgs84_point if record.coordinates else None")
    lines.append("        print(record.business_name, point)")
    lines.append("```")
    lines.append("")
    lines.append("여러 업종을 한 DB에 넣을 때는 `service_slug`를 함께 저장해 업종을 구분합니다.")
    lines.append("")
    lines.append("```python")
    lines.append("from mois import LocalDataFileClient")
    lines.append("")
    lines.append("TOURISM_SLUGS = [")
    lines.append('    "tourist_accommodations",')
    lines.append('    "lodgings",')
    lines.append('    "tourist_restaurants",')
    lines.append('    "pharmacies",')
    lines.append("]")
    lines.append("")
    lines.append("with LocalDataFileClient() as files:")
    lines.append("    for slug in TOURISM_SLUGS:")
    lines.append("        for record in files.iter(slug):")
    lines.append("            print(slug, record.business_name)")
    lines.append("```")
    (root / "tourism-license-data.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    root = Path("docs")
    root.mkdir(exist_ok=True)
    write_api_list(root)
    write_incremental_openapi(root)
    write_response_fields(root)
    write_file_downloads(root)
    write_tourism_license_data(root)


if __name__ == "__main__":
    main()
