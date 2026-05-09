"""개발용 DB 브라우저 서버 실행 진입점."""

from __future__ import annotations

import os

import uvicorn

from .app import create_app


def main() -> None:
    """환경변수 기반으로 FastAPI 개발 서버를 실행합니다."""

    host = os.getenv("MOIS_WEB_HOST", "127.0.0.1")
    port = int(os.getenv("MOIS_WEB_PORT", "8000"))
    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
    main()
