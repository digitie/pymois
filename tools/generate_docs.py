"""카탈로그 기반 한국어 목록 문서를 생성합니다."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pymois.catalog import (  # noqa: E402
    FILE_DOWNLOADS,
    INCREMENTAL_OPENAPI_ENDPOINTS,
    OPENAPI_SERVICES,
    RESPONSE_FIELDS,
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
        "from pymois import ("
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
    lines.append("from pymois import MoisClient, list_incremental_openapi_endpoints")
    lines.append("")
    lines.append("client = MoisClient.from_env()")
    lines.append("")
    lines.append('changed = client.get_updated_hospitals("20260505000000")')
    lines.append("source_changed = client.get_updated_hospitals(")
    lines.append('    "20260505000000",')
    lines.append("    source_modified=True,")
    lines.append(")")
    lines.append("")
    lines.append("for api in list_incremental_openapi_endpoints():")
    lines.append("    print(api.service_slug, api.application_url, api.get_method)")
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
        "확인되는 생활편의정보는 13종이므로, `pymois`는 실제 확인된 208종만 "
        "카탈로그에 포함합니다."
    )
    lines.append("")
    lines.append("## 기본 사용")
    lines.append("")
    lines.append("```python")
    lines.append("from pymois import LocalDataFileClient")
    lines.append("")
    lines.append("files = LocalDataFileClient()")
    lines.append('records = files.load("hospitals")')
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
    lines.append("for record in files.iter_hospitals():")
    lines.append("    print(record.management_number, record.business_name)")
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
    lines.append('records = files.load("hospitals", org_code="3000000")')
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


def main() -> None:
    root = Path("docs")
    root.mkdir(exist_ok=True)
    write_api_list(root)
    write_incremental_openapi(root)
    write_response_fields(root)
    write_file_downloads(root)


if __name__ == "__main__":
    main()
