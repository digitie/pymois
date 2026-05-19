# 관광 관련 인허가 데이터 선별 목록

이 문서는 `mois.catalog`의 공식 인허가 OpenAPI/파일 다운로드 카탈로그에서 관광과 직간접적으로 연결되는 업종만 선별해 생성했습니다.

## 선별 기준

- `직접`: 숙박, 여행업, 관광시설, 공연·문화시설, 레저처럼 관광 목적지나 관광 상품을 직접 구성하는 업종
- `간접`: 식음, 쇼핑, 도시 여가, 야간 상권처럼 여행 경험과 관광권역 분석에 자주 쓰이는 업종
- `편의`: 병원, 약국, 주유, 세탁처럼 여행 중 편의·안전·장기 체류를 보조하는 업종

공급망, 제조, 도매, 백오피스 성격이 강하고 여행자 POI로 바로 쓰기 어려운 업종은 제외했습니다. 전체 카탈로그는 [API 및 파일 다운로드 목록](api-list.md)을 확인합니다.

## 요약

- 선별 업종: 77개
- 좌표가 있는 행은 로더에서 WGS84 `(lon, lat)` 좌표로 함께 변환됩니다.
- 기본 적재와 분석은 `files.iter_<slug>()` 스트리밍 함수를 권장합니다.

| 묶음 | 업종 수 |
|---|---:|
| 의료/안전 | 6 |
| 식음 | 5 |
| 야간/유흥 | 4 |
| 숙박 | 8 |
| 여행업 | 3 |
| 관광/문화 | 12 |
| MICE | 2 |
| 레저/놀이 | 5 |
| 도시여가 | 8 |
| 스포츠/레저 | 12 |
| 생활편의 | 2 |
| 쇼핑/생활 | 4 |
| 이동/주유 | 2 |
| 동반동물 | 4 |

## 전체 선별 목록

| 묶음 | 관련성 | 우선 | 업종 | slug | 활용 예 | 신청 링크 | 파일 로드 |
|---|---|---|---|---|---|---|---|
| 의료/안전 | 편의 | 상 | 병원 | `hospitals` | 여행 중 응급/외래 진료 거점 | [신청](https://www.data.go.kr/data/15154458/openapi.do) | `files.iter_hospitals()` |
| 의료/안전 | 편의 | 상 | 의원 | `clinics` | 가벼운 질환과 지역 의원 접근성 분석 | [신청](https://www.data.go.kr/data/15154874/openapi.do) | `files.iter_clinics()` |
| 의료/안전 | 편의 | 상 | 약국 | `pharmacies` | 상비약·처방약 구매 편의 | [신청](https://www.data.go.kr/data/15154822/openapi.do) | `files.iter_pharmacies()` |
| 의료/안전 | 편의 | 중 | 안전상비의약품 판매업소 | `over_the_counter_medicine_stores` | 야간·휴일 안전상비의약품 구매 편의 | [신청](https://www.data.go.kr/data/15154791/openapi.do) | `files.iter_over_the_counter_medicine_stores()` |
| 의료/안전 | 편의 | 중 | 응급환자이송업 | `emergency_patient_transport` | 응급 이송 인프라 확인 | [신청](https://www.data.go.kr/data/15154834/openapi.do) | `files.iter_emergency_patient_transport()` |
| 의료/안전 | 편의 | 보조 | 안경업 | `optical_shops` | 안경·렌즈 파손 등 여행 중 생활 불편 대응 | [신청](https://www.data.go.kr/data/15154899/openapi.do) | `files.iter_optical_shops()` |
| 식음 | 직접 | 상 | 관광식당 | `tourist_restaurants` | 관광식당 후보와 관광권역 식음 밀도 분석 | [신청](https://www.data.go.kr/data/15154897/openapi.do) | `files.iter_tourist_restaurants()` |
| 식음 | 직접 | 상 | 일반음식점 | `general_restaurants` | 일반 음식점 POI와 상권 분석 | [신청](https://www.data.go.kr/data/15154916/openapi.do) | `files.iter_general_restaurants()` |
| 식음 | 직접 | 상 | 휴게음식점 | `rest_cafes` | 카페·휴게음식점 접근성 분석 | [신청](https://www.data.go.kr/data/15154921/openapi.do) | `files.iter_rest_cafes()` |
| 식음 | 직접 | 중 | 제과점영업 | `bakeries` | 제과점·간식 구매 지점 | [신청](https://www.data.go.kr/data/15155252/openapi.do) | `files.iter_bakeries()` |
| 식음 | 간접 | 중 | 즉석판매제조가공업 | `instant_food_processors` | 즉석 제조 음식과 지역 먹거리 밀도 | [신청](https://www.data.go.kr/data/15155245/openapi.do) | `files.iter_instant_food_processors()` |
| 야간/유흥 | 간접 | 보조 | 단란주점영업 | `singing_bars` | 야간 상권과 유흥 밀집도 참고 | [신청](https://www.data.go.kr/data/15154883/openapi.do) | `files.iter_singing_bars()` |
| 야간/유흥 | 간접 | 보조 | 유흥주점영업 | `entertainment_bars` | 유흥주점 밀집 구역과 야간 관광 상권 참고 | [신청](https://www.data.go.kr/data/15154890/openapi.do) | `files.iter_entertainment_bars()` |
| 야간/유흥 | 직접 | 중 | 관광유흥음식점업 | `tourist_entertainment_restaurants` | 관광유흥음식점 분포 | [신청](https://www.data.go.kr/data/15154903/openapi.do) | `files.iter_tourist_entertainment_restaurants()` |
| 야간/유흥 | 직접 | 중 | 외국인전용유흥음식점업 | `foreigners_entertainment_restaurants` | 외국인 전용 유흥음식점 분포 | [신청](https://www.data.go.kr/data/15154910/openapi.do) | `files.iter_foreigners_entertainment_restaurants()` |
| 숙박 | 직접 | 상 | 관광숙박업 | `tourist_accommodations` | 관광숙박업 핵심 숙박 POI | [신청](https://www.data.go.kr/data/15155090/openapi.do) | `files.iter_tourist_accommodations()` |
| 숙박 | 직접 | 상 | 숙박업 | `lodgings` | 일반 숙박업 분포와 숙박 수용력 추정 | [신청](https://www.data.go.kr/data/15155124/openapi.do) | `files.iter_lodgings()` |
| 숙박 | 직접 | 상 | 관광펜션업 | `tourist_pensions` | 관광펜션 분포와 체류형 관광 분석 | [신청](https://www.data.go.kr/data/15155103/openapi.do) | `files.iter_tourist_pensions()` |
| 숙박 | 직접 | 상 | 농어촌민박업 | `rural_homestays` | 농어촌민박과 로컬 체류 관광 분석 | [신청](https://www.data.go.kr/data/15155113/openapi.do) | `files.iter_rural_homestays()` |
| 숙박 | 직접 | 상 | 외국인관광도시민박업 | `foreigner_city_homestays` | 외국인관광도시민박 분포 | [신청](https://www.data.go.kr/data/15155139/openapi.do) | `files.iter_foreigner_city_homestays()` |
| 숙박 | 직접 | 상 | 일반야영장업 | `general_campgrounds` | 일반야영장과 캠핑 여행지 분석 | [신청](https://www.data.go.kr/data/15155149/openapi.do) | `files.iter_general_campgrounds()` |
| 숙박 | 직접 | 상 | 자동차야영장업 | `auto_campgrounds` | 자동차야영장과 차박·캠핑 동선 분석 | [신청](https://www.data.go.kr/data/15154788/openapi.do) | `files.iter_auto_campgrounds()` |
| 숙박 | 직접 | 상 | 한옥체험업 | `hanok_experience` | 한옥체험 숙박과 전통 체험 콘텐츠 | [신청](https://www.data.go.kr/data/15154808/openapi.do) | `files.iter_hanok_experience()` |
| 여행업 | 직접 | 중 | 국내여행업 | `domestic_travel_agencies` | 국내여행 상품 공급자 분석 | [신청](https://www.data.go.kr/data/15154821/openapi.do) | `files.iter_domestic_travel_agencies()` |
| 여행업 | 직접 | 중 | 국내외여행업 | `domestic_international_travel_agencies` | 국내외 여행업 사업자 분포 | [신청](https://www.data.go.kr/data/15154825/openapi.do) | `files.iter_domestic_international_travel_agencies()` |
| 여행업 | 직접 | 중 | 종합여행업 | `comprehensive_travel_agencies` | 종합여행업 사업자 분포 | [신청](https://www.data.go.kr/data/15154829/openapi.do) | `files.iter_comprehensive_travel_agencies()` |
| 관광/문화 | 직접 | 상 | 관광사업자 | `tourism_businesses` | 관광사업자 핵심 카탈로그 | [신청](https://www.data.go.kr/data/15155130/openapi.do) | `files.iter_tourism_businesses()` |
| 관광/문화 | 직접 | 상 | 관광유람선업 | `tourist_cruises` | 관광유람선과 수변 관광 동선 | [신청](https://www.data.go.kr/data/15155134/openapi.do) | `files.iter_tourist_cruises()` |
| 관광/문화 | 직접 | 상 | 시내순환관광업 | `city_tour_businesses` | 시내순환관광업과 도시 관광 교통 | [신청](https://www.data.go.kr/data/15155152/openapi.do) | `files.iter_city_tour_businesses()` |
| 관광/문화 | 직접 | 상 | 관광궤도업 | `tourist_railways` | 관광궤도업과 관광 이동 시설 | [신청](https://www.data.go.kr/data/15155236/openapi.do) | `files.iter_tourist_railways()` |
| 관광/문화 | 직접 | 상 | 박물관 및 미술관 | `museums_and_art_galleries` | 박물관·미술관 관광 POI | [신청](https://www.data.go.kr/data/15155146/openapi.do) | `files.iter_museums_and_art_galleries()` |
| 관광/문화 | 직접 | 상 | 공연장 | `performance_halls` | 공연장과 문화관광 콘텐츠 분석 | [신청](https://www.data.go.kr/data/15154966/openapi.do) | `files.iter_performance_halls()` |
| 관광/문화 | 직접 | 상 | 관광공연장업 | `tourist_performance_halls` | 관광공연장업 분포 | [신청](https://www.data.go.kr/data/15154970/openapi.do) | `files.iter_tourist_performance_halls()` |
| 관광/문화 | 직접 | 중 | 관광극장유흥업 | `tourist_theater_entertainment` | 관광극장유흥업과 공연·야간 콘텐츠 참고 | [신청](https://www.data.go.kr/data/15154983/openapi.do) | `files.iter_tourist_theater_entertainment()` |
| MICE | 직접 | 상 | 국제회의시설업 | `international_convention_facilities` | 국제회의시설과 MICE 관광 인프라 | [신청](https://www.data.go.kr/data/15155138/openapi.do) | `files.iter_international_convention_facilities()` |
| MICE | 직접 | 중 | 국제회의기획업 | `international_convention_planners` | 국제회의기획업 사업자 분포 | [신청](https://www.data.go.kr/data/15155166/openapi.do) | `files.iter_international_convention_planners()` |
| 레저/놀이 | 직접 | 상 | 테마파크업(기타) | `amusement_facilities_other` | 기타 테마파크·유원시설 분포 | [신청](https://www.data.go.kr/data/15155250/openapi.do) | `files.iter_amusement_facilities_other()` |
| 레저/놀이 | 직접 | 상 | 일반테마파크업 | `general_amusement_facilities` | 일반 테마파크·유원시설 분포 | [신청](https://www.data.go.kr/data/15155157/openapi.do) | `files.iter_general_amusement_facilities()` |
| 레저/놀이 | 직접 | 상 | 종합테마파크업 | `comprehensive_amusement_facilities` | 종합테마파크업 분포 | [신청](https://www.data.go.kr/data/15155238/openapi.do) | `files.iter_comprehensive_amusement_facilities()` |
| 레저/놀이 | 직접 | 상 | 전문휴양업 | `special_resorts` | 전문휴양업과 리조트형 관광 분석 | [신청](https://www.data.go.kr/data/15155232/openapi.do) | `files.iter_special_resorts()` |
| 레저/놀이 | 직접 | 상 | 종합휴양업 | `comprehensive_resorts` | 종합휴양업과 복합 휴양지 분석 | [신청](https://www.data.go.kr/data/15155242/openapi.do) | `files.iter_comprehensive_resorts()` |
| 관광/문화 | 직접 | 중 | 전통사찰 | `traditional_temples` | 전통사찰과 역사·문화 관광지 | [신청](https://www.data.go.kr/data/15155235/openapi.do) | `files.iter_traditional_temples()` |
| 관광/문화 | 간접 | 중 | 지방문화원 | `local_culture_centers` | 지방문화원과 지역 문화 콘텐츠 거점 | [신청](https://www.data.go.kr/data/15155246/openapi.do) | `files.iter_local_culture_centers()` |
| 관광/문화 | 간접 | 보조 | 대중문화예술기획업 | `pop_culture_art_planners` | 공연·행사 기획자와 지역 이벤트 공급자 | [신청](https://www.data.go.kr/data/15155155/openapi.do) | `files.iter_pop_culture_art_planners()` |
| 관광/문화 | 간접 | 보조 | 문화예술법인 | `cultural_art_corporations` | 문화예술법인 기반 지역 문화 인프라 | [신청](https://www.data.go.kr/data/15155142/openapi.do) | `files.iter_cultural_art_corporations()` |
| 도시여가 | 간접 | 중 | 영화상영관 | `movie_theaters` | 영화상영관과 실내 여가 POI | [신청](https://www.data.go.kr/data/15154848/openapi.do) | `files.iter_movie_theaters()` |
| 도시여가 | 간접 | 보조 | 영화상영업 | `film_screenings` | 영화상영업 시설 참고 | [신청](https://www.data.go.kr/data/15154857/openapi.do) | `files.iter_film_screenings()` |
| 도시여가 | 간접 | 보조 | 인터넷컴퓨터게임시설제공업 | `pc_bangs` | 도시형 실내 여가와 야간 체류 편의 | [신청](https://www.data.go.kr/data/15154951/openapi.do) | `files.iter_pc_bangs()` |
| 도시여가 | 간접 | 보조 | 복합유통게임제공업 | `mixed_game_providers` | 복합유통게임제공업과 실내 여가 시설 | [신청](https://www.data.go.kr/data/15154945/openapi.do) | `files.iter_mixed_game_providers()` |
| 도시여가 | 간접 | 보조 | 일반게임제공업 | `general_game_providers` | 일반게임제공업과 오락 시설 | [신청](https://www.data.go.kr/data/15154955/openapi.do) | `files.iter_general_game_providers()` |
| 도시여가 | 간접 | 보조 | 청소년게임제공업 | `youth_game_providers` | 청소년게임제공업과 가족 동반 여가 참고 | [신청](https://www.data.go.kr/data/15154958/openapi.do) | `files.iter_youth_game_providers()` |
| 도시여가 | 간접 | 보조 | 노래연습장업 | `karaoke_rooms` | 노래연습장과 야간 여가 상권 | [신청](https://www.data.go.kr/data/15155135/openapi.do) | `files.iter_karaoke_rooms()` |
| 도시여가 | 간접 | 보조 | 비디오물감상실업 | `video_viewing_rooms` | 비디오물감상실업과 실내 여가 참고 | [신청](https://www.data.go.kr/data/15155128/openapi.do) | `files.iter_video_viewing_rooms()` |
| 스포츠/레저 | 직접 | 상 | 골프장 | `golf_courses` | 골프 관광과 체류형 레저 분석 | [신청](https://www.data.go.kr/data/15154978/openapi.do) | `files.iter_golf_courses()` |
| 스포츠/레저 | 간접 | 중 | 골프연습장업 | `golf_practice_ranges` | 골프 연습장과 레저 상권 | [신청](https://www.data.go.kr/data/15154975/openapi.do) | `files.iter_golf_practice_ranges()` |
| 스포츠/레저 | 직접 | 상 | 스키장 | `ski_resorts` | 스키 관광 목적지 | [신청](https://www.data.go.kr/data/15155041/openapi.do) | `files.iter_ski_resorts()` |
| 스포츠/레저 | 직접 | 중 | 승마장업 | `horse_riding` | 승마 체험형 관광 | [신청](https://www.data.go.kr/data/15155045/openapi.do) | `files.iter_horse_riding()` |
| 스포츠/레저 | 직접 | 중 | 썰매장업 | `sledding` | 가족형 겨울 레저 목적지 | [신청](https://www.data.go.kr/data/15155051/openapi.do) | `files.iter_sledding()` |
| 스포츠/레저 | 직접 | 상 | 요트장업 | `yacht_marinas` | 요트장과 해양 레저 관광 | [신청](https://www.data.go.kr/data/15155061/openapi.do) | `files.iter_yacht_marinas()` |
| 스포츠/레저 | 간접 | 중 | 수영장업 | `swimming_pools` | 수영장과 가족·실내 레저 | [신청](https://www.data.go.kr/data/15155038/openapi.do) | `files.iter_swimming_pools()` |
| 스포츠/레저 | 간접 | 중 | 빙상장업 | `ice_rinks` | 빙상장과 계절형 실내 레저 | [신청](https://www.data.go.kr/data/15155033/openapi.do) | `files.iter_ice_rinks()` |
| 스포츠/레저 | 간접 | 보조 | 당구장업 | `billiard_halls` | 당구장과 도시형 실내 여가 | [신청](https://www.data.go.kr/data/15155011/openapi.do) | `files.iter_billiard_halls()` |
| 스포츠/레저 | 간접 | 중 | 등록체육시설업 | `registered_sports_facilities` | 등록체육시설과 스포츠 관광 기반 | [신청](https://www.data.go.kr/data/15155018/openapi.do) | `files.iter_registered_sports_facilities()` |
| 스포츠/레저 | 간접 | 보조 | 무도장업 | `dance_halls` | 무도장과 야간·실내 여가 참고 | [신청](https://www.data.go.kr/data/15155022/openapi.do) | `files.iter_dance_halls()` |
| 스포츠/레저 | 간접 | 중 | 종합체육시설업 | `comprehensive_sports_facilities` | 종합체육시설과 스포츠 이벤트 입지 | [신청](https://www.data.go.kr/data/15155071/openapi.do) | `files.iter_comprehensive_sports_facilities()` |
| 생활편의 | 편의 | 보조 | 체력단련장업 | `fitness_centers` | 장기 체류 여행자의 운동 편의 | [신청](https://www.data.go.kr/data/15155077/openapi.do) | `files.iter_fitness_centers()` |
| 생활편의 | 편의 | 중 | 목욕장업 | `public_baths` | 목욕장·사우나와 여행 중 휴식 편의 | [신청](https://www.data.go.kr/data/15155091/openapi.do) | `files.iter_public_baths()` |
| 쇼핑/생활 | 간접 | 상 | 대규모점포 | `large_scale_retail_stores` | 대규모점포와 쇼핑 관광·생활 편의 | [신청](https://www.data.go.kr/data/15154948/openapi.do) | `files.iter_large_scale_retail_stores()` |
| 쇼핑/생활 | 편의 | 보조 | 미용업 | `beauty_salons` | 미용 서비스와 장기 체류 편의 | [신청](https://www.data.go.kr/data/15154918/openapi.do) | `files.iter_beauty_salons()` |
| 쇼핑/생활 | 편의 | 보조 | 이용업 | `barber_shops` | 이용업과 장기 체류 생활 편의 | [신청](https://www.data.go.kr/data/15154922/openapi.do) | `files.iter_barber_shops()` |
| 쇼핑/생활 | 편의 | 중 | 세탁업 | `laundries` | 세탁업과 장기 체류·캠핑 여행 편의 | [신청](https://www.data.go.kr/data/15154927/openapi.do) | `files.iter_laundries()` |
| 이동/주유 | 편의 | 중 | 석유판매업 | `oil_retailers` | 렌터카·자차 여행 주유 편의 | [신청](https://www.data.go.kr/data/15155253/openapi.do) | `files.iter_oil_retailers()` |
| 이동/주유 | 편의 | 보조 | 석유및석유대체연료판매업체 | `petroleum_alt_fuel_retailers` | 대체연료 판매 지점과 차량 이동 편의 | [신청](https://www.data.go.kr/data/15155258/openapi.do) | `files.iter_petroleum_alt_fuel_retailers()` |
| 동반동물 | 편의 | 중 | 동물병원 | `animal_hospitals` | 반려동물 동반 여행 중 진료 거점 | [신청](https://www.data.go.kr/data/15154952/openapi.do) | `files.iter_animal_hospitals()` |
| 동반동물 | 편의 | 보조 | 동물약국 | `animal_pharmacies` | 반려동물 약품 구매 편의 | [신청](https://www.data.go.kr/data/15155272/openapi.do) | `files.iter_animal_pharmacies()` |
| 동반동물 | 편의 | 보조 | 동물위탁관리업 | `animal_boarding` | 반려동물 위탁관리와 여행 활동 보조 | [신청](https://www.data.go.kr/data/15155055/openapi.do) | `files.iter_animal_boarding()` |
| 동반동물 | 편의 | 보조 | 동물미용업 | `pet_grooming` | 반려동물 미용과 장기 체류 편의 | [신청](https://www.data.go.kr/data/15154944/openapi.do) | `files.iter_pet_grooming()` |

## 사용 예

```python
from mois import LocalDataFileClient

with LocalDataFileClient() as files:
    for record in files.iter_tourist_accommodations():
        point = record.coordinates.wgs84_point if record.coordinates else None
        print(record.business_name, point)
```

여러 업종을 한 DB에 넣을 때는 `service_slug`를 함께 저장해 업종을 구분합니다.

```python
from mois import LocalDataFileClient

TOURISM_SLUGS = [
    "tourist_accommodations",
    "lodgings",
    "tourist_restaurants",
    "pharmacies",
]

with LocalDataFileClient() as files:
    for slug in TOURISM_SLUGS:
        for record in files.iter(slug):
            print(slug, record.business_name)
```
