from __future__ import annotations

from typing import Any

from mois.parser import parse_openapi_payload
from mois.processor import process_openapi_response

RUNNERS: dict[str, dict[str, Any]] = {
    "openapi_request": {
        "parse": parse_openapi_payload,
        "process": process_openapi_response,
    },
}
