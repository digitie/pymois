"""다운로드된 localdata 파일을 DB 브라우저용 SQLite 테이블에 적재하는 CLI."""

from __future__ import annotations

import argparse
import os
from collections.abc import Iterable
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from mois import (
    LocalDataRecord,
    bulk_upsert_places,
    compact_json_dumps,
    create_sqlite_schema,
)
from mois.files import iter_records_from_binary


def sqlite_url(path: str | os.PathLike[str]) -> str:
    """Windows 경로를 포함한 파일 경로를 SQLAlchemy SQLite URL로 변환합니다."""

    actual_path = Path(path)
    actual_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{actual_path.resolve().as_posix()}"


def load_download_file_to_sqlite(
    *,
    database_path: str | os.PathLike[str],
    file_path: str | os.PathLike[str],
    slug: str,
    batch_size: int = 1000,
    replace_slug: bool = False,
    load_spatialite: bool = True,
) -> int:
    """다운로드된 CSV/ZIP 파일 하나를 SQLite DB에 적재합니다."""

    engine = create_engine(
        sqlite_url(database_path),
        pool_pre_ping=True,
        json_serializer=compact_json_dumps,
    )
    create_sqlite_schema(engine, load_spatialite=load_spatialite)
    if replace_slug:
        delete_slug(engine, slug)

    with Path(file_path).open("rb") as source, Session(engine) as session:
        return load_records_to_sqlite(
            session,
            iter_records_from_binary(source, slug=slug),
            batch_size=batch_size,
        )


def load_records_to_sqlite(
    session: Session,
    records: Iterable[LocalDataRecord],
    *,
    batch_size: int = 1000,
) -> int:
    """레코드 스트림을 배치 UPSERT하고 배치 단위로 커밋합니다."""

    if batch_size < 1:
        raise ValueError("batch_size must be greater than 0")

    count = 0
    batch: list[LocalDataRecord] = []
    for record in records:
        batch.append(record)
        count += 1
        if len(batch) >= batch_size:
            _bulk_upsert_places(session, batch)
            session.commit()
            batch = []

    if batch:
        _bulk_upsert_places(session, batch)
        session.commit()
    return count


def delete_slug(engine: Engine, slug: str) -> None:
    """재적재 전 특정 업종의 기존 마스터/상세 데이터를 삭제합니다."""

    with engine.begin() as connection:
        connection.execute(
            text("delete from mois_place_master where service_slug = :slug"),
            {"slug": slug},
        )


def _bulk_upsert_places(session: Session, records: list[LocalDataRecord]) -> None:
    bulk_upsert_places(session, records)


def main() -> None:
    """명령행 진입점."""

    parser = argparse.ArgumentParser(
        description="다운로드된 localdata CSV/ZIP 파일을 mois SQLite 테이블에 적재합니다.",
    )
    parser.add_argument("--file", required=True, help="다운로드된 CSV/ZIP 파일 경로")
    parser.add_argument("--slug", required=True, help="파일 카탈로그 slug")
    parser.add_argument(
        "--database-path",
        default=os.getenv("MOIS_SQLITE_PATH"),
        help="SQLite DB 파일 경로. 기본값은 MOIS_SQLITE_PATH 환경변수입니다.",
    )
    parser.add_argument("--batch-size", type=int, default=1000, help="커밋 배치 크기")
    parser.add_argument("--replace-slug", action="store_true", help="같은 slug 데이터를 먼저 삭제")
    parser.add_argument(
        "--skip-spatialite",
        action="store_true",
        help="SpatiaLite 확장 로드를 건너뛰고 일반 SQLite 컬럼만 사용",
    )
    args = parser.parse_args()

    if not args.database_path:
        parser.error("--database-path 또는 MOIS_SQLITE_PATH가 필요합니다")

    count = load_download_file_to_sqlite(
        database_path=args.database_path,
        file_path=args.file,
        slug=args.slug,
        batch_size=args.batch_size,
        replace_slug=args.replace_slug,
        load_spatialite=not args.skip_spatialite,
    )
    print(f"loaded={count} slug={args.slug} file={args.file}")


if __name__ == "__main__":
    main()
