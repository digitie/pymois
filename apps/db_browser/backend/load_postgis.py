"""다운로드된 localdata 파일을 DB 브라우저용 PostGIS 테이블에 적재하는 CLI."""

from __future__ import annotations

import argparse
import os
from collections.abc import Iterable
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pymois import LocalDataRecord, create_postgis_schema, upsert_place
from pymois.files import iter_records_from_binary


def load_download_file_to_postgis(
    *,
    database_url: str,
    file_path: str | os.PathLike[str],
    slug: str,
    batch_size: int = 1000,
    replace_slug: bool = False,
    create_extension: bool = True,
) -> int:
    """다운로드된 CSV/ZIP 파일 하나를 PostGIS DB에 적재합니다."""

    engine = create_engine(database_url, pool_pre_ping=True)
    create_postgis_schema(engine, create_extension=create_extension)
    if replace_slug:
        delete_slug(engine, slug)

    with Path(file_path).open("rb") as source, Session(engine) as session:
        return load_records_to_postgis(
            session,
            iter_records_from_binary(source, slug=slug),
            batch_size=batch_size,
        )


def load_records_to_postgis(
    session: Session,
    records: Iterable[LocalDataRecord],
    *,
    batch_size: int = 1000,
) -> int:
    """레코드 스트림을 순차 UPSERT하고 배치 단위로 커밋합니다."""

    if batch_size < 1:
        raise ValueError("batch_size must be greater than 0")

    count = 0
    has_pending = False
    for record in records:
        upsert_place(session, record)
        count += 1
        has_pending = True
        if count % batch_size == 0:
            session.commit()
            has_pending = False

    if has_pending:
        session.commit()
    return count


def delete_slug(engine: Engine, slug: str) -> None:
    """재적재 전 특정 업종의 기존 마스터/상세 데이터를 삭제합니다."""

    with engine.begin() as connection:
        connection.execute(
            text("delete from mois_place_master where service_slug = :slug"),
            {"slug": slug},
        )


def main() -> None:
    """명령행 진입점."""

    parser = argparse.ArgumentParser(
        description="다운로드된 localdata CSV/ZIP 파일을 pymois PostGIS 테이블에 적재합니다.",
    )
    parser.add_argument("--file", required=True, help="다운로드된 CSV/ZIP 파일 경로")
    parser.add_argument("--slug", required=True, help="파일 카탈로그 slug")
    parser.add_argument(
        "--database-url",
        default=os.getenv("MOIS_DATABASE_URL"),
        help="SQLAlchemy DB URL. 기본값은 MOIS_DATABASE_URL 환경변수입니다.",
    )
    parser.add_argument("--batch-size", type=int, default=1000, help="커밋 배치 크기")
    parser.add_argument("--replace-slug", action="store_true", help="같은 slug 데이터를 먼저 삭제")
    parser.add_argument(
        "--skip-create-extension",
        action="store_true",
        help="PostGIS 확장 생성 권한이 없을 때 사용",
    )
    args = parser.parse_args()

    if not args.database_url:
        parser.error("--database-url 또는 MOIS_DATABASE_URL이 필요합니다")

    count = load_download_file_to_postgis(
        database_url=args.database_url,
        file_path=args.file,
        slug=args.slug,
        batch_size=args.batch_size,
        replace_slug=args.replace_slug,
        create_extension=not args.skip_create_extension,
    )
    print(f"loaded={count} slug={args.slug} file={args.file}")


if __name__ == "__main__":
    main()
