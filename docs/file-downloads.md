# 파일 다운로드와 로드 API

localdata 파일 다운로드는 인허가정보 195개 업종을 대상으로 제공합니다. 파일은 CP949 CSV로 내려오며, 로더는 날짜, 시각, 숫자, EPSG:5174 좌표를 Python 타입과 WGS84 좌표로 변환합니다.

참고 PDF는 인허가정보 195종과 생활편의정보 14종, 총 209종을 언급합니다. 다만 2026년 5월 6일 현재 `file.localdata.go.kr`의 파일 다운로드 카탈로그에서 확인되는 생활편의정보는 13종이므로, `mois`는 실제 확인된 208종만 카탈로그에 포함합니다.

## 기본 사용

```python
from mois import LocalDataFileClient

with LocalDataFileClient() as files:
    records = files.load("hospitals")

first = records[0]
print(first.business_name)
print(first.license_date)
print(first.coordinates.lon, first.coordinates.lat)
print(first.coordinates.wgs84_point.as_tuple())  # (lon, lat)
```

대용량 업종은 전체 목록을 메모리에 올리는 `load()`보다 스트리밍 API를 사용합니다.

```python
with LocalDataFileClient() as files:
    for record in files.iter_hospitals():
        print(record.management_number, record.business_name)
```

asyncio 환경에서는 `aio()`를 사용합니다.

```python
import asyncio

from mois import LocalDataFileClient


async def main():
    async with LocalDataFileClient.aio() as files:
        records = await files.load("hospitals")
        print(records[0].business_name)

        async for record in files.iter_hospitals():
            print(record.management_number, record.business_name)
            break


asyncio.run(main())
```

## 지역별 다운로드

지역별 파일은 localdata의 `orgCode`를 그대로 전달합니다. 예: 서울종로구 `3000000`.

```python
with LocalDataFileClient() as files:
    records = files.load("hospitals", org_code="3000000")
```

## 변환 규칙

| 원본 | 변환 |
|---|---|
| `인허가일자`, `폐업일자` 등 일자 | `datetime.date` |
| `데이터갱신시점`, `최종수정시점` | KST timezone-aware `datetime.datetime` |
| `NUMBER` 필드와 면적/수량 계열 | `int` 또는 `float` |
| `좌표정보(X/Y)` | 원본 `CRD_INFO_X/Y` float + `WGS84_LON/LAT` + `Coordinate`, `KatecPoint`, `Wgs84Point` 값 객체 |
| 빈 문자열/공백 | `None` |

좌표 순서는 KATEC/EPSG:5174가 `(x, y)`, WGS84/EPSG:4326이 `(lon, lat)`입니다. 자세한 타입은 [타입과 좌표 값 객체](types-and-coordinates.md)를 봅니다.

## 전체 다운로드 함수 목록

| 분류 | 업종 | slug | 로드 함수 | 스트리밍 함수 | 다운로드 함수 |
|---|---|---|---|---|---|
| 건강 | 병원 | `hospitals` | `files.load_hospitals()` | `files.iter_hospitals()` | `files.download_hospitals(path)` |
| 건강 | 부속의료기관 | `affiliated_medical_institutions` | `files.load_affiliated_medical_institutions()` | `files.iter_affiliated_medical_institutions()` | `files.download_affiliated_medical_institutions(path)` |
| 건강 | 산후조리업 | `postpartum_care` | `files.load_postpartum_care()` | `files.iter_postpartum_care()` | `files.download_postpartum_care(path)` |
| 건강 | 안전상비의약품 판매업소 | `over_the_counter_medicine_stores` | `files.load_over_the_counter_medicine_stores()` | `files.iter_over_the_counter_medicine_stores()` | `files.download_over_the_counter_medicine_stores(path)` |
| 건강 | 약국 | `pharmacies` | `files.load_pharmacies()` | `files.iter_pharmacies()` | `files.download_pharmacies(path)` |
| 건강 | 응급환자이송업 | `emergency_patient_transport` | `files.load_emergency_patient_transport()` | `files.iter_emergency_patient_transport()` | `files.download_emergency_patient_transport(path)` |
| 건강 | 의료법인 | `medical_corporations` | `files.load_medical_corporations()` | `files.iter_medical_corporations()` | `files.download_medical_corporations(path)` |
| 건강 | 의료유사업 | `medical_related_businesses` | `files.load_medical_related_businesses()` | `files.iter_medical_related_businesses()` | `files.download_medical_related_businesses(path)` |
| 건강 | 의원 | `clinics` | `files.load_clinics()` | `files.iter_clinics()` | `files.download_clinics(path)` |
| 건강 | 안경업 | `optical_shops` | `files.load_optical_shops()` | `files.iter_optical_shops()` | `files.download_optical_shops(path)` |
| 건강 | 의료기기수리업 | `medical_device_repair` | `files.load_medical_device_repair()` | `files.iter_medical_device_repair()` | `files.download_medical_device_repair(path)` |
| 건강 | 의료기기판매(임대)업 | `medical_device_sales_rental` | `files.load_medical_device_sales_rental()` | `files.iter_medical_device_sales_rental()` | `files.download_medical_device_sales_rental(path)` |
| 건강 | 치과기공소 | `dental_labs` | `files.load_dental_labs()` | `files.iter_dental_labs()` | `files.download_dental_labs(path)` |
| 동물 | 동물미용업 | `pet_grooming` | `files.load_pet_grooming()` | `files.iter_pet_grooming()` | `files.download_pet_grooming(path)` |
| 동물 | 동물병원 | `animal_hospitals` | `files.load_animal_hospitals()` | `files.iter_animal_hospitals()` | `files.download_animal_hospitals(path)` |
| 동물 | 동물생산업 | `animal_breeding` | `files.load_animal_breeding()` | `files.iter_animal_breeding()` | `files.download_animal_breeding(path)` |
| 동물 | 동물수입업 | `animal_import` | `files.load_animal_import()` | `files.iter_animal_import()` | `files.download_animal_import(path)` |
| 동물 | 동물약국 | `animal_pharmacies` | `files.load_animal_pharmacies()` | `files.iter_animal_pharmacies()` | `files.download_animal_pharmacies(path)` |
| 동물 | 동물용의료용구판매업 | `veterinary_medical_equipment_sales` | `files.load_veterinary_medical_equipment_sales()` | `files.iter_veterinary_medical_equipment_sales()` | `files.download_veterinary_medical_equipment_sales(path)` |
| 동물 | 동물용의약품도매상 | `veterinary_drug_wholesalers` | `files.load_veterinary_drug_wholesalers()` | `files.iter_veterinary_drug_wholesalers()` | `files.download_veterinary_drug_wholesalers(path)` |
| 동물 | 동물운송업 | `animal_transport` | `files.load_animal_transport()` | `files.iter_animal_transport()` | `files.download_animal_transport(path)` |
| 동물 | 동물위탁관리업 | `animal_boarding` | `files.load_animal_boarding()` | `files.iter_animal_boarding()` | `files.download_animal_boarding(path)` |
| 동물 | 동물장묘업 | `animal_cremation` | `files.load_animal_cremation()` | `files.iter_animal_cremation()` | `files.download_animal_cremation(path)` |
| 동물 | 동물전시업 | `animal_exhibition` | `files.load_animal_exhibition()` | `files.iter_animal_exhibition()` | `files.download_animal_exhibition(path)` |
| 동물 | 동물판매업 | `animal_sales` | `files.load_animal_sales()` | `files.iter_animal_sales()` | `files.download_animal_sales(path)` |
| 동물 | 가축사육업 | `livestock_farming` | `files.load_livestock_farming()` | `files.iter_livestock_farming()` | `files.download_livestock_farming(path)` |
| 동물 | 가축인공수정소 | `artificial_insemination_centers` | `files.load_artificial_insemination_centers()` | `files.iter_artificial_insemination_centers()` | `files.download_artificial_insemination_centers(path)` |
| 동물 | 도축업 | `slaughterhouses` | `files.load_slaughterhouses()` | `files.iter_slaughterhouses()` | `files.download_slaughterhouses(path)` |
| 동물 | 부화업 | `hatcheries` | `files.load_hatcheries()` | `files.iter_hatcheries()` | `files.download_hatcheries(path)` |
| 동물 | 사료제조업 | `feed_manufacturers` | `files.load_feed_manufacturers()` | `files.iter_feed_manufacturers()` | `files.download_feed_manufacturers(path)` |
| 동물 | 종축업 | `breeding_stock_businesses` | `files.load_breeding_stock_businesses()` | `files.iter_breeding_stock_businesses()` | `files.download_breeding_stock_businesses(path)` |
| 문화 | 게임물배급업 | `game_distributors` | `files.load_game_distributors()` | `files.iter_game_distributors()` | `files.download_game_distributors(path)` |
| 문화 | 게임물제작업 | `game_producers` | `files.load_game_producers()` | `files.iter_game_producers()` | `files.download_game_producers(path)` |
| 문화 | 복합영상물제공업 | `mixed_video_content_providers` | `files.load_mixed_video_content_providers()` | `files.iter_mixed_video_content_providers()` | `files.download_mixed_video_content_providers(path)` |
| 문화 | 복합유통게임제공업 | `mixed_game_providers` | `files.load_mixed_game_providers()` | `files.iter_mixed_game_providers()` | `files.download_mixed_game_providers(path)` |
| 문화 | 인터넷컴퓨터게임시설제공업 | `pc_bangs` | `files.load_pc_bangs()` | `files.iter_pc_bangs()` | `files.download_pc_bangs(path)` |
| 문화 | 일반게임제공업 | `general_game_providers` | `files.load_general_game_providers()` | `files.iter_general_game_providers()` | `files.download_general_game_providers(path)` |
| 문화 | 청소년게임제공업 | `youth_game_providers` | `files.load_youth_game_providers()` | `files.iter_youth_game_providers()` | `files.download_youth_game_providers(path)` |
| 문화 | 공연장 | `performance_halls` | `files.load_performance_halls()` | `files.iter_performance_halls()` | `files.download_performance_halls(path)` |
| 문화 | 관광공연장업 | `tourist_performance_halls` | `files.load_tourist_performance_halls()` | `files.iter_tourist_performance_halls()` | `files.download_tourist_performance_halls(path)` |
| 문화 | 관광극장유흥업 | `tourist_theater_entertainment` | `files.load_tourist_theater_entertainment()` | `files.iter_tourist_theater_entertainment()` | `files.download_tourist_theater_entertainment(path)` |
| 문화 | 관광궤도업 | `tourist_railways` | `files.load_tourist_railways()` | `files.iter_tourist_railways()` | `files.download_tourist_railways(path)` |
| 문화 | 관광사업자 | `tourism_businesses` | `files.load_tourism_businesses()` | `files.iter_tourism_businesses()` | `files.download_tourism_businesses(path)` |
| 문화 | 관광유람선업 | `tourist_cruises` | `files.load_tourist_cruises()` | `files.iter_tourist_cruises()` | `files.download_tourist_cruises(path)` |
| 문화 | 국제회의시설업 | `international_convention_facilities` | `files.load_international_convention_facilities()` | `files.iter_international_convention_facilities()` | `files.download_international_convention_facilities(path)` |
| 문화 | 박물관 및 미술관 | `museums_and_art_galleries` | `files.load_museums_and_art_galleries()` | `files.iter_museums_and_art_galleries()` | `files.download_museums_and_art_galleries(path)` |
| 문화 | 시내순환관광업 | `city_tour_businesses` | `files.load_city_tour_businesses()` | `files.iter_city_tour_businesses()` | `files.download_city_tour_businesses(path)` |
| 문화 | 테마파크업(기타) | `amusement_facilities_other` | `files.load_amusement_facilities_other()` | `files.iter_amusement_facilities_other()` | `files.download_amusement_facilities_other(path)` |
| 문화 | 일반테마파크업 | `general_amusement_facilities` | `files.load_general_amusement_facilities()` | `files.iter_general_amusement_facilities()` | `files.download_general_amusement_facilities(path)` |
| 문화 | 전문휴양업 | `special_resorts` | `files.load_special_resorts()` | `files.iter_special_resorts()` | `files.download_special_resorts(path)` |
| 문화 | 전통사찰 | `traditional_temples` | `files.load_traditional_temples()` | `files.iter_traditional_temples()` | `files.download_traditional_temples(path)` |
| 문화 | 종합테마파크업 | `comprehensive_amusement_facilities` | `files.load_comprehensive_amusement_facilities()` | `files.iter_comprehensive_amusement_facilities()` | `files.download_comprehensive_amusement_facilities(path)` |
| 문화 | 종합휴양업 | `comprehensive_resorts` | `files.load_comprehensive_resorts()` | `files.iter_comprehensive_resorts()` | `files.download_comprehensive_resorts(path)` |
| 문화 | 지방문화원 | `local_culture_centers` | `files.load_local_culture_centers()` | `files.iter_local_culture_centers()` | `files.download_local_culture_centers(path)` |
| 문화 | 국제회의기획업 | `international_convention_planners` | `files.load_international_convention_planners()` | `files.iter_international_convention_planners()` | `files.download_international_convention_planners(path)` |
| 문화 | 대중문화예술기획업 | `pop_culture_art_planners` | `files.load_pop_culture_art_planners()` | `files.iter_pop_culture_art_planners()` | `files.download_pop_culture_art_planners(path)` |
| 문화 | 문화예술법인 | `cultural_art_corporations` | `files.load_cultural_art_corporations()` | `files.iter_cultural_art_corporations()` | `files.download_cultural_art_corporations(path)` |
| 문화 | 노래연습장업 | `karaoke_rooms` | `files.load_karaoke_rooms()` | `files.iter_karaoke_rooms()` | `files.download_karaoke_rooms(path)` |
| 문화 | 비디오물감상실업 | `video_viewing_rooms` | `files.load_video_viewing_rooms()` | `files.iter_video_viewing_rooms()` | `files.download_video_viewing_rooms(path)` |
| 문화 | 비디오물배급업 | `video_distributors` | `files.load_video_distributors()` | `files.iter_video_distributors()` | `files.download_video_distributors(path)` |
| 문화 | 비디오물소극장업 | `video_mini_theaters` | `files.load_video_mini_theaters()` | `files.iter_video_mini_theaters()` | `files.download_video_mini_theaters(path)` |
| 문화 | 비디오물시청제공업 | `video_streaming_providers` | `files.load_video_streaming_providers()` | `files.iter_video_streaming_providers()` | `files.download_video_streaming_providers(path)` |
| 문화 | 비디오물제작업 | `video_producers` | `files.load_video_producers()` | `files.iter_video_producers()` | `files.download_video_producers(path)` |
| 문화 | 관광숙박업 | `tourist_accommodations` | `files.load_tourist_accommodations()` | `files.iter_tourist_accommodations()` | `files.download_tourist_accommodations(path)` |
| 문화 | 관광펜션업 | `tourist_pensions` | `files.load_tourist_pensions()` | `files.iter_tourist_pensions()` | `files.download_tourist_pensions(path)` |
| 문화 | 농어촌민박업 | `rural_homestays` | `files.load_rural_homestays()` | `files.iter_rural_homestays()` | `files.download_rural_homestays(path)` |
| 문화 | 숙박업 | `lodgings` | `files.load_lodgings()` | `files.iter_lodgings()` | `files.download_lodgings(path)` |
| 문화 | 외국인관광도시민박업 | `foreigner_city_homestays` | `files.load_foreigner_city_homestays()` | `files.iter_foreigner_city_homestays()` | `files.download_foreigner_city_homestays(path)` |
| 문화 | 일반야영장업 | `general_campgrounds` | `files.load_general_campgrounds()` | `files.iter_general_campgrounds()` | `files.download_general_campgrounds(path)` |
| 문화 | 자동차야영장업 | `auto_campgrounds` | `files.load_auto_campgrounds()` | `files.iter_auto_campgrounds()` | `files.download_auto_campgrounds(path)` |
| 문화 | 한옥체험업 | `hanok_experience` | `files.load_hanok_experience()` | `files.iter_hanok_experience()` | `files.download_hanok_experience(path)` |
| 문화 | 국내여행업 | `domestic_travel_agencies` | `files.load_domestic_travel_agencies()` | `files.iter_domestic_travel_agencies()` | `files.download_domestic_travel_agencies(path)` |
| 문화 | 국내외여행업 | `domestic_international_travel_agencies` | `files.load_domestic_international_travel_agencies()` | `files.iter_domestic_international_travel_agencies()` | `files.download_domestic_international_travel_agencies(path)` |
| 문화 | 종합여행업 | `comprehensive_travel_agencies` | `files.load_comprehensive_travel_agencies()` | `files.iter_comprehensive_travel_agencies()` | `files.download_comprehensive_travel_agencies(path)` |
| 문화 | 영화배급업 | `film_distributors` | `files.load_film_distributors()` | `files.iter_film_distributors()` | `files.download_film_distributors(path)` |
| 문화 | 영화상영관 | `movie_theaters` | `files.load_movie_theaters()` | `files.iter_movie_theaters()` | `files.download_movie_theaters(path)` |
| 문화 | 영화상영업 | `film_screenings` | `files.load_film_screenings()` | `files.iter_film_screenings()` | `files.download_film_screenings(path)` |
| 문화 | 영화수입업 | `film_importers` | `files.load_film_importers()` | `files.iter_film_importers()` | `files.download_film_importers(path)` |
| 문화 | 영화제작업 | `film_producers` | `files.load_film_producers()` | `files.iter_film_producers()` | `files.download_film_producers(path)` |
| 문화 | 온라인음악서비스제공업 | `online_music_services` | `files.load_online_music_services()` | `files.iter_online_music_services()` | `files.download_online_music_services(path)` |
| 문화 | 음반및음악영상물배급업 | `music_video_distributors` | `files.load_music_video_distributors()` | `files.iter_music_video_distributors()` | `files.download_music_video_distributors(path)` |
| 문화 | 음반및음악영상물제작업 | `music_video_producers` | `files.load_music_video_producers()` | `files.iter_music_video_producers()` | `files.download_music_video_producers(path)` |
| 문화 | 음반물배급업 | `record_distributors` | `files.load_record_distributors()` | `files.iter_record_distributors()` | `files.download_record_distributors(path)` |
| 문화 | 음반물제작업 | `record_producers` | `files.load_record_producers()` | `files.iter_record_producers()` | `files.download_record_producers(path)` |
| 생활 | 미용업 | `beauty_salons` | `files.load_beauty_salons()` | `files.iter_beauty_salons()` | `files.download_beauty_salons(path)` |
| 생활 | 이용업 | `barber_shops` | `files.load_barber_shops()` | `files.iter_barber_shops()` | `files.download_barber_shops(path)` |
| 생활 | 세탁업 | `laundries` | `files.load_laundries()` | `files.iter_laundries()` | `files.download_laundries(path)` |
| 생활 | 의료기관세탁물처리업 | `medical_laundry` | `files.load_medical_laundry()` | `files.iter_medical_laundry()` | `files.download_medical_laundry(path)` |
| 생활 | 다단계판매업체 | `multilevel_marketing` | `files.load_multilevel_marketing()` | `files.iter_multilevel_marketing()` | `files.download_multilevel_marketing(path)` |
| 생활 | 대규모점포 | `large_scale_retail_stores` | `files.load_large_scale_retail_stores()` | `files.iter_large_scale_retail_stores()` | `files.download_large_scale_retail_stores(path)` |
| 생활 | 방문판매업 | `door_to_door_sales` | `files.load_door_to_door_sales()` | `files.iter_door_to_door_sales()` | `files.download_door_to_door_sales(path)` |
| 생활 | 전화권유판매업 | `telemarketing_sales` | `files.load_telemarketing_sales()` | `files.iter_telemarketing_sales()` | `files.download_telemarketing_sales(path)` |
| 생활 | 통신판매업 | `ecommerce_businesses` | `files.load_ecommerce_businesses()` | `files.iter_ecommerce_businesses()` | `files.download_ecommerce_businesses(path)` |
| 생활 | 후원방문판매업체 | `sponsored_door_to_door_sales` | `files.load_sponsored_door_to_door_sales()` | `files.iter_sponsored_door_to_door_sales()` | `files.download_sponsored_door_to_door_sales(path)` |
| 생활 | 골프연습장업 | `golf_practice_ranges` | `files.load_golf_practice_ranges()` | `files.iter_golf_practice_ranges()` | `files.download_golf_practice_ranges(path)` |
| 생활 | 골프장 | `golf_courses` | `files.load_golf_courses()` | `files.iter_golf_courses()` | `files.download_golf_courses(path)` |
| 생활 | 당구장업 | `billiard_halls` | `files.load_billiard_halls()` | `files.iter_billiard_halls()` | `files.download_billiard_halls(path)` |
| 생활 | 등록체육시설업 | `registered_sports_facilities` | `files.load_registered_sports_facilities()` | `files.iter_registered_sports_facilities()` | `files.download_registered_sports_facilities(path)` |
| 생활 | 무도장업 | `dance_halls` | `files.load_dance_halls()` | `files.iter_dance_halls()` | `files.download_dance_halls(path)` |
| 생활 | 무도학원업 | `dance_academies` | `files.load_dance_academies()` | `files.iter_dance_academies()` | `files.download_dance_academies(path)` |
| 생활 | 빙상장업 | `ice_rinks` | `files.load_ice_rinks()` | `files.iter_ice_rinks()` | `files.download_ice_rinks(path)` |
| 생활 | 수영장업 | `swimming_pools` | `files.load_swimming_pools()` | `files.iter_swimming_pools()` | `files.download_swimming_pools(path)` |
| 생활 | 스키장 | `ski_resorts` | `files.load_ski_resorts()` | `files.iter_ski_resorts()` | `files.download_ski_resorts(path)` |
| 생활 | 승마장업 | `horse_riding` | `files.load_horse_riding()` | `files.iter_horse_riding()` | `files.download_horse_riding(path)` |
| 생활 | 썰매장업 | `sledding` | `files.load_sledding()` | `files.iter_sledding()` | `files.download_sledding(path)` |
| 생활 | 요트장업 | `yacht_marinas` | `files.load_yacht_marinas()` | `files.iter_yacht_marinas()` | `files.download_yacht_marinas(path)` |
| 생활 | 종합체육시설업 | `comprehensive_sports_facilities` | `files.load_comprehensive_sports_facilities()` | `files.iter_comprehensive_sports_facilities()` | `files.download_comprehensive_sports_facilities(path)` |
| 생활 | 체력단련장업 | `fitness_centers` | `files.load_fitness_centers()` | `files.iter_fitness_centers()` | `files.download_fitness_centers(path)` |
| 생활 | 체육도장업 | `martial_arts_dojo` | `files.load_martial_arts_dojo()` | `files.iter_martial_arts_dojo()` | `files.download_martial_arts_dojo(path)` |
| 생활 | 목욕장업 | `public_baths` | `files.load_public_baths()` | `files.iter_public_baths()` | `files.download_public_baths(path)` |
| 식품 | 위탁급식영업 | `contract_catering` | `files.load_contract_catering()` | `files.iter_contract_catering()` | `files.download_contract_catering(path)` |
| 식품 | 집단급식소 | `group_meal_facilities` | `files.load_group_meal_facilities()` | `files.iter_group_meal_facilities()` | `files.download_group_meal_facilities(path)` |
| 식품 | 건강기능식품유통전문판매업 | `health_functional_food_specialty_retailers` | `files.load_health_functional_food_specialty_retailers()` | `files.iter_health_functional_food_specialty_retailers()` | `files.download_health_functional_food_specialty_retailers(path)` |
| 식품 | 건강기능식품일반판매업 | `health_functional_food_general_retailers` | `files.load_health_functional_food_general_retailers()` | `files.iter_health_functional_food_general_retailers()` | `files.download_health_functional_food_general_retailers(path)` |
| 식품 | 식용얼음판매업 | `edible_ice_retailers` | `files.load_edible_ice_retailers()` | `files.iter_edible_ice_retailers()` | `files.download_edible_ice_retailers(path)` |
| 식품 | 식육포장처리업 | `meat_packers` | `files.load_meat_packers()` | `files.iter_meat_packers()` | `files.download_meat_packers(path)` |
| 식품 | 식품냉동냉장업 | `food_freezing_refrigeration` | `files.load_food_freezing_refrigeration()` | `files.iter_food_freezing_refrigeration()` | `files.download_food_freezing_refrigeration(path)` |
| 식품 | 식품소분업 | `food_repackagers` | `files.load_food_repackagers()` | `files.iter_food_repackagers()` | `files.download_food_repackagers(path)` |
| 식품 | 식품운반업 | `food_transporters` | `files.load_food_transporters()` | `files.iter_food_transporters()` | `files.download_food_transporters(path)` |
| 식품 | 식품자동판매기업 | `food_vending_machines` | `files.load_food_vending_machines()` | `files.iter_food_vending_machines()` | `files.download_food_vending_machines(path)` |
| 식품 | 식품제조가공업 | `food_manufacturing_processors` | `files.load_food_manufacturing_processors()` | `files.iter_food_manufacturing_processors()` | `files.download_food_manufacturing_processors(path)` |
| 식품 | 식품첨가물제조업 | `food_additive_manufacturers` | `files.load_food_additive_manufacturers()` | `files.iter_food_additive_manufacturers()` | `files.download_food_additive_manufacturers(path)` |
| 식품 | 식품판매업(기타) | `other_food_retailers` | `files.load_other_food_retailers()` | `files.iter_other_food_retailers()` | `files.download_other_food_retailers(path)` |
| 식품 | 옹기류제조업 | `onggi_manufacturers` | `files.load_onggi_manufacturers()` | `files.iter_onggi_manufacturers()` | `files.download_onggi_manufacturers(path)` |
| 식품 | 용기및포장지제조업 | `container_packaging_manufacturers` | `files.load_container_packaging_manufacturers()` | `files.iter_container_packaging_manufacturers()` | `files.download_container_packaging_manufacturers(path)` |
| 식품 | 용기냉동기특정설비 | `container_refrigeration_equipment` | `files.load_container_refrigeration_equipment()` | `files.iter_container_refrigeration_equipment()` | `files.download_container_refrigeration_equipment(path)` |
| 식품 | 유통전문판매업 | `distribution_specialty_retailers` | `files.load_distribution_specialty_retailers()` | `files.iter_distribution_specialty_retailers()` | `files.download_distribution_specialty_retailers(path)` |
| 식품 | 제과점영업 | `bakeries` | `files.load_bakeries()` | `files.iter_bakeries()` | `files.download_bakeries(path)` |
| 식품 | 즉석판매제조가공업 | `instant_food_processors` | `files.load_instant_food_processors()` | `files.iter_instant_food_processors()` | `files.download_instant_food_processors(path)` |
| 식품 | 집단급식소식품판매업 | `group_meal_food_retailers` | `files.load_group_meal_food_retailers()` | `files.iter_group_meal_food_retailers()` | `files.download_group_meal_food_retailers(path)` |
| 식품 | 집유업 | `milk_collection` | `files.load_milk_collection()` | `files.iter_milk_collection()` | `files.download_milk_collection(path)` |
| 식품 | 축산가공업 | `livestock_processing` | `files.load_livestock_processing()` | `files.iter_livestock_processing()` | `files.download_livestock_processing(path)` |
| 식품 | 축산물보관업 | `livestock_storage` | `files.load_livestock_storage()` | `files.iter_livestock_storage()` | `files.download_livestock_storage(path)` |
| 식품 | 축산물운반업 | `livestock_transport` | `files.load_livestock_transport()` | `files.iter_livestock_transport()` | `files.download_livestock_transport(path)` |
| 식품 | 축산판매업 | `livestock_retail` | `files.load_livestock_retail()` | `files.iter_livestock_retail()` | `files.download_livestock_retail(path)` |
| 식품 | 단란주점영업 | `singing_bars` | `files.load_singing_bars()` | `files.iter_singing_bars()` | `files.download_singing_bars(path)` |
| 식품 | 유흥주점영업 | `entertainment_bars` | `files.load_entertainment_bars()` | `files.iter_entertainment_bars()` | `files.download_entertainment_bars(path)` |
| 식품 | 관광식당 | `tourist_restaurants` | `files.load_tourist_restaurants()` | `files.iter_tourist_restaurants()` | `files.download_tourist_restaurants(path)` |
| 식품 | 관광유흥음식점업 | `tourist_entertainment_restaurants` | `files.load_tourist_entertainment_restaurants()` | `files.iter_tourist_entertainment_restaurants()` | `files.download_tourist_entertainment_restaurants(path)` |
| 식품 | 외국인전용유흥음식점업 | `foreigners_entertainment_restaurants` | `files.load_foreigners_entertainment_restaurants()` | `files.iter_foreigners_entertainment_restaurants()` | `files.download_foreigners_entertainment_restaurants(path)` |
| 식품 | 일반음식점 | `general_restaurants` | `files.load_general_restaurants()` | `files.iter_general_restaurants()` | `files.download_general_restaurants(path)` |
| 식품 | 휴게음식점 | `rest_cafes` | `files.load_rest_cafes()` | `files.iter_rest_cafes()` | `files.download_rest_cafes(path)` |
| 자원환경 | 목재수입유통업 | `lumber_import_distribution` | `files.load_lumber_import_distribution()` | `files.iter_lumber_import_distribution()` | `files.download_lumber_import_distribution(path)` |
| 자원환경 | 원목생산업 | `log_production` | `files.load_log_production()` | `files.iter_log_production()` | `files.download_log_production(path)` |
| 자원환경 | 제재업 | `sawmills` | `files.load_sawmills()` | `files.iter_sawmills()` | `files.download_sawmills(path)` |
| 자원환경 | 계량기수리업 | `weighing_instrument_repair` | `files.load_weighing_instrument_repair()` | `files.iter_weighing_instrument_repair()` | `files.download_weighing_instrument_repair(path)` |
| 자원환경 | 계량기수입업 | `weighing_instrument_import` | `files.load_weighing_instrument_import()` | `files.iter_weighing_instrument_import()` | `files.download_weighing_instrument_import(path)` |
| 자원환경 | 계량기제조업 | `weighing_instrument_manufacturing` | `files.load_weighing_instrument_manufacturing()` | `files.iter_weighing_instrument_manufacturing()` | `files.download_weighing_instrument_manufacturing(path)` |
| 자원환경 | 계량기증명업 | `weighing_instrument_certification` | `files.load_weighing_instrument_certification()` | `files.iter_weighing_instrument_certification()` | `files.download_weighing_instrument_certification(path)` |
| 자원환경 | 고압가스업 | `high_pressure_gas` | `files.load_high_pressure_gas()` | `files.iter_high_pressure_gas()` | `files.download_high_pressure_gas(path)` |
| 자원환경 | 석연탄제조업 | `briquette_manufacturers` | `files.load_briquette_manufacturers()` | `files.iter_briquette_manufacturers()` | `files.download_briquette_manufacturers(path)` |
| 자원환경 | 석유및석유대체연료판매업체 | `petroleum_alt_fuel_retailers` | `files.load_petroleum_alt_fuel_retailers()` | `files.iter_petroleum_alt_fuel_retailers()` | `files.download_petroleum_alt_fuel_retailers(path)` |
| 자원환경 | 석유판매업 | `oil_retailers` | `files.load_oil_retailers()` | `files.iter_oil_retailers()` | `files.download_oil_retailers(path)` |
| 자원환경 | 액화석유가스용품제조업체 | `lpg_equipment_manufacturers` | `files.load_lpg_equipment_manufacturers()` | `files.iter_lpg_equipment_manufacturers()` | `files.download_lpg_equipment_manufacturers(path)` |
| 자원환경 | 일반도시가스업체 | `city_gas_companies` | `files.load_city_gas_companies()` | `files.iter_city_gas_companies()` | `files.download_city_gas_companies(path)` |
| 자원환경 | 전력기술감리업체 | `power_supervision_companies` | `files.load_power_supervision_companies()` | `files.iter_power_supervision_companies()` | `files.download_power_supervision_companies(path)` |
| 자원환경 | 전력기술설계업체 | `power_design_companies` | `files.load_power_design_companies()` | `files.iter_power_design_companies()` | `files.download_power_design_companies(path)` |
| 자원환경 | 특정고압가스업 | `specific_high_pressure_gas` | `files.load_specific_high_pressure_gas()` | `files.iter_specific_high_pressure_gas()` | `files.download_specific_high_pressure_gas(path)` |
| 자원환경 | 지하수시공업체 | `groundwater_construction` | `files.load_groundwater_construction()` | `files.iter_groundwater_construction()` | `files.download_groundwater_construction(path)` |
| 자원환경 | 지하수영향조사기관 | `groundwater_impact_assessment` | `files.load_groundwater_impact_assessment()` | `files.iter_groundwater_impact_assessment()` | `files.download_groundwater_impact_assessment(path)` |
| 자원환경 | 지하수정화업체 | `groundwater_remediation` | `files.load_groundwater_remediation()` | `files.iter_groundwater_remediation()` | `files.download_groundwater_remediation(path)` |
| 자원환경 | 가축분뇨수집운반업 | `manure_collection_transport` | `files.load_manure_collection_transport()` | `files.iter_manure_collection_transport()` | `files.download_manure_collection_transport(path)` |
| 자원환경 | 가축분뇨배출시설관리업(사업장) | `manure_facility_management` | `files.load_manure_facility_management()` | `files.iter_manure_facility_management()` | `files.download_manure_facility_management(path)` |
| 자원환경 | 개인하수처리시설관리업(사업장) | `small_sewage_facility_management` | `files.load_small_sewage_facility_management()` | `files.iter_small_sewage_facility_management()` | `files.download_small_sewage_facility_management(path)` |
| 자원환경 | 건물위생관리업 | `building_sanitation` | `files.load_building_sanitation()` | `files.iter_building_sanitation()` | `files.download_building_sanitation(path)` |
| 자원환경 | 건설폐기물처리업 | `construction_waste_disposal` | `files.load_construction_waste_disposal()` | `files.iter_construction_waste_disposal()` | `files.download_construction_waste_disposal(path)` |
| 자원환경 | 급수공사대행업 | `water_supply_agents` | `files.load_water_supply_agents()` | `files.iter_water_supply_agents()` | `files.download_water_supply_agents(path)` |
| 자원환경 | 단독정화조 및 오수처리시설설계시공업 | `septic_sewage_design_build` | `files.load_septic_sewage_design_build()` | `files.iter_septic_sewage_design_build()` | `files.download_septic_sewage_design_build(path)` |
| 자원환경 | 대기오염물질배출시설설치사업장 | `air_pollution_facility_installation` | `files.load_air_pollution_facility_installation()` | `files.iter_air_pollution_facility_installation()` | `files.download_air_pollution_facility_installation(path)` |
| 자원환경 | 배출가스전문정비사업자(확인검사대행자) | `emission_inspection_agencies` | `files.load_emission_inspection_agencies()` | `files.iter_emission_inspection_agencies()` | `files.download_emission_inspection_agencies(path)` |
| 자원환경 | 분뇨수집운반업 | `night_soil_collection_transport` | `files.load_night_soil_collection_transport()` | `files.iter_night_soil_collection_transport()` | `files.download_night_soil_collection_transport(path)` |
| 자원환경 | 소독업 | `disinfection_companies` | `files.load_disinfection_companies()` | `files.iter_disinfection_companies()` | `files.download_disinfection_companies(path)` |
| 자원환경 | 수질오염원설치시설(기타) | `water_pollution_source_other` | `files.load_water_pollution_source_other()` | `files.iter_water_pollution_source_other()` | `files.download_water_pollution_source_other(path)` |
| 자원환경 | 쓰레기종량제봉투판매업 | `pay_as_you_throw_bag_retailers` | `files.load_pay_as_you_throw_bag_retailers()` | `files.iter_pay_as_you_throw_bag_retailers()` | `files.download_pay_as_you_throw_bag_retailers(path)` |
| 자원환경 | 저수조청소업 | `water_tank_cleaning` | `files.load_water_tank_cleaning()` | `files.iter_water_tank_cleaning()` | `files.download_water_tank_cleaning(path)` |
| 자원환경 | 환경관리대행기관 | `environment_management_agencies` | `files.load_environment_management_agencies()` | `files.iter_environment_management_agencies()` | `files.download_environment_management_agencies(path)` |
| 자원환경 | 환경전문공사업 | `environment_contractors` | `files.load_environment_contractors()` | `files.iter_environment_contractors()` | `files.download_environment_contractors(path)` |
| 자원환경 | 환경측정대행업 | `environment_measurement_agencies` | `files.load_environment_measurement_agencies()` | `files.iter_environment_measurement_agencies()` | `files.download_environment_measurement_agencies(path)` |
| 자원환경 | 환경컨설팅회사 | `environment_consulting_companies` | `files.load_environment_consulting_companies()` | `files.iter_environment_consulting_companies()` | `files.download_environment_consulting_companies(path)` |
| 기타 | 옥외광고업 | `outdoor_advertising_companies` | `files.load_outdoor_advertising_companies()` | `files.iter_outdoor_advertising_companies()` | `files.download_outdoor_advertising_companies(path)` |
| 기타 | 인쇄사 | `printing_shops` | `files.load_printing_shops()` | `files.iter_printing_shops()` | `files.download_printing_shops(path)` |
| 기타 | 출판사 | `publishers` | `files.load_publishers()` | `files.iter_publishers()` | `files.download_publishers(path)` |
| 기타 | 담배도매업 | `tobacco_wholesalers` | `files.load_tobacco_wholesalers()` | `files.iter_tobacco_wholesalers()` | `files.download_tobacco_wholesalers(path)` |
| 기타 | 담배소매업 | `tobacco_retailers` | `files.load_tobacco_retailers()` | `files.iter_tobacco_retailers()` | `files.download_tobacco_retailers(path)` |
| 기타 | 담배수입판매업체 | `tobacco_import_retailers` | `files.load_tobacco_import_retailers()` | `files.iter_tobacco_import_retailers()` | `files.download_tobacco_import_retailers(path)` |
| 기타 | 국제물류주선업 | `international_logistics_forwarders` | `files.load_international_logistics_forwarders()` | `files.iter_international_logistics_forwarders()` | `files.download_international_logistics_forwarders(path)` |
| 기타 | 물류창고업체 | `logistics_warehouses` | `files.load_logistics_warehouses()` | `files.iter_logistics_warehouses()` | `files.download_logistics_warehouses(path)` |
| 기타 | 민방위급수시설 | `civil_defense_water_facilities` | `files.load_civil_defense_water_facilities()` | `files.iter_civil_defense_water_facilities()` | `files.download_civil_defense_water_facilities(path)` |
| 기타 | 상조업 | `funeral_service_providers` | `files.load_funeral_service_providers()` | `files.iter_funeral_service_providers()` | `files.download_funeral_service_providers(path)` |
| 기타 | 승강기유지관리업체 | `elevator_maintenance` | `files.load_elevator_maintenance()` | `files.iter_elevator_maintenance()` | `files.download_elevator_maintenance(path)` |
| 기타 | 승강기제조및수입업체 | `elevator_manufacturers_importers` | `files.load_elevator_manufacturers_importers()` | `files.iter_elevator_manufacturers_importers()` | `files.download_elevator_manufacturers_importers(path)` |
| 기타 | 요양보호사교육기관 | `caregiver_training` | `files.load_caregiver_training()` | `files.iter_caregiver_training()` | `files.download_caregiver_training(path)` |
| 기타 | 장례지도사 교육기관 | `funeral_director_training` | `files.load_funeral_director_training()` | `files.iter_funeral_director_training()` | `files.download_funeral_director_training(path)` |
| 기타 | 무료직업소개소 | `free_job_centers` | `files.load_free_job_centers()` | `files.iter_free_job_centers()` | `files.download_free_job_centers(path)` |
| 기타 | 유료직업소개소 | `paid_job_centers` | `files.load_paid_job_centers()` | `files.iter_paid_job_centers()` | `files.download_paid_job_centers(path)` |
