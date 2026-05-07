"""file.localdata.go.kr 파일 다운로드와 CSV 로더."""

from __future__ import annotations

import codecs
import csv
import io
import os
import tempfile
import zipfile
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import IO, Any, cast
from urllib.parse import urlencode

from requests import RequestException

from ._http import build_session, raise_for_http_error
from .catalogs import get_file_download
from .convert import convert_value, field_for_header
from .exceptions import MoisParseError, MoisRequestError
from .models import Coordinate, LocalDataRecord

DEFAULT_FILE_BASE_URL = "https://file.localdata.go.kr"


class LocalDataFileClient:
    """localdata 인허가정보 CSV 파일 다운로드/로드 클라이언트."""

    def __init__(
        self,
        *,
        timeout: float = 30.0,
        retries: int = 2,
        session: Any | None = None,
        base_url: str = DEFAULT_FILE_BASE_URL,
        validate_download_count: bool = True,
    ) -> None:
        self.timeout = timeout
        self.session = session or build_session(retries)
        self.base_url = base_url.rstrip("/")
        self.validate_download_count = validate_download_count

    def download_bytes(self, slug: str, *, org_code: str | None = None) -> bytes:
        """업종 slug의 전국 또는 지역 CSV 파일을 bytes로 다운로드합니다."""

        with tempfile.TemporaryFile() as output:
            binary_output = cast(IO[bytes], output)
            self._download_to_file(slug, binary_output, org_code=org_code)
            binary_output.seek(0)
            return binary_output.read()

    def download(
        self,
        slug: str,
        output_path: str | os.PathLike[str],
        *,
        org_code: str | None = None,
    ) -> Path:
        """파일을 다운로드해서 `output_path`에 저장하고 경로를 반환합니다."""

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as output:
            self._download_to_file(slug, output, org_code=org_code)
        return path

    def load(
        self,
        slug: str,
        *,
        org_code: str | None = None,
        encoding: str | None = None,
    ) -> list[LocalDataRecord]:
        """업종 파일을 다운로드하고 `LocalDataRecord` 목록으로 로드합니다."""

        return load_records_from_bytes(
            self.download_bytes(slug, org_code=org_code),
            slug=slug,
            encoding=encoding,
        )

    def iter(
        self,
        slug: str,
        *,
        org_code: str | None = None,
        encoding: str | None = None,
    ) -> Iterator[LocalDataRecord]:
        """업종 파일을 다운로드하고 `LocalDataRecord`를 한 행씩 순회합니다.

        대용량 업종은 `load()`처럼 전체 목록을 만들지 말고 이 메서드를 사용합니다.
        """

        with tempfile.TemporaryFile() as output:
            binary_output = cast(IO[bytes], output)
            self._download_to_file(slug, binary_output, org_code=org_code)
            binary_output.seek(0)
            yield from iter_records_from_binary(binary_output, slug=slug, encoding=encoding)

    def load_file(
        self,
        path: str | os.PathLike[str],
        *,
        slug: str | None = None,
        encoding: str | None = None,
    ) -> list[LocalDataRecord]:
        """이미 받은 CSV 파일을 `LocalDataRecord` 목록으로 로드합니다."""

        return list(self.iter_file(path, slug=slug, encoding=encoding))

    def iter_file(
        self,
        path: str | os.PathLike[str],
        *,
        slug: str | None = None,
        encoding: str | None = None,
    ) -> Iterator[LocalDataRecord]:
        """이미 받은 CSV 파일을 `LocalDataRecord`로 한 행씩 순회합니다."""

        with Path(path).open("rb") as source:
            yield from iter_records_from_binary(source, slug=slug, encoding=encoding)

    def __getattr__(self, name: str) -> Any:
        """`load_hospitals()`, `iter_hospitals()` 편의 메서드를 동적으로 제공합니다."""

        if name.startswith("iter_"):
            slug = name[len("iter_") :]

            def iterator(**kwargs: Any) -> Iterator[LocalDataRecord]:
                return self.iter(slug, **kwargs)

            return iterator
        if name.startswith("load_"):
            slug = name[5:]

            def loader(**kwargs: Any) -> list[LocalDataRecord]:
                return self.load(slug, **kwargs)

            return loader
        if name.startswith("download_"):
            slug = name[len("download_") :]

            def downloader(output_path: str | os.PathLike[str], **kwargs: Any) -> Path:
                return self.download(slug, output_path, **kwargs)

            return downloader
        raise AttributeError(name)

    def _absolute(self, path_or_url: str) -> str:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            return path_or_url
        return f"{self.base_url}{path_or_url}"

    def _download_to_file(
        self,
        slug: str,
        output: IO[bytes],
        *,
        org_code: str | None = None,
    ) -> None:
        spec = get_file_download(slug)
        info_url = self._absolute(spec.info_path)
        download_url = self._absolute(spec.download_path)
        if org_code:
            download_url = f"{download_url}?{urlencode({'orgCode': org_code})}"

        response: Any | None = None
        try:
            self.session.get(
                info_url,
                headers={"Referer": self.base_url, "Accept": "text/html,application/xhtml+xml"},
                timeout=self.timeout,
            )
            if self.validate_download_count:
                validation = self.session.get(
                    self._absolute("/file/validate/download-count"),
                    headers={"Referer": info_url, "Accept": "*/*"},
                    timeout=self.timeout,
                )
                raise_for_http_error(validation, "localdata download validation")
            response = self.session.get(
                download_url,
                headers={"Referer": info_url, "Accept": "*/*"},
                timeout=self.timeout,
                stream=True,
            )
            raise_for_http_error(response, f"localdata download {slug}")
            _write_response_to_file(response, output)
        except RequestException as exc:
            raise MoisRequestError(f"localdata download failed: {slug}") from exc
        finally:
            close = getattr(response, "close", None)
            if callable(close):
                close()


def load_records_from_bytes(
    content: bytes,
    *,
    slug: str | None = None,
    encoding: str | None = None,
) -> list[LocalDataRecord]:
    """CSV bytes를 정규화된 객체 목록으로 변환합니다."""

    return list(iter_records_from_bytes(content, slug=slug, encoding=encoding))


def iter_records_from_bytes(
    content: bytes,
    *,
    slug: str | None = None,
    encoding: str | None = None,
) -> Iterator[LocalDataRecord]:
    """CSV bytes를 정규화된 객체로 한 행씩 변환합니다."""

    csv_bytes = _first_csv_bytes(content)
    selected_encoding = _choose_csv_encoding(csv_bytes, encoding)
    stream = io.TextIOWrapper(io.BytesIO(csv_bytes), encoding=selected_encoding)
    try:
        yield from _iter_records_from_reader(csv.DictReader(stream), slug=slug)
    except UnicodeDecodeError as exc:
        raise MoisParseError("CSV 인코딩을 해석할 수 없습니다") from exc


def iter_records_from_binary(
    source: IO[bytes],
    *,
    slug: str | None = None,
    encoding: str | None = None,
) -> Iterator[LocalDataRecord]:
    """seek 가능한 binary CSV/ZIP 스트림을 정규화된 객체로 순회합니다."""

    selected_encoding = encoding or "cp949"
    if _is_zip_binary(source):
        with zipfile.ZipFile(source) as archive:
            candidates = [
                name
                for name in archive.namelist()
                if not name.endswith("/") and name.lower().endswith((".csv", ".txt"))
            ]
            if not candidates:
                raise MoisParseError("ZIP 파일 안에서 CSV를 찾을 수 없습니다")
            with archive.open(candidates[0]) as csv_file:
                yield from _iter_records_from_binary_reader(
                    csv_file,
                    slug=slug,
                    encoding=selected_encoding,
                )
        return

    source.seek(0)
    yield from _iter_records_from_binary_reader(source, slug=slug, encoding=selected_encoding)


def load_records_from_text(text: str, *, slug: str | None = None) -> list[LocalDataRecord]:
    """CSV 문자열을 정규화된 객체 목록으로 변환합니다."""

    return list(iter_records_from_text(text, slug=slug))


def iter_records_from_text(text: str, *, slug: str | None = None) -> Iterator[LocalDataRecord]:
    """CSV 문자열을 정규화된 객체로 한 행씩 변환합니다."""

    yield from _iter_records_from_reader(csv.DictReader(io.StringIO(text)), slug=slug)


def _iter_records_from_reader(
    reader: csv.DictReader[str],
    *,
    slug: str | None = None,
) -> Iterator[LocalDataRecord]:
    if not reader.fieldnames:
        raise MoisParseError("CSV 헤더가 없습니다")
    spec = get_file_download(slug) if slug else None
    for row in reader:
        raw = {str(key): value or "" for key, value in row.items() if key is not None}
        data: dict[str, Any] = {}
        for header, raw_value in raw.items():
            field = field_for_header(header)
            data[field] = convert_value(field, header, raw_value)
        coordinates = _coordinates_from_data(data)
        if coordinates is not None:
            data["WGS84_LON"] = coordinates.lon
            data["WGS84_LAT"] = coordinates.lat
        yield LocalDataRecord.build(
            service_slug=slug,
            category=spec.category if spec else None,
            title=spec.title if spec else None,
            data=data,
            raw=raw,
            coordinates=coordinates,
        )


def _iter_records_from_binary_reader(
    source: IO[bytes],
    *,
    slug: str | None = None,
    encoding: str,
) -> Iterator[LocalDataRecord]:
    stream = io.TextIOWrapper(source, encoding=encoding, newline="")
    try:
        yield from _iter_records_from_reader(csv.DictReader(stream), slug=slug)
    except UnicodeDecodeError as exc:
        raise MoisParseError("CSV 인코딩을 해석할 수 없습니다") from exc


def _coordinates_from_data(data: dict[str, Any]) -> Coordinate | None:
    x = data.get("CRD_INFO_X")
    y = data.get("CRD_INFO_Y")
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        return None
    return Coordinate.from_katec(float(x), float(y))


def _first_csv_bytes(content: bytes) -> bytes:
    if not zipfile.is_zipfile(io.BytesIO(content)):
        return content
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        candidates = [
            name
            for name in archive.namelist()
            if not name.endswith("/") and name.lower().endswith((".csv", ".txt"))
        ]
        if not candidates:
            raise MoisParseError("ZIP 파일 안에서 CSV를 찾을 수 없습니다")
        return archive.read(candidates[0])


def _is_zip_binary(source: IO[bytes]) -> bool:
    position = source.tell()
    try:
        return zipfile.is_zipfile(source)
    finally:
        source.seek(position)


def _write_response_to_file(response: Any, output: IO[bytes]) -> None:
    iter_content = getattr(response, "iter_content", None)
    if callable(iter_content):
        for chunk in iter_content(chunk_size=1024 * 1024):
            if chunk:
                output.write(chunk)
        return
    output.write(bytes(getattr(response, "content", b"")))


def _decode_csv(content: bytes, encoding: str | None) -> str:
    return content.decode(_choose_csv_encoding(content, encoding))


def _choose_csv_encoding(content: bytes, encoding: str | None) -> str:
    encodings: Iterable[str] = (encoding,) if encoding else ("utf-8-sig", "cp949", "euc-kr")
    last_error: UnicodeDecodeError | None = None
    for candidate in encodings:
        if candidate is None:
            continue
        try:
            _validate_decoding(content, candidate)
            return candidate
        except UnicodeDecodeError as exc:
            last_error = exc
    raise MoisParseError("CSV 인코딩을 해석할 수 없습니다") from last_error


def _validate_decoding(content: bytes, encoding: str) -> None:
    decoder = codecs.getincrementaldecoder(encoding)()
    for offset in range(0, len(content), 65536):
        decoder.decode(content[offset : offset + 65536], final=False)
    decoder.decode(b"", final=True)
