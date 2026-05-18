# 타입과 좌표 값 객체

`mois`는 외부 프로그램에서 안정적으로 재사용할 수 있도록 공개 enum, 타입 별칭, 좌표 값 객체를 제공합니다. 기존 `Coordinate.x`, `Coordinate.y`, `Coordinate.lon`, `Coordinate.lat` 접근은 그대로 유지합니다.

## 좌표 순서 원칙

- KATEC/EPSG:5174 좌표는 항상 `(x, y)` 순서입니다.
- WGS84/EPSG:4326 좌표는 항상 `(lon, lat)` 순서입니다.
- GeoJSON Position, WKT, SpatiaLite 입력도 WGS84일 때 `(lon, lat)`입니다.
- 위도/경도라고 말할 때도 코드에서는 `lat, lon` 순서로 넘기지 않습니다.

## 좌표 값 객체

### `KatecPoint`

localdata 원본 `좌표정보(X)`, `좌표정보(Y)`를 표현합니다.

```python
from mois import KatecPoint

katec = KatecPoint(199642.716240024, 452606.614384676)
print(katec.as_tuple())  # (x, y)
print(katec.katec_x, katec.katec_y)

wgs84 = katec.to_wgs84()
print(wgs84.lon, wgs84.lat)
```

### `Wgs84Point`

WGS84 경도/위도 좌표를 표현합니다. 생성자와 tuple 반환 순서는 항상 `(lon, lat)`입니다.

```python
from mois import Wgs84Point

point = Wgs84Point(lon=126.978, lat=37.5665)
print(point.as_tuple())             # (126.978, 37.5665)
print(point.to_geojson_position())  # (126.978, 37.5665)
print(point.to_wkt())               # POINT(126.978 37.5665)
```

`lon`은 -180~180, `lat`은 -90~90 범위를 벗어나면 `ValueError`를 발생시킵니다. 위도와 경도를 실수로 바꿔 넣는 경우를 빨리 찾기 위한 장치입니다.

### `StationCoordinates`

KATEC 원본 좌표와 WGS84 변환 좌표를 함께 담습니다. 기존 `station.katec_x`, `station.katec_y`, `station.lon`, `station.lat` 스타일 접근을 지원하면서 값 객체도 제공합니다.

```python
from mois import StationCoordinates

coords = StationCoordinates.from_katec(199642.716240024, 452606.614384676)

print(coords.katec_x, coords.katec_y)
print(coords.lon, coords.lat)
print(coords.katec_point.as_tuple())  # (x, y)
print(coords.wgs84_point.as_tuple())  # (lon, lat)
```

### `Coordinate`

기존 호환용 객체입니다. `x`, `y`, `lon`, `lat` 필드는 그대로 있고, 새 값 객체 접근자를 추가로 제공합니다.

```python
record = files.load_hospitals()[0]
coordinate = record.coordinates

print(coordinate.x, coordinate.y)               # 기존 호환
print(coordinate.lon, coordinate.lat)           # 기존 호환
print(coordinate.katec_point.as_tuple())        # (x, y)
print(coordinate.wgs84_point.as_tuple())        # (lon, lat)
print(coordinate.station_coordinates.to_wkt())  # WGS84 Point WKT
```

## 변환 helper

```python
from mois.coords import (
    epsg5174_to_wgs84,
    epsg5174_to_wgs84_point,
    station_coordinates_from_katec,
)

lon, lat = epsg5174_to_wgs84(199642.716240024, 452606.614384676)
point = epsg5174_to_wgs84_point(199642.716240024, 452606.614384676)
coords = station_coordinates_from_katec(199642.716240024, 452606.614384676)
```

`epsg5174_to_wgs84()`는 기존 호환을 위해 tuple을 반환하지만, 반환 순서는 명확히 `(lon, lat)`입니다.

## 공개 enum

| enum | 값 | 용도 |
|---|---|---|
| `CoordinateReferenceSystem` | `KATEC`, `WGS84` | 좌표계 명시 |
| `OpenApiKind` | `INFO`, `HISTORY` | OpenAPI 조회/이력조회 구분 |
| `FileDownloadKind` | `LICENSE`, `LIFE_CONVENIENCE` | 파일 다운로드 종류 |
| `ConditionOperator` | `EQ`, `NE`, `LT`, `LTE`, `GT`, `GTE`, `LIKE` | `cond[FIELD::OP]` 조건 연산자 |
| `SyncKind` | `INFO`, `HISTORY`, `FILE` | DB/배치 동기화 종류 |
| `BusinessStatusCategory` | `OPEN`, `CLOSED`, `UNKNOWN` | 영업상태 단순 분류 |

예시:

```python
from mois import Condition, ConditionOperator, OpenApiKind, list_openapi_endpoints

history = list_openapi_endpoints(kind=OpenApiKind.HISTORY)
condition = Condition("DAT_UPDT_PNT", ConditionOperator.GTE, "20260505000000")
```

`LocalDataRecord.status_category`는 `BusinessStatusCategory`를 반환합니다. 원본 코드/명은 `business_status_code`, `business_status_name`에 그대로 남깁니다.

## 공개 타입 별칭

| 타입 | 실제 타입 | 용도 |
|---|---|---|
| `ServiceSlug` | `str` | `hospitals` 같은 서비스 slug |
| `ManagementNumber` | `str` | 인허가 관리번호 |
| `OpenApiItem` | `Mapping[str, Any]` | OpenAPI item |
| `LocalDataRow` | `Mapping[str, Any]` | 변환된 localdata 행 |

런타임 동작을 바꾸지는 않지만, 외부 프로그램이 타입 힌트를 붙일 때 의도를 드러내는 데 사용합니다.
