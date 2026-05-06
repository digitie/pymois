"""응답값과 CSV 값을 Python 타입으로 변환합니다."""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from .catalog import RESPONSE_FIELDS

KST = ZoneInfo("Asia/Seoul")

_DATE_RE = re.compile(r"^\d{4}-?\d{2}-?\d{2}$")
_DATETIME_RE = re.compile(r"^\d{4}-?\d{2}-?\d{2}(?:[ T]?\d{2}:?\d{2}:?\d{2})?$")

HEADER_ALIASES: dict[str, str] = {
    "좌표정보(X)": "CRD_INFO_X",
    "좌표정보(Y)": "CRD_INFO_Y",
    "전화번호": "TELNO",
    "총면적": "TOT_AR",
}


def strip_or_none(value: object) -> str | None:
    """빈 문자열과 공백을 `None`으로 정규화합니다."""

    if value is None:
        return None
    text = str(value).strip()
    return text or None


def field_for_header(header: str) -> str:
    """localdata CSV 한글 헤더를 공공데이터포털 응답변수명으로 매핑합니다."""

    if header in HEADER_ALIASES:
        return HEADER_ALIASES[header]
    for row in RESPONSE_FIELDS:
        if row.get("deleted"):
            continue
        if header in {row.get("name"), row.get("local_name")} and row.get("field"):
            return str(row["field"])
    return _fallback_header_name(header)


def convert_value(field: str, header: str, value: object) -> object:
    """필드 명세와 값 형태를 기준으로 안전하게 변환합니다."""

    text = strip_or_none(value)
    if text is None:
        return None

    if _is_datetime_field(field, header):
        parsed_datetime = to_datetime(text)
        return parsed_datetime if parsed_datetime is not None else text
    if _is_date_field(field, header):
        parsed_date = to_date(text)
        return parsed_date if parsed_date is not None else text
    if _is_numeric_field(field, header):
        parsed_number = to_number(text)
        return parsed_number if parsed_number is not None else text
    return text


def to_date(value: object) -> date | None:
    """YYYYMMDD 또는 YYYY-MM-DD 문자열을 `date`로 변환합니다."""

    text = strip_or_none(value)
    if text is None or not _DATE_RE.match(text):
        return None
    digits = text.replace("-", "")
    try:
        return date(int(digits[:4]), int(digits[4:6]), int(digits[6:8]))
    except ValueError:
        return None


def to_datetime(value: object) -> datetime | None:
    """YYYYMMDDHHMMSS 또는 YYYY-MM-DD HH:MM:SS 문자열을 KST datetime으로 변환합니다."""

    text = strip_or_none(value)
    if text is None or not _DATETIME_RE.match(text):
        return None
    digits = re.sub(r"\D", "", text)
    if len(digits) == 8:
        digits += "000000"
    if len(digits) != 14:
        return None
    try:
        return datetime(
            int(digits[:4]),
            int(digits[4:6]),
            int(digits[6:8]),
            int(digits[8:10]),
            int(digits[10:12]),
            int(digits[12:14]),
            tzinfo=KST,
        )
    except ValueError:
        return None


def to_number(value: object) -> int | float | None:
    """정수는 `int`, 소수는 `float`로 변환합니다."""

    text = strip_or_none(value)
    if text is None:
        return None
    try:
        number = Decimal(text.replace(",", ""))
    except InvalidOperation:
        return None
    if number == number.to_integral_value():
        return int(number)
    return float(number)


def _is_date_field(field: str, header: str) -> bool:
    if field.endswith("_YMD"):
        return True
    return "일자" in header and "시점" not in header


def _is_datetime_field(field: str, header: str) -> bool:
    if field.endswith("_PNT"):
        return True
    return "시점" in header


def _is_numeric_field(field: str, header: str) -> bool:
    if field in {"CRD_INFO_X", "CRD_INFO_Y"}:
        return True
    for row in RESPONSE_FIELDS:
        if row.get("field") == field and str(row.get("type") or "").upper() == "NUMBER":
            return True
    numeric_words = ("면적", "수", "좌표", "높이", "길이", "거리", "금액", "연면적")
    return any(word in header for word in numeric_words)


def _fallback_header_name(header: str) -> str:
    replacements = {
        "(": "_",
        ")": "",
        "/": "_",
        " ": "_",
        "-": "_",
    }
    result = header.strip()
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result
