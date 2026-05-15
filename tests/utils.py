from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def remove_fields(obj: Any, exclude_fields: list[str]) -> Any:
    if isinstance(obj, Mapping):
        return {
            key: remove_fields(value, exclude_fields)
            for key, value in obj.items()
            if key not in exclude_fields
        }
    if isinstance(obj, list):
        return [remove_fields(value, exclude_fields) for value in obj]
    return obj


def assert_case(actual: Any, expected: Any, assertion: Mapping[str, Any]) -> None:
    mode = assertion.get("mode", "snapshot")

    if mode == "snapshot":
        exclude_fields = [str(field) for field in assertion.get("exclude_fields", [])]
        assert remove_fields(actual, exclude_fields) == remove_fields(expected, exclude_fields)
    elif mode == "required_fields":
        for field in assertion.get("required_fields", []):
            assert _has_field(actual, str(field))
    elif mode == "schema_only":
        assert actual is not None
    elif mode == "count":
        assert _count(actual) == _count(expected)
    else:
        raise ValueError(f"Unknown assertion mode: {mode}")


def _has_field(obj: Any, field: str) -> bool:
    if isinstance(obj, Mapping):
        return field in obj or any(_has_field(value, field) for value in obj.values())
    if isinstance(obj, list):
        return any(_has_field(value, field) for value in obj)
    return False


def _count(obj: Any) -> int | None:
    if isinstance(obj, Mapping):
        value = obj.get("count")
        return int(value) if value is not None else None
    if isinstance(obj, list):
        return len(obj)
    return None
