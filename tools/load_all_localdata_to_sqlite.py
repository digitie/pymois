"""전체 localdata 인허가 파일을 저장하고 SQLite/SpatiaLite DB에 적재하는 운영 스크립트."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Iterable, Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from apps.db_browser.backend.load_sqlite import (  # noqa: E402
    delete_slug,
    load_records_to_sqlite,
    sqlite_url,
)
from mois import (  # noqa: E402
    FileDownload,
    LocalDataFileClient,
    LocalDataRecord,
    compact_json_dumps,
    create_sqlite_schema,
    list_file_downloads,
    refresh_spatial_geometries,
)
from mois.files import iter_records_from_binary  # noqa: E402


def main() -> None:
    """명령행 진입점."""

    parser = argparse.ArgumentParser(
        description="전체 localdata 인허가 파일을 로컬에 저장하고 SQLite DB에 적재합니다.",
    )
    parser.add_argument(
        "--database-path",
        default=os.getenv("MOIS_SQLITE_PATH", "artifacts/mois.sqlite"),
        help="SQLite DB 파일 경로. 기본값은 MOIS_SQLITE_PATH 또는 artifacts/mois.sqlite입니다.",
    )
    parser.add_argument("--output-dir", default="artifacts/localdata", help="원본 파일 저장 경로")
    parser.add_argument(
        "--progress-path",
        default="artifacts/load_all_localdata_sqlite_progress.jsonl",
        help="진행 상황 JSONL 로그 경로",
    )
    parser.add_argument("--batch-size", type=int, default=1000, help="DB 커밋 배치 크기")
    parser.add_argument("--progress-every", type=int, default=10000, help="적재 진행 로그 간격")
    parser.add_argument("--timeout", type=float, default=60.0, help="다운로드 요청 timeout 초")
    parser.add_argument("--slug", action="append", help="특정 slug만 실행. 여러 번 지정 가능")
    parser.add_argument("--start-index", type=int, default=1, help="1부터 시작하는 시작 인덱스")
    parser.add_argument("--end-index", type=int, help="1부터 시작하는 종료 인덱스")
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="기존 원본 파일도 다시 다운로드",
    )
    parser.add_argument("--replace-slug", action="store_true", help="적재 전 해당 slug 데이터 삭제")
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="실패해도 다음 slug 계속 처리",
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="원본 파일만 저장하고 DB 적재 생략",
    )
    parser.add_argument(
        "--skip-spatialite",
        action="store_true",
        help="SpatiaLite 확장 로드를 건너뛰고 일반 SQLite 컬럼만 사용",
    )
    parser.add_argument(
        "--skip-refresh-geometry",
        action="store_true",
        help="전체 적재 후 SpatiaLite geometry 갱신을 생략",
    )
    args = parser.parse_args()

    downloads = _select_downloads(
        list_file_downloads(),
        slugs=args.slug,
        start_index=args.start_index,
        end_index=args.end_index,
    )
    output_dir = Path(args.output_dir)
    progress_path = Path(args.progress_path)
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    engine = None
    if not args.download_only:
        engine = create_engine(
            sqlite_url(args.database_path),
            pool_pre_ping=True,
            json_serializer=compact_json_dumps,
        )
        spatialite_enabled = create_sqlite_schema(
            engine,
            load_spatialite=not args.skip_spatialite,
        )
    else:
        spatialite_enabled = False
    client = LocalDataFileClient(timeout=args.timeout)

    failures: list[dict[str, str]] = []
    total_loaded = 0
    _write_progress(
        progress_path,
        "run_start",
        total=len(downloads),
        output_dir=str(output_dir),
        database_path=str(args.database_path),
        spatialite_enabled=spatialite_enabled,
    )
    for index, download in enumerate(downloads, start=1):
        try:
            if args.download_only:
                _download_one(
                    client=client,
                    download=download,
                    output_dir=output_dir,
                    progress_path=progress_path,
                    index=index,
                    total=len(downloads),
                    force_download=args.force_download,
                )
                continue
            if engine is None:
                raise RuntimeError("database engine is not initialized")
            loaded = _download_and_load_one(
                client=client,
                engine=engine,
                download=download,
                output_dir=output_dir,
                progress_path=progress_path,
                index=index,
                total=len(downloads),
                batch_size=args.batch_size,
                progress_every=args.progress_every,
                force_download=args.force_download,
                replace_slug=args.replace_slug,
            )
            total_loaded += loaded
        except Exception as exc:  # noqa: BLE001
            failure = {"slug": download.slug, "error": repr(exc)}
            failures.append(failure)
            _write_progress(progress_path, "failed", **failure)
            if not args.continue_on_error:
                raise

    if engine is not None and not args.skip_refresh_geometry:
        _write_progress(progress_path, "refresh_geometry_start")
        refresh_spatial_geometries(engine)
        _write_progress(progress_path, "refresh_geometry_complete")

    _write_progress(
        progress_path,
        "run_complete",
        total=len(downloads),
        total_loaded=total_loaded,
        failures=failures,
    )
    print(
        json.dumps(
            {
                "total": len(downloads),
                "total_loaded": total_loaded,
                "failures": failures,
                "database_path": str(args.database_path),
                "spatialite_enabled": spatialite_enabled,
            },
            ensure_ascii=False,
        )
    )


def _download_one(
    *,
    client: LocalDataFileClient,
    download: FileDownload,
    output_dir: Path,
    progress_path: Path,
    index: int,
    total: int,
    force_download: bool,
) -> Path:
    _write_progress(progress_path, "start", index=index, total=total, slug=download.slug)
    path = _ensure_download_file(
        client=client,
        download=download,
        output_dir=output_dir,
        progress_path=progress_path,
        index=index,
        total=total,
        force_download=force_download,
    )
    _write_progress(
        progress_path,
        "download_only_complete",
        index=index,
        total=total,
        slug=download.slug,
        file=str(path),
    )
    return path


def _download_and_load_one(
    *,
    client: LocalDataFileClient,
    engine: Engine,
    download: FileDownload,
    output_dir: Path,
    progress_path: Path,
    index: int,
    total: int,
    batch_size: int,
    progress_every: int,
    force_download: bool,
    replace_slug: bool,
) -> int:
    _write_progress(progress_path, "start", index=index, total=total, slug=download.slug)
    path = _ensure_download_file(
        client=client,
        download=download,
        output_dir=output_dir,
        progress_path=progress_path,
        index=index,
        total=total,
        force_download=force_download,
    )

    if replace_slug:
        delete_slug(engine, download.slug)
        _write_progress(progress_path, "deleted_existing", slug=download.slug)

    counter = {"count": 0}
    with path.open("rb") as source, Session(engine) as session:
        records = iter_records_from_binary(source, slug=download.slug)
        loaded = load_records_to_sqlite(
            session,
            _with_progress(records, progress_path, download.slug, progress_every, counter),
            batch_size=batch_size,
        )

    _write_progress(
        progress_path,
        "loaded",
        index=index,
        total=total,
        slug=download.slug,
        records=loaded,
    )
    return loaded


def _ensure_download_file(
    *,
    client: LocalDataFileClient,
    download: FileDownload,
    output_dir: Path,
    progress_path: Path,
    index: int,
    total: int,
    force_download: bool,
) -> Path:
    path = output_dir / f"{download.slug}_info.bin"
    if force_download or not path.exists() or path.stat().st_size == 0:
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        if tmp_path.exists():
            tmp_path.unlink()
        client.download(download.slug, tmp_path)
        tmp_path.replace(path)
        _write_progress(
            progress_path,
            "downloaded",
            index=index,
            total=total,
            slug=download.slug,
            bytes=path.stat().st_size,
            file=str(path),
        )
    else:
        _write_progress(
            progress_path,
            "download_reused",
            index=index,
            total=total,
            slug=download.slug,
            bytes=path.stat().st_size,
            file=str(path),
        )
    return path


def _with_progress(
    records: Iterable[LocalDataRecord],
    progress_path: Path,
    slug: str,
    progress_every: int,
    counter: dict[str, int],
) -> Iterator[LocalDataRecord]:
    for record in records:
        counter["count"] += 1
        if progress_every > 0 and counter["count"] % progress_every == 0:
            _write_progress(progress_path, "load_progress", slug=slug, records=counter["count"])
        yield record


def _select_downloads(
    downloads: list[FileDownload],
    *,
    slugs: list[str] | None,
    start_index: int,
    end_index: int | None,
) -> list[FileDownload]:
    if start_index < 1:
        raise ValueError("start_index must be greater than 0")
    selected = downloads[start_index - 1 : end_index]
    if not slugs:
        return selected
    wanted = set(slugs)
    return [download for download in selected if download.slug in wanted]


def _write_progress(progress_path: Path, event: str, **payload: Any) -> None:
    row = {
        "time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "event": event,
        **payload,
    }
    with progress_path.open("a", encoding="utf-8") as progress:
        progress.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


if __name__ == "__main__":
    main()
