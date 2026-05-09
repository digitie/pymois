# DB 브라우저 웹앱

`apps/db_browser`는 `pymois`로 PostGIS에 적재한 인허가 DB를 간단히 조회하는 웹앱입니다. 백엔드는 FastAPI, 프론트엔드는 React와 Tailwind CSS 기반입니다.

## 구성

| 경로 | 설명 |
|---|---|
| `apps/db_browser/backend` | FastAPI API 서버 |
| `apps/db_browser/frontend` | Vite + React + Tailwind CSS 프론트엔드 |

백엔드는 기존 `mois_place_master`, `mois_place_detail` 테이블을 읽습니다. DB URL은 `MOIS_DATABASE_URL` 환경변수로 전달합니다.

## WSL에서 PostgreSQL/PostGIS 준비

WSL Ubuntu에서 PostgreSQL 16과 PostGIS를 설치한 뒤 `pymois` 전용 DB와 계정을 만듭니다.

```powershell
wsl -d Ubuntu -u root -- bash -lc "apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y postgresql postgresql-contrib postgis postgresql-16-postgis-3 postgresql-16-postgis-3-scripts && pg_ctlcluster 16 main start"

wsl -d Ubuntu -u root -- bash -lc "runuser -u postgres -- psql -p 5433 -c \"CREATE ROLE pymois LOGIN PASSWORD 'pymois';\" || true"
wsl -d Ubuntu -u root -- bash -lc "runuser -u postgres -- createdb -p 5433 -O pymois pymois || true"
wsl -d Ubuntu -u root -- bash -lc "runuser -u postgres -- psql -p 5433 -d pymois -c 'CREATE EXTENSION IF NOT EXISTS postgis;'"
```

설치 환경에 따라 PostgreSQL 포트가 `5432` 또는 `5433`일 수 있습니다. 실제 포트는 다음 명령으로 확인합니다.

```powershell
wsl -d Ubuntu -u root -- bash -lc "pg_lsclusters"
```

## 원본 다운로드 파일 보관

내려받은 원본 localdata 파일은 `artifacts/localdata/` 아래에 저장합니다. `artifacts/`는 `.gitignore`에 포함되어 있으므로 원본 데이터가 git에 노출되지 않습니다.

현재 병원 인허가 원본 파일은 다음 경로에 보관합니다.

```text
artifacts/localdata/hospitals_info.bin
```

## 다운로드 파일 적재

이미 내려받은 localdata CSV/ZIP 파일은 `apps.db_browser.backend.load_postgis` CLI로 적재합니다. 파일은 CP949 CSV 또는 ZIP을 모두 처리하며, 좌표는 기존 `pymois` 로더를 거쳐 WGS84 `(lon, lat)`와 PostGIS `geometry(Point, 4326)`로 저장합니다.

```powershell
wsl -d Ubuntu -- bash -lc "cd /mnt/f/dev/pykrmois && python3 -m venv .venv-wsl && . .venv-wsl/bin/activate && python -m pip install -U pip && python -m pip install -e '.[web]'"

wsl -d Ubuntu -- bash -lc "cd /mnt/f/dev/pykrmois && . .venv-wsl/bin/activate && export MOIS_DATABASE_URL='postgresql+psycopg://pymois:pymois@127.0.0.1:5433/pymois' && python -m apps.db_browser.backend.load_postgis --file artifacts/localdata/hospitals_info.bin --slug hospitals --replace-slug"
```

다른 업종 파일도 같은 방식으로 `--file`과 `--slug`를 바꿔 적재합니다. 같은 업종을 다시 넣을 때는 `--replace-slug`를 붙여 기존 해당 업종 데이터를 먼저 삭제합니다.

## 백엔드 실행

```powershell
pip install -e ".[web,dev]"

$env:MOIS_DATABASE_URL = "postgresql+psycopg://user:password@localhost:5432/mois"
python -m apps.db_browser.backend
```

기본 주소는 `http://127.0.0.1:8000`입니다. 포트와 호스트는 `MOIS_WEB_PORT`, `MOIS_WEB_HOST`로 바꿀 수 있습니다.

WSL에서 빌드된 프론트엔드를 FastAPI가 함께 서빙하게 하려면 다음처럼 실행합니다.

```powershell
wsl -d Ubuntu -- bash -lc "cd /mnt/f/dev/pykrmois && . .venv-wsl/bin/activate && export MOIS_DATABASE_URL='postgresql+psycopg://pymois:pymois@127.0.0.1:5433/pymois' MOIS_WEB_HOST=0.0.0.0 MOIS_WEB_PORT=5173 && python -m apps.db_browser.backend"
```

이 경우 Windows 브라우저에서는 `http://127.0.0.1:5173/`로 접속합니다.

주요 API:

| API | 설명 |
|---|---|
| `GET /api/health` | 서버와 DB 설정 상태 |
| `GET /api/stats` | 전체 건수, 영업 건수, 좌표 보유 건수, 업종 요약 |
| `GET /api/services` | DB에 적재된 업종 목록과 건수 |
| `GET /api/places` | 인허가 레코드 검색/필터/페이지 조회 |
| `GET /api/places/{place_id}` | 마스터와 상세 JSON 데이터 조회 |

`/api/places` 쿼리 파라미터:

| 파라미터 | 설명 |
|---|---|
| `q` | 사업장명, 주소, 관리번호 검색어 |
| `service_slug` | 업종 slug |
| `category` | 인허가 분류 |
| `is_open` | `true` 또는 `false` |
| `limit` | 1~200 |
| `offset` | 페이지 시작 위치 |

## 프론트엔드 실행

```powershell
cd apps\db_browser\frontend
npm install
npm run dev
```

개발 서버는 기본적으로 `http://127.0.0.1:5173`에서 뜨고, Vite proxy가 `/api` 요청을 `http://127.0.0.1:8000`으로 보냅니다.

백엔드 주소가 다르면 `.env.local` 또는 실행 환경에 다음 값을 둡니다.

```powershell
$env:VITE_API_BASE_URL = "http://127.0.0.1:8000"
```

## 빌드 후 백엔드에서 함께 서빙

```powershell
cd apps\db_browser\frontend
npm run build

cd ..\..\..
$env:MOIS_DATABASE_URL = "postgresql+psycopg://user:password@localhost:5432/mois"
python -m apps.db_browser.backend
```

`apps/db_browser/frontend/dist`가 있으면 FastAPI가 빌드된 프론트엔드를 함께 서빙합니다.

## 화면에서 확인할 수 있는 것

- 전체 적재 건수, 영업 중 건수, 좌표 보유 건수, 업종 수
- 분류/업종/영업 상태/검색어 필터
- 사업장명, 관리번호, 주소, WGS84 좌표 `(lon, lat)`, 수정일
- 레코드별 `specific_data`, `record_data`, `raw_data` 상세 JSON

## 주의

- `MOIS_DATABASE_URL`이 없으면 API는 503을 반환합니다.
- 이 앱은 조회용입니다. DB 수정이나 재적재 기능은 제공하지 않습니다.
- 대량 테이블에서는 검색어 없는 전체 조회보다 업종/분류 필터를 함께 쓰는 것이 좋습니다.
